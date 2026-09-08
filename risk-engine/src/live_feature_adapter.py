from datetime import datetime
from typing import Any, Dict, List


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_timestamp(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _normalize_address(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _is_eth_transaction(tx: Dict[str, Any]) -> bool:
    token = str(tx.get("token", "")).strip().upper()
    return token in {"", "ETH"}


def _is_normal_eth_transaction(tx: Dict[str, Any]) -> bool:
    if not _is_eth_transaction(tx):
        return False

    tx_type = str(
        tx.get("transaction_type", "normal")
    ).strip().lower()

    return tx_type == "normal"


def _is_erc20_transaction(tx: Dict[str, Any]) -> bool:
    tx_type = str(
        tx.get("transaction_type", "")
    ).strip().lower()

    token = str(
        tx.get("token", "")
    ).strip().upper()

    return (
        tx_type == "erc20"
        or (
            token not in {"", "ETH"}
            and tx_type != "internal"
        )
    )


def _minutes_between(first_timestamp: int, last_timestamp: int) -> float:
    if first_timestamp <= 0 or last_timestamp <= 0:
        return 0.0

    if last_timestamp < first_timestamp:
        return 0.0

    return (last_timestamp - first_timestamp) / 60.0


def _average_gap(timestamps: List[int]) -> float:
    valid = sorted(
        ts for ts in timestamps
        if ts > 0
    )

    if len(valid) < 2:
        return 0.0

    gaps = [
        valid[i] - valid[i - 1]
        for i in range(1, len(valid))
    ]

    return sum(gaps) / len(gaps)


def _count_rapid_transfers(
    timestamps: List[int],
    threshold_seconds: int = 600
) -> int:
    valid = sorted(
        ts for ts in timestamps
        if ts > 0
    )

    if len(valid) < 2:
        return 0

    return sum(
        1
        for i in range(1, len(valid))
        if 0 <= valid[i] - valid[i - 1] <= threshold_seconds
    )


def _burst_ratio(
    timestamps: List[int],
    threshold_seconds: int = 600
) -> float:
    if len(timestamps) < 2:
        return 0.0

    rapid = _count_rapid_transfers(
        timestamps,
        threshold_seconds
    )

    return rapid / max(len(timestamps) - 1, 1)


def extract_wallet_features(
    transactions: List[Dict[str, Any]],
    wallet_address: str
) -> Dict[str, Any]:

    wallet = _normalize_address(wallet_address)

    incoming = []
    outgoing = []
    normal_eth_incoming = []
    normal_eth_outgoing = []
    erc20_transactions = []

    senders = set()
    receivers = set()

    outgoing_timestamps = []
    incoming_timestamps = []

    created_contracts = 0

    for tx in transactions:

        tx_from = _normalize_address(tx.get("from"))
        tx_to = _normalize_address(tx.get("to"))

        if tx_from != wallet and tx_to != wallet:
            continue

        amount = _safe_float(
            tx.get("amount"),
            0.0
        )

        timestamp = _safe_timestamp(
            tx.get("timestamp")
        )

        is_incoming = tx_to == wallet
        is_outgoing = tx_from == wallet

        if is_incoming:
            incoming.append(tx)

            if tx_from:
                senders.add(tx_from)

            if timestamp:
                incoming_timestamps.append(timestamp)

        if is_outgoing:
            outgoing.append(tx)

            if tx_to:
                receivers.add(tx_to)

            if timestamp:
                outgoing_timestamps.append(timestamp)

        # ------------------------------------------
        # Normal ETH transactions
        # ------------------------------------------

        if _is_normal_eth_transaction(tx):

            if is_incoming:
                normal_eth_incoming.append(tx)

            if is_outgoing:
                normal_eth_outgoing.append(tx)

            # Contract creation
            if (
                is_outgoing
                and not tx_to
            ):
                created_contracts += 1

        # ------------------------------------------
        # ERC20 transactions
        # ------------------------------------------

        if _is_erc20_transaction(tx):
            erc20_transactions.append(tx)

    # ----------------------------------------------
    # ETH values used for ML-compatible features
    # ----------------------------------------------

    total_eth_sent = sum(
        _safe_float(tx.get("amount"))
        for tx in normal_eth_outgoing
    )

    total_eth_received = sum(
        _safe_float(tx.get("amount"))
        for tx in normal_eth_incoming
    )

    eth_balance = (
        total_eth_received
        - total_eth_sent
    )

    # ----------------------------------------------
    # ERC20 counterparties
    # ----------------------------------------------

    erc20_senders = set()
    erc20_receivers = set()

    for tx in erc20_transactions:

        tx_from = _normalize_address(
            tx.get("from")
        )

        tx_to = _normalize_address(
            tx.get("to")
        )

        if tx_to == wallet and tx_from:
            erc20_senders.add(tx_from)

        if tx_from == wallet and tx_to:
            erc20_receivers.add(tx_to)

    # ----------------------------------------------
    # Time information
    # ----------------------------------------------

    all_timestamps = [
        _safe_timestamp(tx.get("timestamp"))
        for tx in incoming + outgoing
    ]

    valid_timestamps = sorted(
        ts for ts in all_timestamps
        if ts > 0
    )

    time_active_minutes = 0.0

    if len(valid_timestamps) >= 2:
        time_active_minutes = _minutes_between(
            valid_timestamps[0],
            valid_timestamps[-1]
        )

    avg_time_between_sent = _average_gap(
        outgoing_timestamps
    )

    avg_time_between_received = _average_gap(
        incoming_timestamps
    )

    rapid_outgoing_count = _count_rapid_transfers(
        outgoing_timestamps
    )

    rapid_incoming_count = _count_rapid_transfers(
        incoming_timestamps
    )

    outgoing_burst_ratio = _burst_ratio(
        outgoing_timestamps
    )

    incoming_burst_ratio = _burst_ratio(
        incoming_timestamps
    )

    # ----------------------------------------------
    # Internal transfer information
    #
    # These are deliberately kept separate from
    # ML-compatible ETH totals.
    # ----------------------------------------------

    internal_eth_sent = sum(
        _safe_float(tx.get("amount"))
        for tx in outgoing
        if (
            str(
                tx.get("transaction_type", "")
            ).strip().lower()
            == "internal"
            and _is_eth_transaction(tx)
        )
    )

    internal_eth_received = sum(
        _safe_float(tx.get("amount"))
        for tx in incoming
        if (
            str(
                tx.get("transaction_type", "")
            ).strip().lower()
            == "internal"
            and _is_eth_transaction(tx)
        )
    )

    return {
        "transaction_count": len(incoming) + len(outgoing),

        "incoming_count": len(incoming),

        "outgoing_count": len(outgoing),

        "unique_senders": len(senders),

        "unique_receivers": len(receivers),

        "created_contracts": created_contracts,

        "time_active_minutes": time_active_minutes,

        "avg_time_between_sent": avg_time_between_sent,

        "avg_time_between_received": avg_time_between_received,

        "rapid_outgoing_count": rapid_outgoing_count,

        "rapid_incoming_count": rapid_incoming_count,

        "outgoing_burst_ratio": outgoing_burst_ratio,

        "incoming_burst_ratio": incoming_burst_ratio,

        "total_eth_sent": total_eth_sent,

        "total_eth_received": total_eth_received,

        "eth_balance": eth_balance,

        "erc20_transactions": len(
            erc20_transactions
        ),

        "erc20_unique_senders": len(
            erc20_senders
        ),

        "erc20_unique_receivers": len(
            erc20_receivers
        ),

        # Descriptive fields, not ML model inputs.
        "internal_eth_sent": internal_eth_sent,

        "internal_eth_received": internal_eth_received,
    }


def build_live_features(
    transactions: List[Dict[str, Any]],
    wallet_address: str
) -> Dict[str, Any]:

    return extract_wallet_features(
        transactions,
        wallet_address
    )