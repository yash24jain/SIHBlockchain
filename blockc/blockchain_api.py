import requests
import time

from datetime import datetime, timezone

from blockc.config import (
    API_KEY,
    BASE_URL,
    CHAIN_ID,
    PAGE_SIZE,
    MAX_PAGES_PER_RANGE,
    MAX_RESULTS_PER_RANGE,
    MIN_BLOCK_RANGE,
    TEST_MODE,
    TEST_RECORD_LIMIT,
    REQUEST_TIMEOUT,
    MAX_API_RETRIES,
    RETRY_DELAY,
    RATE_LIMIT_DELAY,
    REQUEST_DELAY,
    CONTRACT_CACHE_ENABLED,
)


# ============================================================
# GLOBAL CONTRACT CACHE
# ============================================================

contract_cache = {}


# ============================================================
# ADDRESS UTILITIES
# ============================================================

def normalize_address(address):
    """
    Normalize an Ethereum address to lowercase.
    """

    if not address:
        return ""

    return address.strip().lower()


def is_valid_wallet_address(address):
    """
    Validate basic Ethereum wallet address format.
    """

    if not isinstance(address, str):
        return False

    address = address.strip()

    if len(address) != 42:
        return False

    if not address.startswith("0x"):
        return False

    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


# ============================================================
# TIMESTAMP CONVERSION
# ============================================================

def convert_timestamp(timestamp):
    """
    Convert Unix timestamp to UTC ISO-8601 format.

    Example:
        1591798219
        ->
        2020-06-10T14:10:19+00:00
    """

    try:

        timestamp = int(timestamp)

        return datetime.fromtimestamp(
            timestamp,
            timezone.utc
        ).isoformat()

    except (ValueError, TypeError, OSError):

        return None


# ============================================================
# API REQUEST
# ============================================================

