from pathlib import Path
import json


BEHAVIORAL_WEIGHT = 0.30
ML_WEIGHT = 0.30
GRAPH_WEIGHT = 0.40


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, _safe_float(value)))


def _deduplicate(items):
    result = []

    for item in items:
        if item and item not in result:
            result.append(item)

    return result


def _risk_level(score):
    if score >= 75:
        return "HIGH"

    if score >= 40:
        return "MEDIUM"

    return "LOW"


def _behavioral_explanations(details):
    """
    Convert raw behavioral scoring details into
    human-readable investigation explanations.
    """

    explanations = []

    if not isinstance(details, dict):
        return explanations

    feature_names = {
        "transaction_count": "transaction count",
        "incoming_count": "incoming transaction count",
        "outgoing_count": "outgoing transaction count",
        "unique_senders": "unique sender count",
        "unique_receivers": "unique receiver count",
        "created_contracts": "created contract count",
        "total_eth_sent": "ETH sent",
        "total_eth_received": "ETH received",
        "eth_balance": "ETH balance",
        "erc20_transactions": "ERC20 transaction count",
        "erc20_unique_senders": "ERC20 unique sender count",
        "erc20_unique_receivers": "ERC20 unique receiver count",
    }

    for feature, detail in details.items():

        if not isinstance(detail, dict):
            continue

        value = _safe_float(detail.get("value", 0.0))
        percentile = _safe_float(detail.get("percentile", 0.0))
        score = _safe_float(detail.get("score", 0.0))

        if feature not in feature_names:
            continue

        readable_name = feature_names[feature]

        # Only report meaningful elevated behavior.
        if percentile >= 95:
            explanations.append(
                f"{readable_name.capitalize()} is unusually high "
                f"({value:g}), around the {percentile:.1f}th percentile."
            )

        elif percentile >= 90:
            explanations.append(
                f"{readable_name.capitalize()} is elevated "
                f"({value:g}), around the {percentile:.1f}th percentile."
            )

        elif score >= 45:
            explanations.append(
                f"{readable_name.capitalize()} shows elevated activity "
                f"({value:g}, {percentile:.1f}th percentile)."
            )

    return explanations


def _graph_compatibility_score(graph_features):
    """
    Temporary compatibility scoring.

    This exists only until the graph module supplies
    an explicit graph_score.
    """

    score = 0.0

    path_count = _safe_float(graph_features.get("path_count"))
    destination_count = _safe_float(
        graph_features.get("destination_count")
    )

    if path_count >= 10:
        score += 15
    elif path_count >= 5:
        score += 10
    elif path_count > 0:
        score += 5

    if destination_count >= 5:
        score += 15
    elif destination_count >= 3:
        score += 10
    elif destination_count >= 2:
        score += 5

    if graph_features.get("fund_splitting"):
        score += 20

    if graph_features.get("fund_consolidation"):
        score += 15

    if graph_features.get("rapid_movement"):
        score += 15

    if graph_features.get("high_value_transfer"):
        score += 20

    return _clamp(score)


def _graph_explanations(graph_features):
    explanations = []

    path_count = _safe_float(graph_features.get("path_count"))
    destination_count = _safe_float(
        graph_features.get("destination_count")
    )

    if path_count > 0:
        explanations.append(
            f"Multiple transaction paths were detected ({path_count:g} paths)."
        )

    if destination_count >= 2:
        explanations.append(
            f"Funds were distributed across multiple destinations "
            f"({destination_count:g})."
        )

    if graph_features.get("fund_splitting"):
        explanations.append(
            "Fund-splitting behavior was detected."
        )

    if graph_features.get("fund_consolidation"):
        explanations.append(
            "Fund-consolidation behavior was detected."
        )

    if graph_features.get("rapid_movement"):
        explanations.append(
            "Rapid fund movement was detected."
        )

    if graph_features.get("high_value_transfer"):
        explanations.append(
            "High-value transfers were detected."
        )

    if graph_features.get("max_hops", 0) >= 2:
        explanations.append(
            f"Multi-hop fund movement was detected "
            f"(maximum depth: {_safe_float(graph_features['max_hops']):g} hops)."
        )

    return explanations


def _extract_behavioral_output(behavioral_output):
    """
    Supports the existing behavioral_baseline return format
    without assuming it contains exactly two values.
    """

    if isinstance(behavioral_output, tuple):

        score = (
            behavioral_output[0]
            if len(behavioral_output) >= 1
            else 0.0
        )

        reasons = (
            behavioral_output[1]
            if len(behavioral_output) >= 2
            else {}
        )

        return _safe_float(score), reasons

    if isinstance(behavioral_output, dict):

        return (
            _safe_float(behavioral_output.get("score", 0.0)),
            behavioral_output.get("reasons", {}),
        )

    return _safe_float(behavioral_output), {}


