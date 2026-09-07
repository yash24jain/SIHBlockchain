def extract_ml_features(result):
    """
    Convert forensic investigation output into
    ML-ready features.

    Expected path structure:

    {
        "path": [...],
        "hops": 2,
        "transactions": [
            {
                "from": "...",
                "to": "...",
                "amount": 3.0,
                "timestamp": "..."
            },
            ...
        ]
    }

    Returns:
        dict: Flat ML feature dictionary.
    """

    wallets = result.get("wallets", [])
    transactions = result.get("transactions", [])
    paths = result.get("paths", [])
    critical_paths = result.get("critical_paths", [])
    forensics = result.get("forensics", {})

    # =========================================================
    # BASIC FEATURES
    # =========================================================

    wallet_count = len(wallets)
    transaction_count = len(transactions)

    # =========================================================
    # SUSPECT WALLET
    # =========================================================

    suspect_wallet = str(
        result.get("suspect_wallet", "")
    ).lower()

    # =========================================================
    # OUTGOING VALUE
    # =========================================================

    total_outgoing_value = 0.0
    destinations = set()

    for tx in transactions:

        sender = str(
            tx.get("from", "")
        ).lower()

        receiver = str(
            tx.get("to", "")
        ).lower()

        try:
            amount = float(
                tx.get("amount", 0)
            )
        except (TypeError, ValueError):
            amount = 0.0

        if sender == suspect_wallet:

            total_outgoing_value += amount

            if receiver:
                destinations.add(receiver)

    destination_count = len(destinations)

    # =========================================================
    # PATH FEATURES
    # =========================================================

    path_count = len(paths)

    critical_path_count = len(
        critical_paths
    )

    max_path_hops = 0

    path_values = []
    retention_values = []

    high_value_retention_paths = 0

    # =========================================================
    # PROCESS EACH PATH
    # =========================================================

    for path in paths:

        # -----------------------------------------------------
        # HOPS
        # -----------------------------------------------------

        try:
            hops = int(
                path.get("hops", 0)
            )
        except (TypeError, ValueError):
            hops = 0

        max_path_hops = max(
            max_path_hops,
            hops
        )

        # -----------------------------------------------------
        # PATH TRANSACTIONS
        # -----------------------------------------------------

        path_transactions = path.get(
            "transactions",
            []
        )

        if not isinstance(
            path_transactions,
            list
        ):
            path_transactions = []

        if not path_transactions:
            continue

        # -----------------------------------------------------
        # SORT TRANSACTIONS CHRONOLOGICALLY
        # -----------------------------------------------------

        sorted_transactions = sorted(
            path_transactions,
            key=lambda tx: str(
                tx.get("timestamp", "")
            )
        )

        # =====================================================
        # FIRST TRANSACTION FROM SUSPECT
        # =====================================================

        first_amount = None

        for tx in sorted_transactions:

            sender = str(
                tx.get("from", "")
            ).lower()

            if sender == suspect_wallet:

                try:
                    amount = float(
                        tx.get("amount", 0)
                    )
                except (TypeError, ValueError):
                    amount = 0.0

                if amount > 0:
                    first_amount = amount
                    break

        # =====================================================
        # PATH VALUE
        #
        # Path value = amount initially sent
        # by the suspect wallet.
        # =====================================================

        if first_amount is not None:

            path_values.append(
                first_amount
            )

        # =====================================================
        # VALUE RETENTION
        #
        # Only meaningful for multi-hop paths.
        #
        # retention =
        # final amount / initial amount
        #
        # Clamped to [0, 1].
        # =====================================================

        if (
            hops >= 2
            and first_amount is not None
        ):

            final_amount = None

            # -------------------------------------------------
            # Find the final valid transaction
            # -------------------------------------------------

            for tx in reversed(
                sorted_transactions
            ):

                try:
                    amount = float(
                        tx.get("amount", 0)
                    )
                except (
                    TypeError,
                    ValueError
                ):
                    amount = 0.0

                if amount > 0:

                    final_amount = amount
                    break

            # -------------------------------------------------
            # Calculate retention
            # -------------------------------------------------

            if (
                final_amount is not None
                and first_amount > 0
            ):

                retention = (
                    final_amount
                    / first_amount
                )

                # Keep retention between 0 and 1
                retention = min(
                    max(retention, 0.0),
                    1.0
                )

                retention_values.append(
                    retention
                )

                if retention >= 0.8:
                    high_value_retention_paths += 1

    # =========================================================
    # PATH VALUE STATISTICS
    # =========================================================

    if path_values:

        max_path_value = max(
            path_values
        )

        average_path_value = (
            sum(path_values)
            / len(path_values)
        )

    else:

        max_path_value = 0.0
        average_path_value = 0.0

    # =========================================================
    # RETENTION STATISTICS
    # =========================================================

    if retention_values:

        average_value_retention = (
            sum(retention_values)
            / len(retention_values)
        )

    else:

        average_value_retention = None

    # =========================================================
    # FORENSIC FEATURES
    # =========================================================

    splitting = forensics.get(
        "splitting"
    )

    consolidation = forensics.get(
        "consolidation"
    )

    rapid_movements = forensics.get(
        "rapid_movements",
        []
    )

    fund_splitting = (
        1 if splitting else 0
    )

    fund_consolidation = (
        1 if consolidation else 0
    )

    rapid_movement = (
        1 if rapid_movements else 0
    )

    # =========================================================
    # HIGH VALUE TRANSFER
    #
    # Threshold:
    # amount >= 1 ETH
    # =========================================================

    high_value_transfer = 0

    for tx in transactions:

        try:
            amount = float(
                tx.get("amount", 0)
            )
        except (TypeError, ValueError):
            amount = 0.0

        if amount >= 1:

            high_value_transfer = 1
            break

    # =========================================================
    # FINAL ML FEATURE VECTOR
    # =========================================================

    return {

        "wallet_count":
            wallet_count,

        "transaction_count":
            transaction_count,

        "total_outgoing_value":
            round(
                total_outgoing_value,
                6
            ),

        "destination_count":
            destination_count,

        "max_hops":
            result.get(
                "max_hops",
                0
            ),

        "path_count":
            path_count,

        "critical_path_count":
            critical_path_count,

        "max_path_hops":
            max_path_hops,

        "max_path_value":
            round(
                max_path_value,
                6
            ),

        "average_path_value":
            round(
                average_path_value,
                6
            ),

        "fund_splitting":
            fund_splitting,

        "fund_consolidation":
            fund_consolidation,

        "rapid_movement":
            rapid_movement,

        "high_value_transfer":
            high_value_transfer,

        "average_value_retention":
            (
                round(
                    average_value_retention,
                    4
                )
                if average_value_retention is not None
                else None
            ),

        "high_value_retention_paths":
            high_value_retention_paths
    }