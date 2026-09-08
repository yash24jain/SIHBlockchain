import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)

from src.ml_dataset_loader import prepare_ml_dataset


DATASET_PATH = "data/transaction_dataset.csv"
MODEL_PATH = "data/fraud_model.pkl"


def train_fraud_model():

    print("Loading dataset...")

    df = pd.read_csv(DATASET_PATH)

    # --------------------------------------------------
    # PREPARE FEATURES
    # --------------------------------------------------

    X, y, addresses = prepare_ml_dataset(df)

    print(f"Total wallets: {len(df)}")
    print(f"Fraud wallets: {(y == 1).sum()}")
    print(f"Legitimate wallets: {(y == 0).sum()}")

    print("\nFeatures used:")
    for feature in X.columns:
        print(f"  - {feature}")

    # --------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print(f"\nTraining wallets: {len(X_train)}")
    print(f"Testing wallets: {len(X_test)}")

    # --------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------

    print("\nTraining Random Forest...")

    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------
    # PREDICTIONS
    # --------------------------------------------------

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    # --------------------------------------------------
    # EVALUATION
    # --------------------------------------------------

    print("\n===== FRAUD MODEL EVALUATION =====")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=[
                "LEGITIMATE",
                "FRAUD"
            ]
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities
    )

    print(f"\nROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC:  {pr_auc:.4f}")

    # --------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------

    print("\n===== FEATURE IMPORTANCE =====")

    importance = pd.Series(
        model.feature_importances_,
        index=X.columns
    ).sort_values(
        ascending=False
    )

    for feature, value in importance.items():

        print(
            f"{feature:<30} "
            f"{value:.6f}"
        )

    # --------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"\nModel saved to {MODEL_PATH}"
    )


if __name__ == "__main__":
    train_fraud_model()