def make_api_request(params):
    """
    Send a request to the Etherscan V2 API.

    Handles:
    - API key
    - Chain ID
    - Timeout
    - HTTP 429 rate limiting
    - API-level rate limiting
    - Retries
    - Invalid JSON
    - Controlled request delay
    """

    if not API_KEY:

        print(
            "ERROR: ETHERSCAN_API_KEY environment variable "
            "is not set."
        )

        return None

    params = params.copy()

    params["apikey"] = API_KEY
    params["chainid"] = CHAIN_ID

    for attempt in range(
        1,
        MAX_API_RETRIES + 1
    ):

        try:

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            # --------------------------------------------
            # HTTP RATE LIMIT
            # --------------------------------------------

            if response.status_code == 429:

                print(
                    f"HTTP 429 rate limit. "
                    f"Retry {attempt}/{MAX_API_RETRIES}"
                )

                if attempt < MAX_API_RETRIES:

                    time.sleep(
                        RATE_LIMIT_DELAY
                    )

                    continue

                print(
                    "Maximum rate-limit retries reached."
                )

                return None

            # --------------------------------------------
            # OTHER HTTP ERRORS
            # --------------------------------------------

            response.raise_for_status()

            # --------------------------------------------
            # JSON RESPONSE
            # --------------------------------------------

            try:

                data = response.json()

            except ValueError:

                print(
                    "ERROR: Invalid JSON response."
                )

                if attempt < MAX_API_RETRIES:

                    time.sleep(
                        RETRY_DELAY * attempt
                    )

                    continue

                return None

            # --------------------------------------------
            # API-LEVEL RATE LIMIT
            # --------------------------------------------

            message = str(
                data.get("message", "")
            ).lower()

            result = str(
                data.get("result", "")
            ).lower()

            if (
                "rate limit" in message
                or "rate limit" in result
                or "max rate limit" in message
                or "max rate limit" in result
            ):

                print(
                    f"API rate limit detected. "
                    f"Retry {attempt}/{MAX_API_RETRIES}"
                )

                if attempt < MAX_API_RETRIES:

                    time.sleep(
                        RATE_LIMIT_DELAY
                    )

                    continue

                print(
                    "Maximum rate-limit retries reached."
                )

                return None

            # --------------------------------------------
            # CONTROLLED REQUEST DELAY
            # --------------------------------------------

            if REQUEST_DELAY > 0:

                time.sleep(
                    REQUEST_DELAY
                )

            return data

        except requests.exceptions.RequestException as error:

            print(
                f"API request failed "
                f"(attempt {attempt}/{MAX_API_RETRIES}): "
                f"{error}"
            )

            if attempt < MAX_API_RETRIES:

                delay = RETRY_DELAY * attempt

                print(
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

            else:

                print(
                    "Maximum API retries reached."
                )

                return None

    return None


# ============================================================
# TRANSACTION STATUS
# ============================================================

def get_transaction_status(tx):
    """
    Determine transaction status.

    Returns:
        SUCCESS
        FAILED
        UNKNOWN
    """

    is_error = str(
        tx.get("isError", "")
    ).strip()

    receipt_status = str(
        tx.get("txreceipt_status", "")
    ).strip()

    if is_error == "1":

        return "FAILED"

    if (
        is_error == "0"
        and receipt_status in ("1", "")
    ):

        return "SUCCESS"

    if receipt_status == "1":

        return "SUCCESS"

    return "UNKNOWN"


# ============================================================
# ETH TRANSACTION FETCHING
# ============================================================

def fetch_eth_range(
    wallet,
    start_block,
    end_block
):
    """
    Fetch ETH transactions for a block range.

    Handles:
    - Pagination
    - Test mode
    - Page limits
    - API failures
    """

    wallet = normalize_address(wallet)

    all_transactions = []

    for page in range(
        1,
        MAX_PAGES_PER_RANGE + 1
    ):

        params = {

            "module": "account",

            "action": "txlist",

            "address": wallet,

            "startblock": start_block,

            "endblock": end_block,

            "page": page,

            "offset": PAGE_SIZE,

            "sort": "desc",
        }

        data = make_api_request(params)

        if data is None:

            print(
                f"ETH API request failed for "
                f"blocks {start_block}-{end_block}"
            )

            return None

        status = str(
            data.get("status", "")
        )

        message = str(
            data.get("message", "")
        )

        result = data.get("result")

        # --------------------------------------------
        # API ERROR
        # --------------------------------------------

        if status == "0":

            if "No transactions found" in str(result):

                break

            print(
                f"ETH API error: "
                f"{message} | {result}"
            )

            return None

        # --------------------------------------------
        # RESULT VALIDATION
        # --------------------------------------------

        if not isinstance(result, list):

            print(
                "ERROR: Invalid ETH transaction result."
            )

            return None

        if len(result) == 0:

            break

        print(
            f"ETH | Blocks {start_block}-{end_block} "
            f"| Page {page} "
            f"| Records {len(result)}"
        )

        all_transactions.extend(result)

        # --------------------------------------------
        # TEST MODE
        # --------------------------------------------

        if TEST_MODE:

            print(
                "TEST MODE: limited ETH collection."
            )

            break

        # --------------------------------------------
        # PAGE COMPLETION
        # --------------------------------------------

        if len(result) < PAGE_SIZE:

            break

    return all_transactions


# ============================================================
# ERC-20 TRANSFER FETCHING
# ============================================================

def fetch_token_range(
    wallet,
    start_block,
    end_block
):
    """
    Fetch ERC-20 token transfers for a block range.

    Handles:
    - Pagination
    - Test mode
    - API limits
    - API failures
    """

    wallet = normalize_address(wallet)

    all_transfers = []

    for page in range(
        1,
        MAX_PAGES_PER_RANGE + 1
    ):

        params = {

            "module": "account",

            "action": "tokentx",

            "address": wallet,

            "startblock": start_block,

            "endblock": end_block,

            "page": page,

            "offset": PAGE_SIZE,

            "sort": "desc",
        }

        data = make_api_request(params)

        if data is None:

            print(
                f"ERC-20 API request failed for "
                f"blocks {start_block}-{end_block}"
            )

            return None

        status = str(
            data.get("status", "")
        )

        message = str(
            data.get("message", "")
        )

        result = data.get("result")

        # --------------------------------------------
        # API ERROR
        # --------------------------------------------

        if status == "0":

            if "No transactions found" in str(result):

                break

            print(
                f"ERC-20 API error: "
                f"{message} | {result}"
            )

            return None

        # --------------------------------------------
        # RESULT VALIDATION
        # --------------------------------------------

        if not isinstance(result, list):

            print(
                "ERROR: Invalid ERC-20 transfer result."
            )

            return None

        if len(result) == 0:

            break

        print(
            f"ERC20 | Blocks {start_block}-{end_block} "
            f"| Page {page} "
            f"| Records {len(result)}"
        )

        all_transfers.extend(result)

        # --------------------------------------------
        # TEST MODE
        # --------------------------------------------

        if TEST_MODE:

            print(
                "TEST MODE: limited ERC-20 collection."
            )

            break

        # --------------------------------------------
        # PAGE COMPLETION
        # --------------------------------------------

        if len(result) < PAGE_SIZE:

            break

    return all_transfers


# ============================================================
# FIND FIRST BLOCK
# ============================================================

def get_wallet_start_block(wallet):
    """
    Find the first ETH transaction block for the wallet.

    Returns:
        block number
        0    -> no history
        None -> API failure
    """

    wallet = normalize_address(wallet)

    params = {

        "module": "account",

        "action": "txlist",

        "address": wallet,

        "startblock": 0,

        "endblock": 99999999,

        "page": 1,

        "offset": 1,

        "sort": "asc",
    }

    data = make_api_request(params)

    if data is None:

        print(
            "ERROR: Unable to determine wallet "
            "start block."
        )

        return None

    status = str(
        data.get("status", "")
    )

    result = data.get("result")

    message = str(
        data.get("message", "")
    )

    if status == "0":

        if "No transactions found" in str(result):

            return 0

        print(
            f"Etherscan API error: "
            f"{message} | {result}"
        )

        return None

    if not isinstance(result, list):

        print(
            "ERROR: Invalid result from Etherscan."
        )

        return None

    if len(result) == 0:

        return 0

    try:

        return int(
            result[0]["blockNumber"]
        )

    except (
        KeyError,
        ValueError,
        TypeError
    ):

        print(
            "ERROR: Invalid block number."
        )

        return None


# ============================================================
# ETH ADAPTIVE FETCHING
# ============================================================

def fetch_eth_adaptive(
    wallet,
    start_block,
    end_block
):
    """
    Fetch ETH history.

    TEST_MODE:
        Collect only a small sample.

    Production:
        If a range reaches the 10,000-result API
        window, split the block range recursively.
    """

    transactions = fetch_eth_range(
        wallet,
        start_block,
        end_block
    )

    if transactions is None:

        return None

    if TEST_MODE:

        return transactions[
            :TEST_RECORD_LIMIT
        ]

    # --------------------------------------------
    # RANGE WITHIN API LIMIT
    # --------------------------------------------

    if len(transactions) < MAX_RESULTS_PER_RANGE:

        return transactions

    # --------------------------------------------
    # MINIMUM RANGE CHECK
    # --------------------------------------------

    if (
        end_block - start_block
    ) <= MIN_BLOCK_RANGE:

        print(
            "WARNING: Minimum block range reached "
            "while handling the 10,000-result limit."
        )

        return transactions

    # --------------------------------------------
    # SPLIT RANGE
    # --------------------------------------------

    middle = (
        start_block + end_block
    ) // 2

    print(
        "\n10,000-result limit reached."
    )

    print(
        f"Splitting ETH range: "
        f"{start_block}-{middle}"
    )

    print(
        f"Splitting ETH range: "
        f"{middle + 1}-{end_block}"
    )

    first_half = fetch_eth_adaptive(
        wallet,
        start_block,
        middle
    )

    second_half = fetch_eth_adaptive(
        wallet,
        middle + 1,
        end_block
    )

    if (
        first_half is None
        or second_half is None
    ):

        return None

    return first_half + second_half


# ============================================================
# ERC-20 ADAPTIVE FETCHING
# ============================================================

def fetch_token_adaptive(
    wallet,
    start_block,
    end_block
):
    """
    Fetch complete ERC-20 transfer history.

    Uses adaptive block-range splitting when
    the 10,000-result API window is reached.
    """

    transfers = fetch_token_range(
        wallet,
        start_block,
        end_block
    )

    if transfers is None:

        return None

    if TEST_MODE:

        return transfers[
            :TEST_RECORD_LIMIT
        ]

    # --------------------------------------------
    # RANGE WITHIN API LIMIT
    # --------------------------------------------

    if len(transfers) < MAX_RESULTS_PER_RANGE:

        return transfers

    # --------------------------------------------
    # MINIMUM RANGE CHECK
    # --------------------------------------------

    if (
        end_block - start_block
    ) <= MIN_BLOCK_RANGE:

        print(
            "WARNING: Minimum block range reached "
            "while handling the 10,000-result limit."
        )

        return transfers

    # --------------------------------------------
    # SPLIT RANGE
    # --------------------------------------------

    middle = (
        start_block + end_block
    ) // 2

    print(
        "\n10,000-result limit reached."
    )

    print(
        f"Splitting ERC-20 range: "
        f"{start_block}-{middle}"
    )

    print(
        f"Splitting ERC-20 range: "
        f"{middle + 1}-{end_block}"
    )

    first_half = fetch_token_adaptive(
        wallet,
        start_block,
        middle
    )

    second_half = fetch_token_adaptive(
        wallet,
        middle + 1,
        end_block
    )

    if (
        first_half is None
        or second_half is None
    ):

        return None

    return first_half + second_half


# ============================================================
# ETH CLEANING / NORMALIZATION
# ============================================================

def clean_eth_transactions(
    wallet,
    transactions
):
    """
    Clean and normalize ETH transactions.

    IMPORTANT:
        amount      -> ETH
        amount_raw  -> Wei
        amount_unit -> ETH

    Both incoming and outgoing transactions
    are retained.
    """

    wallet = normalize_address(wallet)

    cleaned = []

    seen_hashes = set()

    for tx in transactions:

        tx_hash = tx.get("hash")

        if not tx_hash:

            continue

        tx_hash = tx_hash.lower()

        # --------------------------------------------
        # DUPLICATE PREVENTION
        # --------------------------------------------

        if tx_hash in seen_hashes:

            continue

        seen_hashes.add(tx_hash)

        from_address = normalize_address(
            tx.get("from")
        )

        to_address = normalize_address(
            tx.get("to")
        )

        # --------------------------------------------
        # RAW WEI
        # --------------------------------------------

        raw_value = tx.get(
            "value",
            "0"
        )

        try:

            raw_value_int = int(
                raw_value
            )

            eth_value = (
                raw_value_int / 10**18
            )

        except (
            ValueError,
            TypeError
        ):

            raw_value_int = 0

            eth_value = 0.0

        # --------------------------------------------
        # DIRECTION
        # --------------------------------------------

        if from_address == wallet:

            direction = "OUT"

        elif to_address == wallet:

            direction = "IN"

        else:

            direction = "UNKNOWN"

        # --------------------------------------------
        # STATUS
        # --------------------------------------------

        transaction_status = (
            get_transaction_status(tx)
        )

        # --------------------------------------------
        # BLOCK NUMBER
        # --------------------------------------------

        try:

            block_number = int(
                tx.get(
                    "blockNumber",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            block_number = 0

        # --------------------------------------------
        # TRANSACTION INDEX
        # --------------------------------------------

        try:

            transaction_index = int(
                tx.get(
                    "transactionIndex",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            transaction_index = 0

        # --------------------------------------------
        # NORMALIZED RECORD
        # --------------------------------------------

        cleaned.append({

            "from": from_address,

            "to": to_address,

            "amount": eth_value,

            "amount_unit": "ETH",

            "amount_raw": str(
                raw_value_int
            ),

            "timestamp": convert_timestamp(
                tx.get("timeStamp")
            ),

            "tx_hash": tx_hash,

            "token": "ETH",

            "token_symbol": "ETH",

            "chain": "ethereum",

            "direction": direction,

            "transaction_status":
                transaction_status,

            "transaction_type":
                "NATIVE_TRANSFER",

            "block_number":
                block_number,

            "transaction_index":
                transaction_index,
        })

    return cleaned


# ============================================================
# ERC-20 CLEANING / NORMALIZATION
# ============================================================

def clean_token_transfers(
    wallet,
    transfers
):
    """
    Clean and normalize ERC-20 transfers.

    IMPORTANT:
        amount is expressed in the token's
        human-readable unit after applying decimals.

    Example:
        1250.5 USDT

    Raw blockchain value is retained in amount_raw.

    Both incoming and outgoing transfers are retained.
    """

    wallet = normalize_address(wallet)

    cleaned = []

    seen_transfers = set()

    for tx in transfers:

        tx_hash = tx.get("hash")

        if not tx_hash:

            continue

        tx_hash = tx_hash.lower()

        from_address = normalize_address(
            tx.get("from")
        )

        to_address = normalize_address(
            tx.get("to")
        )

        contract_address = normalize_address(
            tx.get("contractAddress")
        )

        raw_value = tx.get(
            "value",
            "0"
        )

        # --------------------------------------------
        # BLOCK NUMBER
        # --------------------------------------------

        try:

            block_number = int(
                tx.get(
                    "blockNumber",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            block_number = 0

        # --------------------------------------------
        # TRANSACTION INDEX
        # --------------------------------------------

        try:

            transaction_index = int(
                tx.get(
                    "transactionIndex",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            transaction_index = 0

        # --------------------------------------------
        # DUPLICATE FINGERPRINT
        # --------------------------------------------

        duplicate_key = (

            tx_hash,

            block_number,

            transaction_index,

            contract_address,

            from_address,

            to_address,

            str(raw_value),
        )

        if duplicate_key in seen_transfers:

            continue

        seen_transfers.add(
            duplicate_key
        )

        # --------------------------------------------
        # TOKEN DECIMALS
        # --------------------------------------------

        try:

            decimals = int(
                tx.get(
                    "tokenDecimal",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            decimals = 0

        # --------------------------------------------
        # RAW TOKEN VALUE
        # --------------------------------------------

        try:

            raw_value_int = int(
                raw_value
            )

            token_amount = (
                raw_value_int
                / (10 ** decimals)
            )

        except (
            ValueError,
            TypeError
        ):

            raw_value_int = 0

            token_amount = 0.0

        # --------------------------------------------
        # DIRECTION
        # --------------------------------------------

        if from_address == wallet:

            direction = "OUT"

        elif to_address == wallet:

            direction = "IN"

        else:

            direction = "UNKNOWN"

        # --------------------------------------------
        # STATUS
        # --------------------------------------------

        transaction_status = (
            get_transaction_status(tx)
        )

        # --------------------------------------------
        # TOKEN METADATA
        # --------------------------------------------

        token_name = str(
            tx.get(
                "tokenName",
                ""
            )
        )

        token_symbol = str(
            tx.get(
                "tokenSymbol",
                ""
            )
        )

        # --------------------------------------------
        # NORMALIZED RECORD
        # --------------------------------------------

        cleaned.append({

            "from": from_address,

            "to": to_address,

            "amount": token_amount,

            "amount_unit":
                token_symbol
                if token_symbol
                else "TOKEN",

            "amount_raw": str(
                raw_value_int
            ),

            "timestamp": convert_timestamp(
                tx.get("timeStamp")
            ),

            "tx_hash": tx_hash,

            "token":
                token_symbol
                if token_symbol
                else token_name,

            "token_symbol":
                token_symbol,

            "chain":
                "ethereum",

            "direction": direction,

            "transaction_status":
                transaction_status,

            "transaction_type":
                "ERC20_TRANSFER",

            "token_name":
                token_name,

            "token_contract":
                contract_address,

            "token_decimals":
                decimals,

            "block_number":
                block_number,

            "transaction_index":
                transaction_index,
        })

    return cleaned


# ============================================================
# GET ETH TRANSACTIONS
# ============================================================

def get_transactions(wallet):
    """
    Collect and clean ETH transactions.
    """

    wallet = normalize_address(wallet)

    if not is_valid_wallet_address(wallet):

        print(
            f"ERROR: Invalid Ethereum wallet address: "
            f"{wallet}"
        )

        return []

    start_block = get_wallet_start_block(
        wallet
    )

    if start_block is None:

        print(
            "ETH collection aborted."
        )

        return []

    if start_block == 0:

        print(
            "No ETH transaction history found."
        )

        return []

    end_block = 99999999

    print(
        f"\nETH block range: "
        f"{start_block} to {end_block}"
    )

    transactions = fetch_eth_adaptive(
        wallet,
        start_block,
        end_block
    )

    if transactions is None:

        print(
            "ETH collection failed."
        )

        return []

    cleaned = clean_eth_transactions(
        wallet,
        transactions
    )

    print(
        f"ETH collection complete: "
        f"{len(cleaned)} unique transactions"
    )

    return cleaned


# ============================================================
# GET ERC-20 TRANSFERS
# ============================================================

def get_token_transfers(wallet):
    """
    Collect and clean ERC-20 token transfers.
    """

    wallet = normalize_address(wallet)

    if not is_valid_wallet_address(wallet):

        print(
            f"ERROR: Invalid Ethereum wallet address: "
            f"{wallet}"
        )

        return []

    start_block = get_wallet_start_block(
        wallet
    )

    if start_block is None:

        print(
            "ERC-20 collection aborted."
        )

        return []

    if start_block == 0:

        print(
            "No ERC-20 transfer history found."
        )

        return []

    end_block = 99999999

    print(
        f"\nERC-20 block range: "
        f"{start_block} to {end_block}"
    )

    transfers = fetch_token_adaptive(
        wallet,
        start_block,
        end_block
    )

    if transfers is None:

        print(
            "ERC-20 collection failed."
        )

        return []

    cleaned = clean_token_transfers(
        wallet,
        transfers
    )

    print(
        f"ERC-20 collection complete: "
        f"{len(cleaned)} unique transfers"
    )

    return cleaned


# ============================================================
# COMBINED CLEAN BLOCKCHAIN DATA
# ============================================================

def get_clean_blockchain_data(wallet):
    """
    Public interface for other modules.

    Input:
        Ethereum wallet address

    Output:
        Standardized blockchain transaction JSON.

    Example:

    {
        "wallet": "0x...",
        "chain": "ethereum",
        "transactions": [...]
    }

    Both ETH and ERC-20 transactions are included.

    ETH:
        amount -> ETH

    ERC-20:
        amount -> token's human-readable unit
    """

    wallet = normalize_address(wallet)

    if not is_valid_wallet_address(wallet):

        raise ValueError(
            "Invalid Ethereum wallet address."
        )

    print(
        "\n========================================"
    )

    print(
        "COLLECTING BLOCKCHAIN DATA"
    )

    print(
        "========================================"
    )

    # --------------------------------------------
    # ETH
    # --------------------------------------------

    print(
        "\nFetching ETH transactions..."
    )

    eth_transactions = get_transactions(
        wallet
    )

    # --------------------------------------------
    # ERC-20
    # --------------------------------------------

    print(
        "\nFetching ERC-20 transfers..."
    )

    token_transfers = get_token_transfers(
        wallet
    )

    # --------------------------------------------
    # COMBINE
    # --------------------------------------------

    all_transactions = (
        eth_transactions
        + token_transfers
    )

    # --------------------------------------------
    # SORT BY TIMESTAMP
    # --------------------------------------------

    all_transactions.sort(
        key=lambda tx: (
            tx.get("timestamp") or ""
        )
    )

    return {

        "wallet": wallet,

        "chain": "ethereum",

        "transactions": all_transactions
    }


# ============================================================
# SMART CONTRACT DETECTION
# ============================================================

def is_contract_address(address):
    """
    Determine whether an Ethereum address
    is a smart contract.

    Result is cached to reduce API calls.
    """

    address = normalize_address(address)

    if not is_valid_wallet_address(address):

        return False

    # --------------------------------------------
    # CACHE
    # --------------------------------------------

    if CONTRACT_CACHE_ENABLED:

        if address in contract_cache:

            return contract_cache[address]

    # --------------------------------------------
    # API REQUEST
    # --------------------------------------------

    params = {

        "module": "proxy",

        "action": "eth_getCode",

        "address": address,

        "tag": "latest",
    }

    data = make_api_request(params)

    if data is None:

        print(
            f"WARNING: Could not determine contract "
            f"status for {address}"
        )

        return False

    result = data.get(
        "result"
    )

    is_contract = (

        isinstance(result, str)

        and result != "0x"

        and result != "0x0"
    )

    # --------------------------------------------
    # CACHE RESULT
    # --------------------------------------------

    if CONTRACT_CACHE_ENABLED:

        contract_cache[
            address
        ] = is_contract

    return is_contract