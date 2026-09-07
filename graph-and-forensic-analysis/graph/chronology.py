
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


def _get_transactions_for_edge(graph, sender, receiver):
    """
    Get all valid transactions between two wallets.
    """

    edge_data = graph.get_edge_data(
        sender,
        receiver
    )

    if not edge_data:
        return []

    # Normal DiGraph
    if "amount" in edge_data:

        candidates = [edge_data]

    # MultiDiGraph
    else:

        candidates = [
            data
            for data in edge_data.values()
            if isinstance(data, dict)
        ]

    transactions = []

    for data in candidates:

        timestamp = data.get("timestamp")

        parsed_time = _parse_timestamp(
            timestamp
        )

        if parsed_time is None:
            continue

        transactions.append({
            "from": sender,
            "to": receiver,
            "amount": data.get("amount", 0),
            "timestamp": timestamp,
            "tx_hash": data.get("tx_hash"),
            "_parsed_time": parsed_time
        })

    return transactions


def build_chronological_flow(graph, path):
    """
    Build chronological transaction information for a path.

    A path is chronological only when the transaction used
    for each hop occurs at or after the transaction used
    for the previous hop.

    Example:

        A --2020--> B --2021--> C

    is chronological.

        A --2021--> B --2020--> C

    is NOT chronological.
    """

    flow = []

    # ---------------------------------------------------------
    # COLLECT TRANSACTIONS PER HOP
    # ---------------------------------------------------------

    hop_transactions = []

    for i in range(len(path) - 1):

        sender = path[i]
        receiver = path[i + 1]

        transactions = _get_transactions_for_edge(
            graph,
            sender,
            receiver
        )

        # Sort transactions within this hop
        transactions.sort(
            key=lambda tx: tx["_parsed_time"]
        )

        hop_transactions.append(
            transactions
        )

        # Add them to output
        flow.extend(
            transactions
        )

    # ---------------------------------------------------------
    # CHECK CHRONOLOGY BETWEEN HOPS
    # ---------------------------------------------------------

    chronological = True

    previous_hop_latest = None

    for transactions in hop_transactions:

        # No usable transaction for this hop
        if not transactions:
            continue

        current_hop_earliest = min(
            tx["_parsed_time"]
            for tx in transactions
        )

        current_hop_latest = max(
            tx["_parsed_time"]
            for tx in transactions
        )

        # Current hop happened before previous hop
        if (
            previous_hop_latest is not None
            and current_hop_earliest < previous_hop_latest
        ):

            chronological = False

        previous_hop_latest = current_hop_latest

    # ---------------------------------------------------------
    # REMOVE INTERNAL FIELDS
    # ---------------------------------------------------------

    for tx in flow:

        tx.pop(
            "_parsed_time",
            None
        )

    # ---------------------------------------------------------
    # SORT OUTPUT FOR DISPLAY ONLY
    # ---------------------------------------------------------

    flow.sort(
        key=lambda tx: _parse_timestamp(
            tx["timestamp"]
        ) or datetime.max
    )

    return {
        "transactions": flow,
        "chronological": chronological
    }