import json
from pathlib import Path


GRAPH_FEATURE_KEYS = [
    "wallet_count",
    "transaction_count",
    "total_outgoing_value",
    "destination_count",
    "max_hops",
    "path_count",
    "critical_path_count",
    "max_path_hops",
    "max_path_value",
    "average_path_value",
    "fund_splitting",
    "fund_consolidation",
    "rapid_movement",
    "high_value_transfer",
    "average_value_retention",
    "high_value_retention_paths",
]


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_features(features):
    return {
        key: _safe_float(features.get(key, 0.0))
        for key in GRAPH_FEATURE_KEYS
    }


def calculate_graph_score(features):
    """
    Calculate the Graph Risk Score from graph-analysis features.

    The graph-analysis teammate is responsible for producing the
    graph features.

    Student 4 is responsible for converting those features into
    a normalized 0-100 graph risk score.

    Returns:
        {
            "graph_score": float,
            "graph_reasons": list[str]
        }
    """

    score = 0.0
    reasons = []

    # ---------------------------------------------------------
    # 1. Suspicious path activity
    # ---------------------------------------------------------

    path_count = features.get("path_count", 0.0)

    if path_count >= 10:
        score += 15
        reasons.append(
            f"Multiple suspicious transaction paths detected ({int(path_count)} paths)."
        )
    elif path_count >= 5:
        score += 10
        reasons.append(
            f"Several transaction paths detected ({int(path_count)} paths)."
        )
    elif path_count > 0:
        score += 5
        reasons.append(
            f"Transaction path activity detected ({int(path_count)} path(s))."
        )

    # ---------------------------------------------------------
    # 2. Multiple destinations
    # ---------------------------------------------------------

    destination_count = features.get("destination_count", 0.0)

    if destination_count >= 5:
        score += 15
        reasons.append(
            f"Funds were distributed across many destinations ({int(destination_count)})."
        )
    elif destination_count >= 3:
        score += 10
        reasons.append(
            f"Funds were distributed across multiple destinations ({int(destination_count)})."
        )
    elif destination_count >= 2:
        score += 5
        reasons.append(
            f"Multiple destination wallets were observed ({int(destination_count)})."
        )

    # ---------------------------------------------------------
    # 3. Fund splitting
    # ---------------------------------------------------------

    if features.get("fund_splitting", 0.0) > 0:
        score += 20
        reasons.append(
            "Fund-splitting behavior was detected."
        )

    # ---------------------------------------------------------
    # 4. Fund consolidation
    # ---------------------------------------------------------

    if features.get("fund_consolidation", 0.0) > 0:
        score += 15
        reasons.append(
            "Fund-consolidation behavior was detected."
        )

    # ---------------------------------------------------------
    # 5. Rapid movement
    # ---------------------------------------------------------

    if features.get("rapid_movement", 0.0) > 0:
        score += 15
        reasons.append(
            "Rapid movement of funds across the transaction graph was detected."
        )

    # ---------------------------------------------------------
    # 6. High-value transfers
    # ---------------------------------------------------------

    if features.get("high_value_transfer", 0.0) > 0:
        score += 20
        reasons.append(
            "High-value transfers were detected in the transaction graph."
        )

    # ---------------------------------------------------------
    # Keep score within 0-100
    # ---------------------------------------------------------

    score = min(max(score, 0.0), 100.0)

    return {
        "graph_score": round(score, 2),
        "graph_reasons": reasons,
    }


def load_graph_output(path, suspect_wallet):
    """
    Load graph-analysis output produced by the graph-analysis module.

    Student 4 does NOT build the graph or trace transactions here.

    The graph-analysis teammate provides the graph features.
    This module normalizes those features and calculates the
    Graph Risk Score from them.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Graph output file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    features = raw.get("features", raw)

    normalized_features = _normalize_features(features)

    # ---------------------------------------------------------
    # Calculate graph score from graph teammate's features
    # ---------------------------------------------------------

    graph_result = calculate_graph_score(normalized_features)

    output = {
        "suspect_wallet": suspect_wallet,
        "chain": raw.get("chain", "ethereum"),
        "features": normalized_features,
        "graph_score": graph_result["graph_score"],
        "graph_reasons": graph_result["graph_reasons"],
    }

    # Preserve paths if supplied by the graph module.
    if "paths" in raw:
        output["paths"] = raw["paths"]

    return output
