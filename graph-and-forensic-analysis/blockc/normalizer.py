from datetime import datetime


def normalize_transactions(api_response):

    transactions = []

    raw_transactions = api_response.get("result", [])

    for tx in raw_transactions:

        # Ignore transactions without a receiver
        if not tx.get("to"):
            continue

        transaction = {
            "from": tx["from"].lower(),
            "to": tx["to"].lower(),
            "amount": int(tx["value"]) / 10**18,
            "timestamp": datetime.fromtimestamp(
                int(tx["timeStamp"])
            ).isoformat(),
            "tx_hash": tx["hash"]
        }

        transactions.append(transaction)

    return transactions