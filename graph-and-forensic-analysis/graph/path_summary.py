def build_path_summary(path_data):
    """
    Build a compact investigator-friendly summary
    for a ranked money-flow path.
    """

    path = path_data.get("path", [])
    transactions = path_data.get("transactions", [])

    if not path:
        return {}

    # -------------------------
    # BASIC PATH INFORMATION
    # -------------------------

    start_wallet = path[0]
    end_wallet = path[-1]
    hops = len(path) - 1

    # -------------------------
    # TRANSACTION VALUES
    # -------------------------

    amounts = []

    for tx in transactions:
        try:
            amount = float(tx.get("amount", 0))
        except (TypeError, ValueError):
            amount = 0.0

        if amount > 0:
            amounts.append(amount)

    total_value = amounts[0] if amounts else 0.0
    final_value = amounts[-1] if amounts else 0.0

    # -------------------------
    # VALUE RETENTION
    # -------------------------

    if total_value > 0:
        value_retention = final_value / total_value
    else:
        value_retention = 0.0

    value_retention = max(
        0.0,
        min(value_retention, 1.0)
    )

    # -------------------------
    # VELOCITY
    # -------------------------

    velocity = path_data.get("velocity", {})

    # -------------------------
    # SUMMARY
    # -------------------------

    summary = {
        "start_wallet": start_wallet,
        "end_wallet": end_wallet,
        "hops": hops,
        "transaction_count": len(transactions),
        "total_value": round(total_value, 6),
        "final_value": round(final_value, 6),
        "value_retention": round(
            value_retention,
            4
        ),
        "rapid_movement": velocity.get(
            "rapid_movement",
            False
        )
    }

    # -------------------------
    # INVESTIGATIVE INDICATORS
    # -------------------------

    indicators = []

    if hops >= 2:
        indicators.append(
            "multi-hop movement"
        )

    if value_retention >= 0.8 and hops >= 2:
        indicators.append(
            "high value retention"
        )

    if velocity.get("rapid_movement"):
        indicators.append(
            "rapid movement"
        )

    # Preserve ranking reasons
    for reason in path_data.get("reasons", []):

        if reason not in indicators:
            indicators.append(reason)

    return {
        "summary": summary,
        "indicators": indicators
    }