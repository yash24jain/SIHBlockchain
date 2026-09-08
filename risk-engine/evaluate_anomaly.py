import pandas as pd
import joblib

from src.ml_dataset_loader import prepare_ml_dataset


# ==========================================
# Load dataset
# ==========================================

df = pd.read_csv(
    "data/transaction_dataset.csv"
)

X, labels, addresses = prepare_ml_dataset(df)


# ==========================================
# Load model
# ==========================================

model = joblib.load(
    "data/anomaly_model.pkl"
)


# ==========================================
# Get anomaly scores
# ==========================================

scores = model.decision_function(X)


# Lower score = more anomalous


results = pd.DataFrame({
    "address": addresses,
    "label": labels,
    "anomaly_score": scores
})


# ==========================================
# Sort by most anomalous
# ==========================================

results = results.sort_values(
    "anomaly_score"
)


print("\n===== MOST ANOMALOUS WALLETS =====")

print(
    results.head(20).to_string(
        index=False
    )
)


# ==========================================
# Overall statistics
# ==========================================

print("\n===== SCORE STATISTICS =====")

print(
    results["anomaly_score"].describe()
)


# ==========================================
# Fraud rate by anomaly ranking
# ==========================================

for percentage in [1, 5, 10]:

    count = int(
        len(results) * percentage / 100
    )

    top_wallets = results.head(count)

    frauds = (
        top_wallets["label"] == 1
    ).sum()

    precision = frauds / count

    print(
        f"\nTop {percentage}% most anomalous:"
    )

    print(
        f"Wallets: {count}"
    )

    print(
        f"Fraud wallets: {frauds}"
    )

    print(
        f"Precision: {precision:.2%}"
    )