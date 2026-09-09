import networkx as nx


def build_transaction_graph(transactions):

    graph = nx.MultiDiGraph()

    for tx in transactions:

        sender = tx.get("from") or tx.get("from_address")
        receiver = tx.get("to") or tx.get("to_address")

        if not sender or not receiver:
            continue

        graph.add_node(sender)
        graph.add_node(receiver)

        graph.add_edge(
            sender,
            receiver,
            amount=tx.get("amount", 0.0),
            amount_unit=tx.get("amount_unit"),
            token=tx.get("token") or tx.get("token_symbol"),
            token_contract=tx.get("token_contract"),
            timestamp=tx.get("timestamp"),
            tx_hash=tx.get("tx_hash"),
            transaction_type=tx.get("transaction_type"),
            transaction_status=tx.get("transaction_status")
        )

    return graph