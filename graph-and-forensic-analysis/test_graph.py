import json

from graph.builder import build_transaction_graph


def load_blockchain_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_graph_transactions(data):

    graph_transactions = []

    for tx in data.get("transactions", []):

        sender = str(tx.get("from", "")).lower()
        receiver = str(tx.get("to", "")).lower()

        if not sender or not receiver:
            continue

        try:
            amount = float(tx.get("amount", 0))
        except (TypeError, ValueError):
            amount = 0.0

        graph_transactions.append({
            "from": sender,
            "to": receiver,
            "amount": amount,
            "amount_unit": tx.get("amount_unit"),
            "token": tx.get("token_symbol"),
            "token_contract": tx.get("token_contract"),
            "timestamp": tx.get("timestamp"),
            "tx_hash": tx.get("tx_hash"),
            "transaction_type": tx.get("transaction_type"),
            "transaction_status": tx.get("transaction_status")
        })

    return graph_transactions


# 1. Load JSON
data = load_blockchain_data("blockchain_data.json")

# 2. Prepare transactions
transactions = prepare_graph_transactions(data)

# 3. Build graph
graph = build_transaction_graph(transactions)

# 4. Check result
print("Transactions:", len(transactions))
print("Nodes:", graph.number_of_nodes())
print("Edges:", graph.number_of_edges())