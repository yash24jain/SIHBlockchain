from graph.traversal import find_paths
from graph.features import analyze_path
from analysis.splitting import detect_fund_splitting
from analysis.consolidation import detect_fund_consolidation
from analysis.velocity import calculate_path_velocity
from graph.chronology import build_chronological_flow
from graph.path_ranking import rank_paths
from graph.path_summary import build_path_summary
from analysis.evidence import extract_path_evidence
from graph.path_selection import get_selected_path
from graph.path_expansion import expand_path
from analysis.features import extract_ml_features


def investigate_wallet(graph, wallet, max_hops=4):

    wallet = wallet.lower().strip()

    # ---------------------------------------------------------
    # FIND MONEY-FLOW PATHS
    # ---------------------------------------------------------
    paths = find_paths(
        graph,
        wallet,
        max_hops
    )

    result = {
        "suspect_wallet": wallet,
        "chain": "ethereum",
        "max_hops": max_hops,
        "wallets": [],
        "transactions": [],
        "paths": [],
        "critical_paths": [],
        "forensics": {
            "splitting": None,
            "consolidation": None,
            "rapid_movements": []
        }
    }

    # ---------------------------------------------------------
    # WALLET INFORMATION
    # ---------------------------------------------------------
    for node in graph.nodes:
        result["wallets"].append({
            "address": node,
            "hop": graph.nodes[node].get("hop")
        })

    # ---------------------------------------------------------
    # TRANSACTIONS
    # ---------------------------------------------------------
    for sender, receiver, data in graph.edges(data=True):
        result["transactions"].append({
            "from": sender,
            "to": receiver,
            "amount": data.get("amount"),
            "timestamp": data.get("timestamp"),
            "tx_hash": data.get("tx_hash")
        })

    # ---------------------------------------------------------
    # PRUNE SUB-PATH PREFIXES
    # Drop intermediate 1-hop / 2-hop slices if a longer extension exists
    # ---------------------------------------------------------
    path_tuples = [tuple(p) for p in paths]
    path_set = set(path_tuples)

    # A path is maximal if no other path starts with it and has greater length
    maximal_paths = [
        list(p) for p in path_tuples
        if not any(
            len(other) > len(p) and other[:len(p)] == p
            for other in path_set
        )
    ]

    # Target evaluating maximal paths first, fallback to all paths if empty
    eval_paths = maximal_paths if maximal_paths else paths

    # ---------------------------------------------------------
    # MONEY FLOW PATHS EVALUATION
    # ---------------------------------------------------------
    rankable_paths = []

    for path in eval_paths:

        # Analyze path metrics & attributes
        path_data = analyze_path(
            graph,
            path
        )

        # Build chronological transaction flow
        chronological_flow = build_chronological_flow(
            graph,
            path
        )

        # Calculate transaction velocity
        velocity = calculate_path_velocity(
            graph,
            path
        )

        path_result = {
            "path": path_data.get("path", path),
            "hops": path_data.get("hops", len(path) - 1),
            "chronological_flow": chronological_flow,
            "transactions": path_data.get("transactions", [])
        }

        # -----------------------------------------------------
        # VELOCITY & RAPID MOVEMENT
        # -----------------------------------------------------
        if velocity:
            path_result["velocity"] = {
                "duration_seconds": velocity.get("duration_seconds"),
                "hops_per_minute": velocity.get("hops_per_minute"),
                "rapid_movement": velocity.get("rapid_movement", False)
            }

            if velocity.get("rapid_movement"):
                result["forensics"]["rapid_movements"].append(
                    path_result
                )

        # Save to all discovered candidate paths
        result["paths"].append(path_result)

        # -----------------------------------------------------
        # VALIDATE CHRONOLOGY FOR RANKING
        # -----------------------------------------------------
        chronological_transactions = (
            chronological_flow.get("transactions", [])
            if isinstance(chronological_flow, dict)
            else []
        )

        is_chronological = (
            isinstance(chronological_flow, dict)
            and chronological_flow.get("chronological", False)
        )

        if is_chronological and len(chronological_transactions) > 0:
            rankable_paths.append(path_result)
        else:
            if len(path) > 2:
                print(
                    f"[DEBUG - Chronology Rejected] Hops: {len(path) - 1} | "
                    f"Path: {' -> '.join(path)}"
                )

    # ---------------------------------------------------------
    # CRITICAL PATH RANKING
    # If no paths passed chronology, fallback to candidate paths
    # ---------------------------------------------------------
    paths_to_rank = rankable_paths if rankable_paths else result["paths"]

    critical_paths = rank_paths(
        paths_to_rank,
        graph=graph,
        top_n=10
    )

    # ---------------------------------------------------------
    # ADD SUMMARY + EVIDENCE
    # ---------------------------------------------------------
    for path_data in critical_paths:

        path_summary = build_path_summary(
            path_data
        )

        if isinstance(path_summary, dict):
            path_data.update(path_summary)

        evidence = extract_path_evidence(
            path_data
        )

        path_data["evidence"] = evidence

    result["critical_paths"] = critical_paths

    # ---------------------------------------------------------
    # FUND SPLITTING
    # ---------------------------------------------------------
    splitting = detect_fund_splitting(
        graph,
        wallet
    )

    if splitting and splitting.get("is_split"):
        result["forensics"]["splitting"] = splitting

    # ---------------------------------------------------------
    # FUND CONSOLIDATION
    # ---------------------------------------------------------
    consolidation = detect_fund_consolidation(
        graph,
        wallet
    )

    if consolidation and consolidation.get("is_consolidation"):
        result["forensics"]["consolidation"] = consolidation

    # ---------------------------------------------------------
    # ML FEATURES
    # ---------------------------------------------------------
    features = extract_ml_features(result)
    result["features"] = features

    return result


# =============================================================
# SELECT INVESTIGATION PATH
# =============================================================

def select_investigation_path(
    result,
    path_id
):
    """
    Select one ranked critical path for investigation.
    """
    return get_selected_path(
        result.get(
            "critical_paths",
            []
        ),
        path_id
    )


# =============================================================
# EXPAND INVESTIGATION PATH
# =============================================================

def expand_investigation_path(
    graph,
    selected_path,
    additional_hops=1
):
    """
    Continue investigation from the final wallet
    of the selected path.
    """
    return expand_path(
        graph,
        selected_path,
        additional_hops
    )