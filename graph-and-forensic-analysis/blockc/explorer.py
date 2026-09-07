import json
from blockc.blockchain_api import get_clean_blockchain_data, is_contract_address
from blockc.data_exporter import export_blockchain_data

# Known entity database (Centralized Exchanges & Routers)
KNOWN_VASP = {
    "0xbf2179859fc6d5bee9bf9158632dc51678a4100e": "Binance 14 Deposit Forwarder",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase 1",
    "0x503828976d22510aad0201ac7ec88293211d23dc": "Coinbase 2",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
}

# Normalize KNOWN_VASP keys to lowercase to prevent checksum mismatches
KNOWN_VASP = {str(k).lower().strip(): v for k, v in KNOWN_VASP.items()}


def resolve_metadata(address):
    """
    Dynamically resolve entity labels and types.
    """
    clean = str(address).lower().strip()
    if clean in KNOWN_VASP:
        label = KNOWN_VASP[clean]
        entity_type = "SMART_CONTRACT" if "Router" in label else "EXCHANGE_DEPOSIT"
        return {"entity_type": entity_type, "label": label}

    # Contract check via API
    try:
        if is_contract_address(clean):
            return {"entity_type": "SMART_CONTRACT", "label": "Contract Address"}
    except Exception:
        pass

    return {"entity_type": "EOA", "label": "Unlabeled"}


def explore_wallet(
    wallet,
    max_hops=3,
    max_wallets=50,
    branches_per_wallet=2
):
    wallet = str(wallet).lower().strip()

    visited = set()
    queue = [(wallet, 0)]

    all_transactions = []
    wallet_depths = {wallet: 0}
    wallets_metadata = {}

    while queue and len(visited) < max_wallets:
        current_wallet, depth = queue.pop(0)

        if current_wallet in visited:
            continue

        if depth > max_hops:
            continue

        print(f"Exploring: {current_wallet} (hop {depth})")

        visited.add(current_wallet)
        wallet_depths[current_wallet] = depth

        # Resolve classification metadata immediately
        wallets_metadata[current_wallet] = resolve_metadata(current_wallet)

        # Stop crawling deeper if an exchange deposit address is reached
        if wallets_metadata[current_wallet]["entity_type"] == "EXCHANGE_DEPOSIT":
            print(f"Terminal VASP reached: {current_wallet}. Stopping expansion on this branch.")
            continue

        # If a contract is reached that isn't the root wallet, don't try txlist (it yields no direct EOA sends)
        if depth > 0 and wallets_metadata[current_wallet]["entity_type"] == "SMART_CONTRACT":
            print(f"Contract reached at hop {depth}: {current_wallet}. Skipping expansion.")
            continue

        # ==================================================
        # FETCH TRANSACTIONS VIA BLOCKCHAIN API
        # ==================================================
        try:
            response = get_clean_blockchain_data(current_wallet)
            transactions = response.get("transactions", [])
        except Exception as e:
            print(f"Could not fetch {current_wallet}: {e}")
            continue

        # ==================================================
        # FIND VALID OUTGOING WALLET TRANSFERS
        # ==================================================
        outgoing = []

        for tx in transactions:
            sender = str(tx.get("from", "")).lower().strip()
            receiver = str(tx.get("to", "")).lower().strip()

            # Ensure case-insensitive sender comparison
            if sender != current_wallet:
                continue

            if not receiver or receiver == current_wallet:
                continue

            try:
                amount = float(tx.get("amount", 0) or 0)
            except (TypeError, ValueError):
                amount = 0.0

            # Filter out micro-dust (gas fees / spam)
            if amount < 0.001:
                continue

            transaction_type = str(tx.get("transaction_type", "")).upper()
            if transaction_type in ("NATIVE_TRANSFER", "ERC20_TRANSFER", ""):
                outgoing.append(tx)

        # ==================================================
        # SORT BY VALUE & SELECT TOP BRANCHES
        # Prioritizes native ETH capital flows, then sorts by volume
        # ==================================================
        outgoing.sort(
            key=lambda item: (
                1 if str(item.get("token_symbol", item.get("token", "ETH"))).upper() == "ETH" else 0,
                float(item.get("amount", 0) or 0)
            ),
            reverse=True
        )

        selected = outgoing[:branches_per_wallet]

        for tx in selected:
            all_transactions.append(tx)

        # Stop queueing deeper branches once max_hops is reached
        if depth == max_hops:
            continue

        # ==================================================
        # EXPAND TO NEXT WALLETS
        # ==================================================
        for tx in selected:
            next_wallet = str(tx.get("to", "")).lower().strip()

            if not next_wallet or next_wallet in visited:
                continue

            queued_wallets = [item[0] for item in queue]
            if next_wallet in queued_wallets:
                continue

            # Pre-resolve metadata for the next wallet so VASP flags register immediately
            if next_wallet not in wallets_metadata:
                wallets_metadata[next_wallet] = resolve_metadata(next_wallet)

            if len(visited) + len(queue) >= max_wallets:
                break

            queue.append((next_wallet, depth + 1))
            wallet_depths[next_wallet] = depth + 1

    # Ensure all remaining addresses have metadata
    for w in wallet_depths.keys():
        if w not in wallets_metadata:
            wallets_metadata[w] = resolve_metadata(w)

    # Also resolve metadata for all receivers in recorded transactions
    for tx in all_transactions:
        rec = str(tx.get("to", "")).lower().strip()
        if rec and rec not in wallets_metadata:
            wallets_metadata[rec] = resolve_metadata(rec)

    # ==================================================
    # PACKAGE PAYLOAD AND EXPORT
    # ==================================================
    final_payload = {
        "wallet": wallet,
        "chain": "ethereum",
        "wallets_metadata": wallets_metadata,
        "transactions": all_transactions
    }

    export_blockchain_data(final_payload, "data/blockchain_data.json")

    return final_payload