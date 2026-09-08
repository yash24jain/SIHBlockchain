import pandas as pd

from src.behavioral_baseline import (
    build_behavioral_baseline
)


DATASET_PATH = (
    "data/transaction_dataset.csv"
)

BASELINE_PATH = (
    "data/behavioral_baseline.json"
)


def main():

    print(
        "Loading training dataset..."
    )

    df = pd.read_csv(
        DATASET_PATH
    )

    print(
        f"Loaded {len(df)} rows."
    )

    baseline = build_behavioral_baseline(
        df,
        output_path=BASELINE_PATH
    )

    print(
        "Behavioral baseline created for "
        f"{len(baseline['feature_stats'])} "
        "features."
    )

    print(
        "Saved to: "
        f"{BASELINE_PATH}"
    )


if __name__ == "__main__":
    main()