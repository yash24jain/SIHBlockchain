import os

import joblib
import pandas as pd

from src.ml_dataset_loader import ML_FEATURE_MAP


MODEL_PATH = "data/fraud_model.pkl"


def build_feature_dataframe(features):

    feature_names = list(
        ML_FEATURE_MAP.keys()
    )

    data = {}

    for feature_name in feature_names:

        value = features.get(
            feature_name,
            0
        )

        try:

            value = float(value)

        except (
            TypeError,
            ValueError
        ):

            value = 0.0

        data[feature_name] = value

    return pd.DataFrame(
        [data],
        columns=feature_names
    )


def predict_fraud_probability(features):

    if not os.path.exists(MODEL_PATH):

        raise FileNotFoundError(
            f"Fraud model not found: {MODEL_PATH}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    X = build_feature_dataframe(
        features
    )

    probability = model.predict_proba(
        X
    )[0][1]

    prediction = model.predict(
        X
    )[0]

    return {

        "fraud_probability": round(
            float(probability),
            4
        ),

        "prediction":
            "FRAUD"
            if prediction == 1
            else "LEGITIMATE"
    }