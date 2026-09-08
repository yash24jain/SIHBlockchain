import json
from pathlib import Path


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_vasp_evidence(suspect_wallet, path):
    """
    Consume VASP attribution produced by the VASP/entity module.

    This adapter does not perform attribution.
    It only normalizes attribution evidence for the risk engine.
    """

    path = Path(path)

    if not path.exists():
        return {
            "suspect_wallet": suspect_wallet,
            "chain": "ethereum",
            "vasp_matches": [],
        }

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        raw = json.load(f)

    matches = []

    for match in raw.get(
        "vasp_matches",
        [],
    ):

        if not isinstance(match, dict):
            continue

        normalized = dict(match)

        normalized["confidence_score"] = _safe_float(
            match.get(
                "confidence_score",
                0.0,
            )
        )

        normalized["interaction_count"] = _safe_int(
            match.get(
                "interaction_count",
                0,
            )
        )

        normalized["incoming_interactions"] = _safe_int(
            match.get(
                "incoming_interactions",
                0,
            )
        )

        normalized["outgoing_interactions"] = _safe_int(
            match.get(
                "outgoing_interactions",
                0,
            )
        )

        normalized["hop_distance"] = _safe_int(
            match.get(
                "hop_distance",
                0,
            )
        )

        if not isinstance(
            normalized.get(
                "matched_transaction_hashes"
            ),
            list,
        ):
            normalized[
                "matched_transaction_hashes"
            ] = []

        if not isinstance(
            normalized.get(
                "confidence_reasons"
            ),
            list,
        ):
            normalized[
                "confidence_reasons"
            ] = []

        matches.append(normalized)

    return {
        "suspect_wallet": suspect_wallet,
        "chain": raw.get(
            "chain",
            "ethereum",
        ),
        "vasp_matches": matches,
    }