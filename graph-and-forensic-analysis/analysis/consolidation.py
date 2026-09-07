def detect_fund_consolidation(graph, wallet):

    incoming = list(
        graph.in_edges(
            wallet,
            data=True
        )
    )

    if not incoming:
        return {
            "is_consolidation": False
        }

    sources = []
    unique_sources = set()
    total_incoming = 0.0

    for sender, receiver, data in incoming:

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

        sender = sender.lower()

        unique_sources.add(sender)

        sources.append({
            "wallet": sender,
            "amount": amount
        })

        total_incoming += amount

    # Consolidation requires funds coming from
    # at least two different wallets.
    if len(unique_sources) < 2:

        return {
            "is_consolidation": False
        }

    return {
        "is_consolidation": True,
        "wallet": wallet.lower(),
        "sources": sources,
        "total_incoming": total_incoming,
        "source_count": len(unique_sources)
    }