def extract_path_evidence(path_data):
    """
    Convert ranked path information into structured
    investigative evidence.

    This does not calculate a new risk score.
    It only extracts evidence/features for the
    downstream risk engine.
    """

    reasons = path_data.get("reasons", [])

    velocity = path_data.get("velocity", {})

    evidence = {
        "high_value_transfer": (
            "high value transfer" in reasons
            or "significant value transfer" in reasons
        ),

        "multi_hop": (
            path_data.get("hops", 0) >= 2
        ),

        "long_multi_hop": (
            path_data.get("hops", 0) >= 5
        ),

        "high_value_retention": (
            "high value retention" in reasons
        ),

        "moderate_value_retention": (
            "moderate value retention" in reasons
        ),

        "fund_splitting": (
            "fund splitting" in reasons
        ),

        "rapid_movement": (
            velocity.get("rapid_movement", False)
        ),

        "transaction_count": len(
            path_data.get("transactions", [])
        ),

        "hop_count": path_data.get("hops", 0),

        "amount": path_data.get("amount", 0),

        "final_amount": path_data.get(
            "final_amount", 0
        ),

        "value_retention": path_data.get(
            "value_retention", 0
        )
    }

    return evidence


if __name__ == "__main__":

    sample_path = {
        "hops": 2,
        "amount": 3.294102,
        "final_amount": 0.06,
        "value_retention": 0.0182,
        "reasons": [
            "significant value transfer",
            "multi-hop movement",
            "fund splitting"
        ],
        "transactions": [
            {"amount": 3.294102},
            {"amount": 0.06}
        ],
        "velocity": {
            "rapid_movement": False
        }
    }

    result = extract_path_evidence(
        sample_path
    )

    print(result)