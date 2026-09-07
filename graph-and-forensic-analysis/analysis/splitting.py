def detect_fund_splitting(graph, wallet):

    outgoing = list(
        graph.out_edges(
            wallet,
            data=True
        )
    )

    # No outgoing transactions
    if not outgoing:
        return {
            "is_split": False
        }

    destinations = []
    unique_destinations = set()
    total_outgoing = 0.0

    for sender, receiver, data in outgoing:

        amount = data.get("amount", 0)

        if amount is None:
            amount = 0

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0.0

        # Ignore zero-value transactions
        if amount <= 0:
            continue

        receiver = receiver.lower()

        unique_destinations.add(receiver)

        destinations.append({
            "wallet": receiver,
            "amount": amount
        })

        total_outgoing += amount

    # Splitting requires funds going to at least
    # two different destinations.
    if len(unique_destinations) < 2:

        return {
            "is_split": False
        }

    return {
        "is_split": True,
        "wallet": wallet.lower(),
        "destinations": destinations,
        "total_outgoing": total_outgoing,
        "destination_count": len(unique_destinations)
    }