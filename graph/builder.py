import networkx as nx


def build_transaction_graph(transactions):

    graph = nx.MultiDiGraph()

    for tx in transactions:

        sender = tx["from"]
        receiver = tx["to"]

        graph.add_node(sender)
        graph.add_node(receiver)

        graph.add_edge(
            sender,
            receiver,
            amount=tx["amount"],
            amount_unit=tx.get("amount_unit"),
            token=tx.get("token"),
            token_contract=tx.get("token_contract"),
            timestamp=tx["timestamp"],
            tx_hash=tx["tx_hash"],
            transaction_type=tx.get("transaction_type"),
            transaction_status=tx.get("transaction_status")
        )

    return graph