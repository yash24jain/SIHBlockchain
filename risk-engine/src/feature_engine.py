import json
from collections import Counter


def load_transactions(file_path="data/transactions.json"):
    """Load normalized blockchain transactions."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_features(transactions, wallet_address):

    wallet = wallet_address.lower()

    incoming = []
    outgoing = []

    senders = set()
    receivers = set()

    token_counts = Counter()
    type_counts = Counter()

    # --------------------------------
    # Separate incoming / outgoing
    # --------------------------------

    for tx in transactions:

        sender = tx["from"].lower()
        receiver = tx["to"].lower() if tx["to"] else ""

        if receiver == wallet:
            incoming.append(tx)

            if sender:
                senders.add(sender)

        if sender == wallet:
            outgoing.append(tx)

            if receiver:
                receivers.add(receiver)

        token_counts[tx["token"]] += 1
        type_counts[tx["transaction_type"]] += 1

    # --------------------------------
    # Sort by timestamp
    # --------------------------------

    sorted_transactions = sorted(
        transactions,
        key=lambda tx: tx["timestamp"]
    )

    # --------------------------------
    # Time-based features
    # --------------------------------

    timestamps = [
        tx["timestamp"]
        for tx in sorted_transactions
    ]

    time_gaps = []

    for i in range(1, len(timestamps)):

        gap = timestamps[i] - timestamps[i - 1]

        if gap >= 0:
            time_gaps.append(gap)

    if time_gaps:

        average_time_gap = (
            sum(time_gaps) / len(time_gaps)
        )

        minimum_time_gap = min(time_gaps)

    else:

        average_time_gap = 0
        minimum_time_gap = 0

    # --------------------------------
    # Activity duration
    # --------------------------------

    if len(timestamps) >= 2:

        activity_duration = (
            timestamps[-1] - timestamps[0]
        )

    else:

        activity_duration = 0

    # --------------------------------
    # Transaction rate
    # --------------------------------

    if activity_duration > 0:

        transactions_per_hour = (
            len(transactions)
            / (activity_duration / 3600)
        )

    else:

        transactions_per_hour = 0

    # --------------------------------
    # Rapid transfers
    # --------------------------------

    rapid_transfer_count = sum(
        1
        for gap in time_gaps
        if gap <= 300
    )

    # --------------------------------
    # Burst detection
    # --------------------------------
    # Number of transactions occurring
    # within 10 minutes of another one.

    burst_count = sum(
        1
        for gap in time_gaps
        if gap <= 600
    )

    # --------------------------------
    # ETH totals
    # --------------------------------

    total_eth_received = sum(
        tx["amount"]
        for tx in incoming
        if tx["token"] == "ETH"
        and tx["transaction_type"] != "internal"
    )

    total_eth_sent = sum(
        tx["amount"]
        for tx in outgoing
        if tx["token"] == "ETH"
        and tx["transaction_type"] != "internal"
    )

    # --------------------------------
    # Incoming / outgoing ratio
    # --------------------------------

    total_directional = (
        len(incoming) + len(outgoing)
    )

    if total_directional > 0:

        incoming_ratio = (
            len(incoming) / total_directional
        )

        outgoing_ratio = (
            len(outgoing) / total_directional
        )

    else:

        incoming_ratio = 0
        outgoing_ratio = 0

    # --------------------------------
    # Forwarding behavior
    # --------------------------------

    forwarding_count = 0

    for received_tx in incoming:

        received_time = received_tx["timestamp"]

        for sent_tx in outgoing:

            sent_time = sent_tx["timestamp"]

            if 0 <= sent_time - received_time <= 3600:

                forwarding_count += 1
                break

    if len(incoming) > 0:

        forwarding_ratio = (
            forwarding_count / len(incoming)
        )

    else:

        forwarding_ratio = 0

    # --------------------------------
    # Build features
    # --------------------------------

    features = {

        # Basic activity
        "transaction_count":
            len(transactions),

        "incoming_count":
            len(incoming),

        "outgoing_count":
            len(outgoing),

        # Counterparties
        "unique_senders":
            len(senders),

        "unique_receivers":
            len(receivers),

        "unique_counterparties":
            len(senders | receivers),

        # ETH movement
        "total_eth_received":
            total_eth_received,

        "total_eth_sent":
            total_eth_sent,

        # Transaction types
        "normal_transaction_count":
            type_counts["normal"],

        "erc20_transfer_count":
            type_counts["erc20"],

        "internal_transaction_count":
            type_counts["internal"],

        # Tokens
        "token_counts":
            dict(token_counts),

        # Time behavior
        "activity_duration_seconds":
            activity_duration,

        "average_time_gap_seconds":
            round(average_time_gap, 2),

        "minimum_time_gap_seconds":
            minimum_time_gap,

        # Activity intensity
        "transactions_per_hour":
            round(transactions_per_hour, 3),

        "rapid_transfer_count":
            rapid_transfer_count,

        "burst_count":
            burst_count,

        # Direction
        "incoming_ratio":
            round(incoming_ratio, 3),

        "outgoing_ratio":
            round(outgoing_ratio, 3),

        # Forwarding
        "forwarding_count":
            forwarding_count,

        "forwarding_ratio":
            round(forwarding_ratio, 3)
    }

    return features


def save_features(
    features,
    file_path="data/features.json"
):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            features,
            file,
            indent=4
        )