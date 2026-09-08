from src.risk_engine import calculate_risk


def test_final_risk_uses_three_scores():
    wallet_features = {
        "transaction_count": 29,
        "incoming_count": 19,
        "outgoing_count": 10,
        "unique_senders": 14,
        "unique_receivers": 3,
        "created_contracts": 0,
        "time_active_minutes": 1000,
        "avg_time_between_sent": 500,
        "avg_time_between_received": 500,
        "total_eth_sent": 100,
        "total_eth_received": 100,
        "eth_balance": 0,
        "erc20_transactions": 10,
        "erc20_unique_senders": 10,
        "erc20_unique_receivers": 0,
    }

    ml_result = {
        "fraud_probability": 0.72,
        "prediction": "FRAUD",
    }

    graph_result = {
        "suspect_wallet": "0xabc",
        "chain": "ethereum",
        "graph_score": 80,
        "features": {
            "wallet_count": 10,
            "transaction_count": 20,
            "total_outgoing_value": 1000,
            "destination_count": 5,
            "max_hops": 3,
            "path_count": 10,
            "critical_path_count": 2,
            "max_path_hops": 3,
            "max_path_value": 500,
            "average_path_value": 100,
            "fund_splitting": 1,
            "fund_consolidation": 1,
            "rapid_movement": 1,
            "high_value_transfer": 1,
            "average_value_retention": 0.5,
            "high_value_retention_paths": 2,
        },
    }

    baseline = {
        "feature_stats": {
            "transaction_count": {
                "min": 1,
                "q25": 4,
                "median": 11,
                "q75": 85,
                "q90": 370,
                "q95": 1229,
                "q99": 10000,
                "max": 20000,
            },
            "incoming_count": {
                "min": 0,
                "q25": 2,
                "median": 5,
                "q75": 40,
                "q90": 171,
                "q95": 556,
                "q99": 6793,
                "max": 10000,
            },
            "outgoing_count": {
                "min": 0,
                "q25": 1,
                "median": 3,
                "q75": 16,
                "q90": 127,
                "q95": 379,
                "q99": 4456,
                "max": 10000,
            },
            "unique_senders": {
                "min": 0,
                "q25": 1,
                "median": 2,
                "q75": 5,
                "q90": 10,
                "q95": 19,
                "q99": 946,
                "max": 9999,
            },
            "unique_receivers": {
                "min": 0,
                "q25": 1,
                "median": 2,
                "q75": 3,
                "q90": 16,
                "q95": 42,
                "q99": 566,
                "max": 9287,
            },
            "created_contracts": {
                "min": 0,
                "q25": 0,
                "median": 0,
                "q75": 0,
                "q90": 1,
                "q95": 1,
                "q99": 1,
                "max": 9995,
            },
            "total_eth_sent": {
                "min": 0,
                "q25": 1,
                "median": 34,
                "q75": 101,
                "q90": 1672,
                "q95": 2004,
                "q99": 45162,
                "max": 28580960,
            },
            "total_eth_received": {
                "min": 0,
                "q25": 8.5,
                "median": 71,
                "q75": 120,
                "q90": 1845,
                "q95": 2191,
                "q99": 59937,
                "max": 28581590,
            },
            "eth_balance": {
                "min": -1000,
                "q25": 0,
                "median": 0.002,
                "q75": 0.1,
                "q90": 40,
                "q95": 109,
                "q99": 1604,
                "max": 1000,
            },
            "erc20_transactions": {
                "min": 0,
                "q25": 0,
                "median": 0,
                "q75": 3,
                "q90": 23,
                "q95": 69,
                "q99": 326,
                "max": 10001,
            },
            "erc20_unique_senders": {
                "min": 0,
                "q25": 0,
                "median": 0,
                "q75": 0,
                "q90": 2,
                "q95": 9,
                "q99": 42,
                "max": 6582,
            },
            "erc20_unique_receivers": {
                "min": 0,
                "q25": 0,
                "median": 0,
                "q75": 2,
                "q90": 11,
                "q95": 26,
                "q99": 81,
                "max": 4293,
            },
        }
    }

    vasp_result = {
        "suspect_wallet": "0xabc",
        "chain": "ethereum",
        "vasp_matches": [
            {
                "entity_name": "Binance",
                "confidence_score": 0.9,
                "direction": "INCOMING",
            }
        ],
    }

    result = calculate_risk(
        wallet_features=wallet_features,
        ml_result=ml_result,
        graph_result=graph_result,
        vasp_result=vasp_result,
        behavioral_baseline=baseline,
    )

    assert "risk_score" in result

    assert 0 <= result["risk_score"] <= 100
    assert 0 <= result["behavioral_score"] <= 100
    assert 0 <= result["ml_score"] <= 100
    assert 0 <= result["graph_score"] <= 100

    assert result["ml_score"] == 72
    assert result["graph_score"] == 80

    assert result["weights"]["behavioral"] == 0.30
    assert result["weights"]["ml"] == 0.30
    assert result["weights"]["graph"] == 0.40

    assert "vasp_evidence" in result
    assert len(result["vasp_evidence"]) == 1
    assert result["vasp_evidence"][0]["entity_name"] == "Binance"


def test_vasp_does_not_change_risk_score():
    wallet_features = {
        "transaction_count": 10,
        "incoming_count": 5,
        "outgoing_count": 5,
        "unique_senders": 2,
        "unique_receivers": 2,
        "created_contracts": 0,
        "time_active_minutes": 100,
        "avg_time_between_sent": 10,
        "avg_time_between_received": 10,
        "total_eth_sent": 10,
        "total_eth_received": 10,
        "eth_balance": 0,
        "erc20_transactions": 2,
        "erc20_unique_senders": 1,
        "erc20_unique_receivers": 1,
    }

    ml_result = {
        "fraud_probability": 0.5,
        "prediction": "FRAUD",
    }

    graph_result = {
        "graph_score": 50,
        "features": {},
    }

    baseline = {
        "feature_stats": {
            feature: {
                "min": 0,
                "q25": 1,
                "median": 10,
                "q75": 20,
                "q90": 30,
                "q95": 40,
                "q99": 50,
                "max": 100,
            }
            for feature in [
                "transaction_count",
                "incoming_count",
                "outgoing_count",
                "unique_senders",
                "unique_receivers",
                "created_contracts",
                "total_eth_sent",
                "total_eth_received",
                "eth_balance",
                "erc20_transactions",
                "erc20_unique_senders",
                "erc20_unique_receivers",
            ]
        }
    }

    no_vasp = calculate_risk(
        wallet_features,
        ml_result,
        graph_result,
        None,
        baseline,
    )

    with_vasp = calculate_risk(
        wallet_features,
        ml_result,
        graph_result,
        {
            "suspect_wallet": "0xabc",
            "chain": "ethereum",
            "vasp_matches": [
                {
                    "entity_name": "Binance",
                    "confidence_score": 1.0,
                    "direction": "INCOMING",
                }
            ],
        },
        baseline,
    )

    assert no_vasp["risk_score"] == with_vasp["risk_score"]
    assert no_vasp["behavioral_score"] == with_vasp["behavioral_score"]
    assert no_vasp["ml_score"] == with_vasp["ml_score"]
    assert no_vasp["graph_score"] == with_vasp["graph_score"]