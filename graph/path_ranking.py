import hashlib
import math


def generate_path_id(path):
    """
    Generate a stable ID for a money-flow path.

    The ID depends on the wallets in the path,
    not on its ranking position.
    """
    path_string = "->".join(
        str(wallet).lower().strip()
        for wallet in path
    )

    hash_value = hashlib.sha256(
        path_string.encode("utf-8")
    ).hexdigest()

    return f"PATH-{hash_value[:8].upper()}"


def rank_paths(paths, graph=None, top_n=10):
    """
    Rank money-flow paths according to investigative importance.

    Scoring factors:
    - Continuous transfer value (higher volume = significantly higher score)
    - Value retention along the path (tight laundering chains rewarded)
    - Number of hops (deeper movement penalized for decay, rewarded for obfuscation)
    - Rapid movement / velocity
    - Fund splitting / fan-out
    """
    ranked_paths = []

    for path_data in paths:
        path = path_data.get("path", [])
        transactions = path_data.get("transactions", [])

        if not path or not transactions:
            continue

        hops = len(path) - 1

        # --------------------------------------------------
        # 1. GET CHRONOLOGICAL TRANSACTIONS
        # --------------------------------------------------
        chronological_flow = path_data.get("chronological_flow", {})
        chronological_transactions = (
            chronological_flow.get("transactions", [])
            if isinstance(chronological_flow, dict)
            else []
        )

        flow_transactions = (
            chronological_transactions
            if chronological_transactions
            else transactions
        )

        # --------------------------------------------------
        # 2. EXTRACT POSITIVE TRANSACTION AMOUNTS
        # --------------------------------------------------
        amounts = []
        for tx in flow_transactions:
            amount = tx.get("amount", 0)
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = 0.0

            if amount > 0:
                amounts.append(amount)

        if not amounts:
            continue

        first_amount = amounts[0]
        final_amount = amounts[-1]

        # --------------------------------------------------
        # 3. VALUE RETENTION
        # --------------------------------------------------
        if first_amount > 0:
            raw_retention = final_amount / first_amount
        else:
            raw_retention = 0.0

        value_retention = max(0.0, min(raw_retention, 1.0))

        score = 0.0
        reasons = []

        # --------------------------------------------------
        # 4. CONTINUOUS VOLUME SCORING (Up to 45 pts)
        # Scaled dynamically so 100 ETH drastically beats 25 ETH
        # --------------------------------------------------
        if first_amount >= 100.0:
            score += 45.0
            reasons.append("massive value transfer")
        elif first_amount >= 50.0:
            score += 35.0
            reasons.append("very high value transfer")
        elif first_amount >= 10.0:
            # Scale smoothly between 20 and 30 points for 10-50 ETH
            score += 20.0 + (first_amount - 10.0) * 0.25
            reasons.append("high value transfer")
        elif first_amount >= 1.0:
            score += 10.0 + (first_amount - 1.0) * 1.0
            reasons.append("significant value transfer")
        elif first_amount >= 0.1:
            score += 5.0
            reasons.append("moderate value transfer")

        # --------------------------------------------------
        # 5. MULTI-HOP OBFUSCATION (Up to 25 pts)
        # --------------------------------------------------
        if hops >= 5:
            score += 25.0
            reasons.append("long multi-hop path")
        elif hops >= 4:
            score += 20.0
            reasons.append("multi-hop movement (4 hops)")
        elif hops >= 3:
            score += 15.0
            reasons.append("multi-hop movement")
        elif hops >= 2:
            score += 10.0
            reasons.append("multi-hop movement")

        # --------------------------------------------------
        # 6. VALUE RETENTION (Up to 20 pts)
        # Highly retained multi-hop flows indicate deliberate laundering
        # --------------------------------------------------
        if hops >= 2:
            if value_retention >= 0.90:
                score += 20.0
                reasons.append("high value retention")
            elif value_retention >= 0.70:
                score += 12.0
                reasons.append("moderate value retention")
            elif value_retention >= 0.50:
                score += 6.0

        # --------------------------------------------------
        # 7. RAPID MOVEMENT (Up to 15 pts)
        # --------------------------------------------------
        velocity = path_data.get("velocity", {})
        if velocity.get("rapid_movement"):
            score += 15.0
            reasons.append("rapid movement")

        # --------------------------------------------------
        # 8. FUND SPLITTING (Up to 10 pts)
        # --------------------------------------------------
        if graph is not None:
            for node in path:
                try:
                    outgoing_count = graph.out_degree(node)
                except Exception:
                    outgoing_count = 0

                if outgoing_count >= 2:
                    score += 10.0
                    reasons.append("fund splitting")
                    break

        score = min(round(score, 2), 100.0)

        path_id = generate_path_id(path)

        ranked_paths.append({
            "path_id": path_id,
            "path": path,
            "hops": hops,
            "amount": first_amount,
            "final_amount": final_amount,
            "value_retention": round(value_retention, 4),
            "value_retention_percent": round(value_retention * 100, 2),
            "score": score,
            "reasons": reasons,
            "indicators": reasons,  # Synced alias for main.py
            "transactions": transactions
        })

    # ------------------------------------------------------
    # MULTI-LEVEL SORT:
    # 1. Primary: Highest Score
    # 2. Secondary: Highest Final Amount (Volume tie-break)
    # 3. Tertiary: Longest Hops (Deepest trace)
    # ------------------------------------------------------
    ranked_paths.sort(
        key=lambda item: (
            item["score"],
            item["final_amount"],
            item["hops"]
        ),
        reverse=True
    )

    final_paths = ranked_paths[:top_n]

    for index, path_data in enumerate(final_paths, start=1):
        path_data["rank"] = index

    return final_paths