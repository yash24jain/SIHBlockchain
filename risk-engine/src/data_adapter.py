import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://api.etherscan.io/v2/api"


def call_etherscan(params):
    """Make a request to Etherscan V2 API."""

    if not API_KEY:
        raise ValueError("ETHERSCAN_API_KEY not found in .env")

    params["apikey"] = API_KEY

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data


def get_normal_transactions(wallet_address, page=1, offset=100):
    """Get normal ETH transactions."""

    params = {
        "chainid": "1",
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": page,
        "offset": offset,
        "sort": "asc"
    }

    data = call_etherscan(params)

    if data.get("status") != "1":
        # An address with no transactions can return status 0.
        if data.get("result") == "No transactions found":
            return []

        raise RuntimeError(
            f"Etherscan error: {data.get('message')} - "
            f"{data.get('result')}"
        )

    return data["result"]


def get_token_transfers(wallet_address, page=1, offset=100):
    """Get ERC-20 token transfers."""

    params = {
        "chainid": "1",
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": page,
        "offset": offset,
        "sort": "asc"
    }

    data = call_etherscan(params)

    if data.get("status") != "1":
        if data.get("result") == "No transactions found":
            return []

        raise RuntimeError(
            f"Etherscan error: {data.get('message')} - "
            f"{data.get('result')}"
        )

    return data["result"]


def get_internal_transactions(wallet_address, page=1, offset=100):
    """Get internal Ethereum transactions."""

    params = {
        "chainid": "1",
        "module": "account",
        "action": "txlistinternal",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": page,
        "offset": offset,
        "sort": "asc"
    }

    data = call_etherscan(params)

    if data.get("status") != "1":
        if data.get("result") == "No transactions found":
            return []

        raise RuntimeError(
            f"Etherscan error: {data.get('message')} - "
            f"{data.get('result')}"
        )

    return data["result"]


def normalize_normal_transaction(tx):
    """Normalize a normal ETH transaction."""

    value_eth = int(tx["value"]) / 10**18

    return {
        "tx_hash": tx["hash"],
        "from": tx["from"],
        "to": tx["to"],
        "amount": value_eth,
        "token": "ETH",
        "timestamp": int(tx["timeStamp"]),
        "block_number": int(tx["blockNumber"]),
        "chain": "ethereum",
        "transaction_type": "normal"
    }


def normalize_token_transfer(tx):
    """Normalize an ERC-20 token transfer."""

    decimals = int(tx.get("tokenDecimal", 18))

    raw_value = int(tx["value"])

    amount = raw_value / (10 ** decimals)

    return {
        "tx_hash": tx["hash"],
        "from": tx["from"],
        "to": tx["to"],
        "amount": amount,
        "token": tx.get("tokenSymbol", "UNKNOWN"),
        "timestamp": int(tx["timeStamp"]),
        "block_number": int(tx["blockNumber"]),
        "chain": "ethereum",
        "transaction_type": "erc20"
    }


def normalize_internal_transaction(tx):
    """Normalize an internal ETH transaction."""

    value_eth = int(tx["value"]) / 10**18

    return {
        "tx_hash": tx["hash"],
        "from": tx["from"],
        "to": tx["to"],
        "amount": value_eth,
        "token": "ETH",
        "timestamp": int(tx["timeStamp"]),
        "block_number": int(tx["blockNumber"]),
        "chain": "ethereum",
        "transaction_type": "internal"
    }


def get_wallet_data(wallet_address, offset=100):
    """
    Collect and normalize all currently supported
    Ethereum activity for a wallet.
    """

    normal = get_normal_transactions(
        wallet_address,
        offset=offset
    )

    token = get_token_transfers(
        wallet_address,
        offset=offset
    )

    internal = get_internal_transactions(
        wallet_address,
        offset=offset
    )

    transactions = []

    transactions.extend(
        normalize_normal_transaction(tx)
        for tx in normal
    )

    transactions.extend(
        normalize_token_transfer(tx)
        for tx in token
    )

    transactions.extend(
        normalize_internal_transaction(tx)
        for tx in internal
    )

    # Sort everything chronologically.
    transactions.sort(
        key=lambda tx: tx["timestamp"]
    )

    return transactions