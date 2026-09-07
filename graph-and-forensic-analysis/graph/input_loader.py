import json


def load_blockchain_data(file_path):
    """
    Load standardized blockchain JSON data.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_graph_transactions(data):
    """
    Convert standardized blockchain transactions
    into the format required by the graph builder.
    """

    graph_transactions = []

    for tx in data.get("transactions", []):

        sender = str(
            tx.get("from", "")
        ).lower()

        receiver = str(
            tx.get("to", "")
        ).lower()

        # Skip invalid transactions
        if not sender or not receiver:
            continue

        try:
            amount = float(
                tx.get("amount", 0)
            )
        except (TypeError, ValueError):
            amount = 0.0

        graph_transactions.append({

            "from": sender,

            "to": receiver,

            "amount": amount,

            "amount_unit":
                tx.get("amount_unit"),

            "token":
                tx.get("token_symbol"),

            "timestamp":
                tx.get("timestamp"),

            "tx_hash":
                tx.get("tx_hash"),

            "transaction_type":
                tx.get("transaction_type"),

            "transaction_status":
                tx.get("transaction_status")
        })

    return graph_transactions