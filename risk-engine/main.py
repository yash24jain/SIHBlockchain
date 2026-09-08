import json
from pathlib import Path

from src.live_feature_adapter import build_live_features
from src.fraud_predictor import predict_fraud_probability
from src.graph_adapter import load_graph_output
from src.vasp_adapter import get_vasp_evidence
from src.risk_engine import calculate_risk


WALLET_ADDRESS = (
    "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"
)

TRANSACTIONS_PATH = Path(
    "data/transactions.json"
)

GRAPH_OUTPUT_PATH = Path(
    "data/graph_output.json"
)

VASP_OUTPUT_PATH = Path(
    "data/vasp_output.json"
)

RISK_OUTPUT_PATH = Path(
    "data/risk_result.json"
)


def load_transactions(path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def main():

    print("=" * 70)
    print("STUDENT 4 - AI/ML + RISK ENGINE")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Transactions
    # ---------------------------------------------------------

    print("\n[1/5] Loading transactions...")

    transactions = load_transactions(
        TRANSACTIONS_PATH
    )

    print(
        f"Loaded {len(transactions)} transactions"
    )

    # ---------------------------------------------------------
    # 2. Live features
    # ---------------------------------------------------------

    print("\n[2/5] Building wallet features...")

    wallet_features = build_live_features(
        transactions,
        WALLET_ADDRESS,
    )

    print(
        f"Transactions       : "
        f"{wallet_features.get('transaction_count', 0)}"
    )

    print(
        f"Incoming           : "
        f"{wallet_features.get('incoming_count', 0)}"
    )

    print(
        f"Outgoing           : "
        f"{wallet_features.get('outgoing_count', 0)}"
    )

    print(
        f"Unique senders     : "
        f"{wallet_features.get('unique_senders', 0)}"
    )

    print(
        f"Unique receivers   : "
        f"{wallet_features.get('unique_receivers', 0)}"
    )

    print(
        f"ERC20 transactions : "
        f"{wallet_features.get('erc20_transactions', 0)}"
    )

    # ---------------------------------------------------------
    # 3. ML
    # ---------------------------------------------------------

    print("\n[3/5] Running ML fraud model...")

    ml_result = predict_fraud_probability(
        wallet_features
    )

    fraud_probability = float(
        ml_result.get(
            "fraud_probability",
            0.0,
        )
    )

    ml_score = fraud_probability * 100.0

    print(
        f"Fraud probability : "
        f"{fraud_probability:.4f}"
    )

    print(
        f"ML score          : "
        f"{ml_score:.2f}"
    )

    print(
        f"Prediction        : "
        f"{ml_result.get('prediction', 'UNKNOWN')}"
    )

    # ---------------------------------------------------------
    # 4. Graph
    # ---------------------------------------------------------

    print("\n[4/5] Loading graph analysis...")

    graph_result = load_graph_output(
        GRAPH_OUTPUT_PATH,
        WALLET_ADDRESS,
    )

    graph_features = graph_result.get(
        "features",
        {},
    )

    print(
        f"Wallet count      : "
        f"{graph_features.get('wallet_count', 0):g}"
    )

    print(
        f"Graph transactions: "
        f"{graph_features.get('transaction_count', 0):g}"
    )

    print(
        f"Destinations      : "
        f"{graph_features.get('destination_count', 0):g}"
    )

    print(
        f"Path count        : "
        f"{graph_features.get('path_count', 0):g}"
    )

    if "graph_score" in graph_result:

        print(
            f"Graph score       : "
            f"{float(graph_result['graph_score']):.2f}"
        )

    else:

        print(
            "Graph score       : "
            "compatibility scoring"
        )

    # ---------------------------------------------------------
    # 5. VASP
    # ---------------------------------------------------------

    print("\n[5/5] Loading VASP attribution...")

    vasp_result = get_vasp_evidence(
        WALLET_ADDRESS,
        VASP_OUTPUT_PATH,
    )

    vasp_matches = vasp_result.get(
        "vasp_matches",
        [],
    )

    print(
        f"VASP matches      : "
        f"{len(vasp_matches)}"
    )

    # ---------------------------------------------------------
    # Final risk
    # ---------------------------------------------------------

    print("\nCalculating final risk...")

    risk_result = calculate_risk(
        wallet_features=wallet_features,
        ml_result={
            **ml_result,
            "ml_score": ml_score,
        },
        graph_result=graph_result,
        vasp_result=vasp_result,
    )

    # ---------------------------------------------------------
    # Save result
    # ---------------------------------------------------------

    with open(
        RISK_OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            risk_result,
            f,
            indent=2,
        )

    # ---------------------------------------------------------
    # Final presentation
    # ---------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("FINAL INVESTIGATION RESULT")
    print("=" * 70)

    print(
        f"Wallet       : "
        f"{WALLET_ADDRESS}"
    )

    print(
        f"Behavioral   : "
        f"{risk_result['behavioral_score']:.2f}"
    )

    print(
        f"ML           : "
        f"{risk_result['ml_score']:.2f}"
    )

    print(
        f"Graph        : "
        f"{risk_result['graph_score']:.2f}"
    )

    print("-" * 70)

    print(
        f"FINAL RISK   : "
        f"{risk_result['risk_score']:.2f}"
    )

    print(
        f"RISK LEVEL   : "
        f"{risk_result['risk_level']}"
    )

    print("\nInvestigation Signals:")

    for reason in risk_result.get(
        "reasons",
        [],
    ):
        print(f"  - {reason}")

    print("\nVASP Attribution:")

    if vasp_matches:

        for match in vasp_matches:

            confidence = float(
                match.get(
                    "confidence_score",
                    0.0,
                )
            )

            print(
                f"  - Entity       : "
                f"{match.get('entity_name', 'Unknown')}"
            )

            print(
                f"    Category     : "
                f"{match.get('vasp_category', 'Unknown')}"
            )

            print(
                f"    Confidence   : "
                f"{confidence * 100:.2f}%"
            )

            print(
                f"    Status       : "
                f"{match.get('match_status', 'Unknown')}"
            )

            print(
                f"    Interactions : "
                f"{match.get('interaction_count', 0)}"
            )

            print(
                f"    Hop distance : "
                f"{match.get('hop_distance', 0)}"
            )

            print(
                f"    Source       : "
                f"{match.get('source', 'Unknown')}"
            )

    else:

        print(
            "  - No VASP attribution found."
        )

    print("\n" + "=" * 70)

    print(
        f"Risk result saved to: "
        f"{RISK_OUTPUT_PATH.resolve()}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()