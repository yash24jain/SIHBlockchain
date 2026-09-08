from src.live_feature_adapter import build_live_features


WALLET = "0xabc"


def test_internal_eth_is_excluded_from_ml_eth_totals():
    transactions = [
        {
            "tx_hash": "0x1",
            "from": "0xsender",
            "to": WALLET,
            "amount": 10.0,
            "token": "ETH",
            "timestamp": 1000,
            "transaction_type": "normal",
        },
        {
            "tx_hash": "0x2",
            "from": WALLET,
            "to": "0xreceiver",
            "amount": 7.0,
            "token": "ETH",
            "timestamp": 2000,
            "transaction_type": "normal",
        },
        {
            "tx_hash": "0x3",
            "from": WALLET,
            "to": "0xinternal",
            "amount": 1000.0,
            "token": "ETH",
            "timestamp": 3000,
            "transaction_type": "internal",
        },
    ]

    features = build_live_features(
        transactions,
        WALLET,
    )

    assert features["total_eth_received"] == 10.0
    assert features["total_eth_sent"] == 7.0
    assert features["eth_balance"] == 3.0

    assert features["internal_eth_sent"] == 1000.0