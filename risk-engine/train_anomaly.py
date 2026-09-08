from src.ml_dataset_loader import (
    load_dataset,
    prepare_ml_dataset
)

from src.ml_anomaly import train_model
import joblib


# ==========================================
# 1. Load real Ethereum dataset
# ==========================================

df = load_dataset(
    "data/transaction_dataset.csv"
)

print("\n===== REAL ETHEREUM DATASET =====")

print(
    f"Total wallets: {len(df)}"
)


# ==========================================
# 2. Convert to our ML features
# ==========================================

X, labels, addresses = prepare_ml_dataset(
    df
)

print(
    f"ML feature count: {X.shape[1]}"
)

print(
    f"Training samples: {X.shape[0]}"
)


# ==========================================
# 3. Train Isolation Forest
# ==========================================

# ==========================================
# Train ONLY on legitimate wallets
# ==========================================

legitimate_mask = labels == 0

X_legitimate = X[legitimate_mask]

print(
    f"Legitimate wallets used for training: "
    f"{len(X_legitimate)}"
)

print(
    f"Fraudulent wallets excluded from training: "
    f"{(labels == 1).sum()}"
)


model = train_model(
    X_legitimate.to_dict("records")
)
joblib.dump(
    model,
    "data/anomaly_model.pkl"
)

print("Model saved to data/anomaly_model.pkl")

print("\n===== MODEL TRAINED =====")

print("Isolation Forest training complete.")