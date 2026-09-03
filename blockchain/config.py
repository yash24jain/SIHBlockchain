import os

# Etherscan API
API_KEY = os.getenv("ETHERSCAN_API_KEY")

BASE_URL = "https://api.etherscan.io/v2/api"

# Ethereum Mainnet
CHAIN_ID = 1

# Pagination
PAGE_SIZE = 100
MAX_PAGES_PER_RANGE = 100

# Etherscan's result window
MAX_RESULTS_PER_RANGE = 10000
MIN_BLOCK_RANGE = 1000

# Testing
TEST_MODE = True
TEST_RECORD_LIMIT = 10

# API hardening
REQUEST_TIMEOUT = 15
MAX_API_RETRIES = 3
RETRY_DELAY = 1
RATE_LIMIT_DELAY = 2
REQUEST_DELAY = 0.2

# Contract detection
CONTRACT_CACHE_ENABLED = True