from datetime import datetime


def _parse_timestamp(timestamp):
    """
    Convert an ISO timestamp into a datetime object.
    """
    if timestamp is None:
        return None

    try:
        return datetime.fromisoformat(str(timestamp))
    except (ValueError, TypeError):
        return None


def calculate_path_velocity(graph, path):
    """
    Calculate how quickly money moves through a path.

    For a MultiDiGraph, multiple transactions may exist between
    the same pair of wallets. We therefore inspect all valid
    transactions and use the chronological transactions belonging
    to the path.

    Returns:
        duration_seconds
        hops_per_minute
        rapid_movement
    """

    timestamps = []

    for i in range(len(path) - 1):

        sender = path[i]
        receiver = path[i + 1]

        edge_data = graph.get_edge_data(
            sender,
            receiver
        )

        if not edge_data:
            continue

        # -------------------------------------------------
        # Normal DiGraph
        # -------------------------------------------------

        if "timestamp" in edge_data:

            candidates = [edge_data]

        # -------------------------------------------------
        # MultiDiGraph
        # -------------------------------------------------

        else:

            candidates = [
                data
                for data in edge_data.values()
                if isinstance(data, dict)
            ]

        # -------------------------------------------------
        # Collect valid timestamps
        # -------------------------------------------------

        for data in candidates:

            timestamp = data.get("timestamp")

            parsed_timestamp = _parse_timestamp(
                timestamp
            )

            if parsed_timestamp is not None:
                timestamps.append(
                    parsed_timestamp
                )

    # -----------------------------------------------------
    # Need at least two transactions
    # -----------------------------------------------------

    if len(timestamps) < 2:

        return {
            "duration_seconds": 0,
            "hops_per_minute": None,
            "rapid_movement": False
        }

    # Sort chronologically

    timestamps.sort()

    first_timestamp = timestamps[0]
    last_timestamp = timestamps[-1]

    duration = (
        last_timestamp - first_timestamp
    ).total_seconds()

    hops = len(path) - 1

    # -----------------------------------------------------
    # Same timestamp / zero duration
    # -----------------------------------------------------

    if duration <= 0:

        return {
            "duration_seconds": 0,
            "hops_per_minute": None,
            "rapid_movement": False
        }

    # -----------------------------------------------------
    # Calculate velocity
    # -----------------------------------------------------

    hops_per_minute = (
        hops / duration
    ) * 60

    # -----------------------------------------------------
    # Rapid movement threshold
    #
    # 2 or more hops per minute = rapid
    # -----------------------------------------------------

    rapid_movement = (
        hops_per_minute >= 2
    )

    return {
        "duration_seconds": duration,
        "hops_per_minute": hops_per_minute,
        "rapid_movement": rapid_movement
    }