def calculate_risk(
    wallet_features,
    ml_result,
    graph_result,
    vasp_result=None,
    behavioral_baseline=None,
):
    """
    Final Student 4 risk engine.

    Final Risk =
        30% Behavioral
        30% ML
        40% Graph

    VASP attribution is evidence only.
    It does NOT modify the numerical risk score.
    """

    # ---------------------------------------------------------
    # Behavioral score
    # ---------------------------------------------------------

    if behavioral_baseline is None:

        baseline_path = Path("data/behavioral_baseline.json")
        if not baseline_path.exists():
            alt_path = Path(__file__).parent.parent / "data" / "behavioral_baseline.json"
            if alt_path.exists():
                baseline_path = alt_path

        if baseline_path.exists():

            with open(
                baseline_path,
                "r",
                encoding="utf-8",
            ) as f:
                behavioral_baseline = json.load(f)

    from .behavioral_baseline import calculate_behavioral_score

    behavioral_output = calculate_behavioral_score(
        wallet_features,
        behavioral_baseline,
    )

    behavioral_score, behavioral_details = (
        _extract_behavioral_output(behavioral_output)
    )

    behavioral_score = _clamp(behavioral_score)

    # ---------------------------------------------------------
    # ML score
    # ---------------------------------------------------------

    ml_result = ml_result or {}

    if "ml_score" in ml_result:
        ml_score = _safe_float(ml_result["ml_score"])

    else:
        fraud_probability = _safe_float(
            ml_result.get("fraud_probability", 0.0)
        )

        ml_score = fraud_probability * 100.0

    ml_score = _clamp(ml_score)

    fraud_probability = _safe_float(
        ml_result.get("fraud_probability", ml_score / 100.0)
    )

    ml_prediction = ml_result.get(
        "prediction",
        "UNKNOWN",
    )

    # ---------------------------------------------------------
    # Graph score
    # ---------------------------------------------------------

    graph_result = graph_result or {}

    graph_features = graph_result.get(
        "features",
        {},
    )

    if "graph_score" in graph_result:

        graph_score = _clamp(
            graph_result["graph_score"]
        )

        graph_score_source = "graph_module"

    else:

        graph_score = _graph_compatibility_score(
            graph_features
        )

        graph_score_source = "compatibility"

    # ---------------------------------------------------------
    # Final score
    # ---------------------------------------------------------

    final_score = (
        BEHAVIORAL_WEIGHT * behavioral_score
        + ML_WEIGHT * ml_score
        + GRAPH_WEIGHT * graph_score
    )

    final_score = round(
        _clamp(final_score),
        2,
    )

    # ---------------------------------------------------------
    # Risk level
    # ---------------------------------------------------------

    risk_level = _risk_level(final_score)

    # ---------------------------------------------------------
    # Explanations
    # ---------------------------------------------------------

    reasons = []

    reasons.extend(
        _behavioral_explanations(
            behavioral_details
        )
    )

    reasons.extend(
        _graph_explanations(
            graph_features
        )
    )

    # ML explanation
    if fraud_probability >= 0.70:

        reasons.append(
            f"ML model indicates elevated fraud likelihood "
            f"({fraud_probability * 100:.1f}%)."
        )

    elif fraud_probability >= 0.50:

        reasons.append(
            f"ML model indicates moderate fraud likelihood "
            f"({fraud_probability * 100:.1f}%)."
        )

    else:

        reasons.append(
            f"ML model currently classifies the wallet as "
            f"{ml_prediction.lower()} "
            f"({fraud_probability * 100:.1f}% fraud probability)."
        )

    reasons = _deduplicate(reasons)

    # ---------------------------------------------------------
    # VASP evidence
    # ---------------------------------------------------------

    vasp_result = vasp_result or {}

    vasp_matches = vasp_result.get(
        "vasp_matches",
        [],
    )

    vasp_evidence = []

    for match in vasp_matches:

        vasp_evidence.append(
            {
                "entity_name": match.get(
                    "entity_name",
                    "Unknown",
                ),
                "entity_type": match.get(
                    "entity_type",
                    "Unknown",
                ),
                "vasp_category": match.get(
                    "vasp_category",
                    "Unknown",
                ),
                "confidence_score": _safe_float(
                    match.get(
                        "confidence_score",
                        0.0,
                    )
                ),
                "match_status": match.get(
                    "match_status",
                    "unknown",
                ),
                "interaction_count": int(
                    _safe_float(
                        match.get(
                            "interaction_count",
                            0,
                        )
                    )
                ),
                "hop_distance": int(
                    _safe_float(
                        match.get(
                            "hop_distance",
                            0,
                        )
                    )
                ),
                "jurisdiction": match.get(
                    "jurisdiction",
                    "Unknown",
                ),
                "source": match.get(
                    "source",
                    "Unknown",
                ),
                "address": match.get(
                    "address",
                    "",
                ),
            }
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return {
        "suspect_wallet": wallet_features.get(
            "suspect_wallet",
            "",
        ),

        "risk_score": final_score,
        "risk_level": risk_level,
        "risk_category": risk_level,

        "behavioral_score": round(
            behavioral_score,
            2,
        ),

        "ml_score": round(
            ml_score,
            2,
        ),

        "graph_score": round(
            graph_score,
            2,
        ),

        "component_scores": {
            "behavioral": round(
                behavioral_score,
                2,
            ),
            "ml": round(
                ml_score,
                2,
            ),
            "graph": round(
                graph_score,
                2,
            ),
        },

        "weights": {
            "behavioral": BEHAVIORAL_WEIGHT,
            "ml": ML_WEIGHT,
            "graph": GRAPH_WEIGHT,
        },

        "fraud_probability": round(
            fraud_probability,
            4,
        ),

        "ml_prediction": ml_prediction,

        "graph_score_source": graph_score_source,

        "reasons": reasons,

        "behavioral_details": behavioral_details,

        "graph_reasons": _graph_explanations(
            graph_features
        ),

        "vasp_attribution": vasp_evidence,

        "vasp_evidence": vasp_evidence,
    }