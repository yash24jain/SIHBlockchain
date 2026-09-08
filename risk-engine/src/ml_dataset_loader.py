import pandas as pd


# IMPORTANT:
# These features MUST remain aligned with the features
# used when fraud_model.pkl was trained.

ML_FEATURE_MAP = {

    "transaction_count":
        "total transactions (including tnx to create contract",

    "incoming_count":
        "Received Tnx",

    "outgoing_count":
        "Sent tnx",

    "unique_senders":
        "Unique Received From Addresses",

    "unique_receivers":
        "Unique Sent To Addresses",

    "created_contracts":
        "Number of Created Contracts",

    "time_active_minutes":
        "Time Diff between first and last (Mins)",

    "avg_time_between_sent":
        "Avg min between sent tnx",

    "avg_time_between_received":
        "Avg min between received tnx",

    "total_eth_sent":
        "total Ether sent",

    "total_eth_received":
        "total ether received",

    "eth_balance":
        "total ether balance",

    "erc20_transactions":
        " Total ERC20 tnxs",

    "erc20_unique_senders":
        " ERC20 uniq sent addr",

    "erc20_unique_receivers":
        " ERC20 uniq rec addr"
}


def load_dataset(file_path):

    return pd.read_csv(file_path)


def prepare_ml_dataset(df):

    result = pd.DataFrame()

    for our_name, dataset_column in ML_FEATURE_MAP.items():

        result[our_name] = pd.to_numeric(
            df[dataset_column],
            errors="coerce"
        )

    result = result.fillna(0)

    labels = df["FLAG"].astype(int)

    addresses = df["Address"]

    return result, labels, addresses