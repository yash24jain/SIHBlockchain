import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


# These are the numerical behavioral features
# currently available to our ML model.

ML_FEATURES = [
    "transaction_count",
    "incoming_count",
    "outgoing_count",
    "unique_senders",
    "unique_receivers",
    "created_contracts",
    "time_active_minutes",
    "avg_time_between_sent",
    "avg_time_between_received",
    "total_eth_sent",
    "total_eth_received",
    "eth_balance",
    "erc20_transactions",
    "erc20_unique_senders",
    "erc20_unique_receivers"
]


def build_feature_vector(features):
    """
    Convert our feature dictionary into a numerical
    vector that can be given to the ML model.
    """

    vector = []

    for feature_name in ML_FEATURES:

        value = features.get(
            feature_name,
            0
        )

        vector.append(float(value))

    return np.array(vector).reshape(1, -1)


def train_model(training_data):
    X = []

    for features in training_data:
        vector = [float(features.get(name, 0)) for name in ML_FEATURES]
        X.append(vector)

    X = pd.DataFrame(X, columns=ML_FEATURES)

    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42
    )

    model.fit(X)

    return model


def analyze_anomaly(model, features):
    """
    Analyze one wallet using the trained model.
    """

    vector = build_feature_vector(features)

    prediction = model.predict(vector)[0]

    raw_score = model.decision_function(vector)[0]

    # Isolation Forest:
    # +1 = normal
    # -1 = anomaly

    if prediction == -1:
        classification = "ANOMALOUS"
    else:
        classification = "NORMAL"

    return {
        "classification": classification,
        "raw_anomaly_score": round(
            float(raw_score),
            4
        )
    }