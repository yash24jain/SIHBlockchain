from blockchain_api import (
    get_clean_blockchain_data,
    is_valid_wallet_address,
    normalize_address
)

from data_exporter import (
    export_blockchain_data
)


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "ETHEREUM BLOCKCHAIN DATA COLLECTOR"
    )

    print(
        "========================================"
    )

    # ----------------------------------------
    # INPUT
    # ----------------------------------------

    wallet = input(
        "\nEnter Ethereum wallet address: "
    ).strip()

    wallet = normalize_address(
        wallet
    )

    # ----------------------------------------
    # VALIDATE
    # ----------------------------------------

    if not is_valid_wallet_address(
        wallet
    ):

        print(
            "\nERROR: Invalid Ethereum wallet address."
        )

        return

    # ----------------------------------------
    # COLLECT
    # ----------------------------------------

    try:

        blockchain_data = (
            get_clean_blockchain_data(
                wallet
            )
        )

    except ValueError as error:

        print(
            f"\nERROR: {error}"
        )

        return

    # ----------------------------------------
    # SUMMARY
    # ----------------------------------------

    transactions = (
        blockchain_data["transactions"]
    )

    print(
        "\n========================================"
    )

    print(
        "BLOCKCHAIN DATA SUMMARY"
    )

    print(
        "========================================"
    )

    print(
        f"Wallet: {wallet}"
    )

    print(
        f"Chain: ethereum"
    )

    print(
        f"Total transactions: "
        f"{len(transactions)}"
    )

    # ----------------------------------------
    # DISPLAY SAMPLE
    # ----------------------------------------

    if transactions:

        print(
            "\nSample normalized transaction:"
        )

        print(
            "----------------------------------------"
        )

        sample = transactions[0]

        print(
            f"From       : {sample.get('from')}"
        )

        print(
            f"To         : {sample.get('to')}"
        )

        print(
            f"Amount     : {sample.get('amount')}"
        )

        print(
            f"Unit       : {sample.get('amount_unit')}"
        )

        print(
            f"Token      : {sample.get('token')}"
        )

        print(
            f"Timestamp  : {sample.get('timestamp')}"
        )

        print(
            f"TX Hash    : {sample.get('tx_hash')}"
        )

        print(
            f"Direction  : {sample.get('direction')}"
        )

        print(
            f"Status     : "
            f"{sample.get('transaction_status')}"
        )

        print(
            f"Chain      : {sample.get('chain')}"
        )

    # ----------------------------------------
    # EXPORT
    # ----------------------------------------

    export_blockchain_data(
        blockchain_data,
        "data/blockchain_data.json"
    )

    # ----------------------------------------
    # COMPLETE
    # ----------------------------------------

    print(
        "\n========================================"
    )

    print(
        "BLOCKCHAIN DATA PIPELINE COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        "\nClean data is ready for Chirag's "
        "graph module."
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()