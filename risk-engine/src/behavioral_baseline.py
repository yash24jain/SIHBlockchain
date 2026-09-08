import json

from src.ml_dataset_loader import (
    ML_FEATURE_MAP,
    prepare_ml_dataset
)


BASELINE_PATH = "data/behavioral_baseline.json"


# =========================================================
# FEATURES USED BY THE INDEPENDENT BEHAVIORAL ENGINE
# =========================================================

BEHAVIORAL_FEATURES = {

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

    "erc20_unique_receivers"
}


# Both unusually high and unusually low values
# can be interesting for these features.

TWO_SIDED_FEATURES = {
    "eth_balance"
}


def build_behavioral_baseline(
    df,
    output_path=BASELINE_PATH
):

    ml_features, labels, addresses = (
        prepare_ml_dataset(df)
    )

    # -----------------------------------------------------
    # Legitimate wallets establish our normal population.
    # -----------------------------------------------------

    legitimate = ml_features[
        labels == 0
    ].copy()

    feature_stats = {}

    for feature_name in ML_FEATURE_MAP.keys():

        if feature_name not in BEHAVIORAL_FEATURES:
            continue

        if feature_name not in legitimate.columns:
            continue

        series = legitimate[
            feature_name
        ].astype(float)

        feature_stats[
            feature_name
        ] = {

            "min":
                float(series.min()),

            "q25":
                float(series.quantile(0.25)),

            "median":
                float(series.quantile(0.50)),

            "q75":
                float(series.quantile(0.75)),

            "q90":
                float(series.quantile(0.90)),

            "q95":
                float(series.quantile(0.95)),

            "q99":
                float(series.quantile(0.99)),

            "max":
                float(series.max())
        }

    baseline = {

        "feature_stats":
            feature_stats,

        "population": {

            "total_wallets":
                int(len(ml_features)),

            "legitimate_wallets":
                int(len(legitimate)),

            "fraud_wallets":
                int(labels.sum())
        }
    }

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            baseline,
            file,
            indent=2
        )

    return baseline


def load_behavioral_baseline(
    path=BASELINE_PATH
):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {
            "feature_stats": {}
        }


def _empirical_percentile(
    value,
    stats
):

    q25 = stats["q25"]
    q50 = stats["median"]
    q75 = stats["q75"]
    q90 = stats["q90"]
    q95 = stats["q95"]
    q99 = stats["q99"]

    if value <= q25:
        return 25.0

    if value <= q50:

        ratio = (
            (value - q25)
            / max(q50 - q25, 1e-9)
        )

        return 25.0 + ratio * 25.0

    if value <= q75:

        ratio = (
            (value - q50)
            / max(q75 - q50, 1e-9)
        )

        return 50.0 + ratio * 25.0

    if value <= q90:

        ratio = (
            (value - q75)
            / max(q90 - q75, 1e-9)
        )

        return 75.0 + ratio * 15.0

    if value <= q95:

        ratio = (
            (value - q90)
            / max(q95 - q90, 1e-9)
        )

        return 90.0 + ratio * 5.0

    if value <= q99:

        ratio = (
            (value - q95)
            / max(q99 - q95, 1e-9)
        )

        return 95.0 + ratio * 4.0

    return 99.5


def score_feature(
    value,
    stats,
    two_sided=False
):

    percentile = _empirical_percentile(
        value,
        stats
    )

    if two_sided:

        deviation = max(
            percentile,
            100.0 - percentile
        )

    else:

        deviation = percentile

    if deviation >= 99:

        score = 100

    elif deviation >= 95:

        score = 85

    elif deviation >= 90:

        score = 70

    elif deviation >= 75:

        score = 45

    elif deviation >= 50:

        score = 20

    else:

        score = 5

    return {

        "value":
            float(value),

        "percentile":
            round(
                float(percentile),
                2
            ),

        "deviation":
            round(
                float(deviation),
                2
            ),

        "score":
            float(score)
    }


def calculate_behavioral_score(
    wallet_features,
    baseline
):

    feature_stats = baseline.get(
        "feature_stats",
        {}
    )

    details = {}

    scores = []

    reasons = []

    for feature_name, stats in feature_stats.items():

        value = wallet_features.get(
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

        result = score_feature(
            value,
            stats,
            two_sided=(
                feature_name
                in TWO_SIDED_FEATURES
            )
        )

        details[
            feature_name
        ] = result

        scores.append(
            result["score"]
        )

        if result["deviation"] >= 90:

            reasons.append({

                "feature":
                    feature_name,

                "score":
                    result["score"],

                "percentile":
                    result["percentile"],

                "message":
                    (
                        f"{feature_name} is "
                        f"unusually high/deviant "
                        f"({result['percentile']:.1f}"
                        f"th percentile)"
                    )
            })

    if scores:

        behavioral_score = (
            sum(scores)
            / len(scores)
        )

    else:

        behavioral_score = 0.0

    reasons.sort(
        key=lambda item:
            item["percentile"],
        reverse=True
    )

    return (
        round(
            float(behavioral_score),
            2
        ),
        details,
        reasons[:5]
    )