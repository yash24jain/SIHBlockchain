import json
import os
from datetime import datetime, timezone


# ============================================================
# EXPORT CLEAN BLOCKCHAIN DATA
# ============================================================

def export_blockchain_data(
    blockchain_data,
    filename="data/blockchain_data.json"
):
    """
    Export standardized blockchain data to JSON.

    Expected structure:
    {
        "wallet": "...",
        "chain": "ethereum",
        "generated_at": "...",
        "wallets_metadata": {...},
        "transactions": [...]
    }
    """

    # --------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # --------------------------------------------

    directory = os.path.dirname(filename)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

    # --------------------------------------------
    # COPY DATA & PRESERVE METADATA
    # --------------------------------------------

    export_data = {
        "wallet": blockchain_data.get(
            "wallet",
            ""
        ),
        "chain": blockchain_data.get(
            "chain",
            "ethereum"
        ),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "wallets_metadata": blockchain_data.get(
            "wallets_metadata",
            {}
        ),
        "transactions": blockchain_data.get(
            "transactions",
            []
        )
    }

    # --------------------------------------------
    # WRITE JSON
    # --------------------------------------------

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            export_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------
    # SUMMARY
    # --------------------------------------------

    transactions = export_data["transactions"]

    eth_count = sum(
        1
        for tx in transactions
        if tx.get("token") == "ETH"
    )

    token_count = sum(
        1
        for tx in transactions
        if tx.get("transaction_type") == "ERC20_TRANSFER"
    )

    incoming_count = sum(
        1
        for tx in transactions
        if tx.get("direction") == "IN"
    )

    outgoing_count = sum(
        1
        for tx in transactions
        if tx.get("direction") == "OUT"
    )

    metadata_count = len(export_data["wallets_metadata"])

    print("\n========================================")
    print("DATA EXPORT COMPLETE")
    print("========================================")
    print(f"Output file        : {filename}")
    print(f"Total transactions : {len(transactions)}")
    print(f"ETH transactions   : {eth_count}")
    print(f"ERC-20 transfers   : {token_count}")
    print(f"Incoming           : {incoming_count}")
    print(f"Outgoing           : {outgoing_count}")
    print(f"Tagged entities    : {metadata_count}")
    print("========================================")

    return filename