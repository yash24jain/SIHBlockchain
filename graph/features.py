def analyze_path(graph, path):

    transactions = []
    total_amount = 0.0

    for i in range(len(path) - 1):

        sender = path[i]
        receiver = path[i + 1]

        edge_data = graph.get_edge_data(
            sender,
            receiver
        )

        if not edge_data:
            continue

        # --------------------------------------------------
        # MultiDiGraph
        # --------------------------------------------------

        if graph.is_multigraph():

            for _, data in edge_data.items():

                if not isinstance(data, dict):
                    continue

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

                transactions.append({
                    "from": sender,
                    "to": receiver,
                    "amount": amount,
                    "timestamp": data.get("timestamp"),
                    "tx_hash": data.get("tx_hash")
                })

                total_amount += amount

        # --------------------------------------------------
        # Normal DiGraph
        # --------------------------------------------------

        else:

            data = edge_data

            amount = data.get("amount", 0)

            if amount is None:
                amount = 0

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = 0.0

            if amount <= 0:
                continue

            transactions.append({
                "from": sender,
                "to": receiver,
                "amount": amount,
                "timestamp": data.get("timestamp"),
                "tx_hash": data.get("tx_hash")
            })

            total_amount += amount

    return {
        "path": path,
        "hops": len(path) - 1,
        "transactions": transactions,
        "total_amount": total_amount
    }