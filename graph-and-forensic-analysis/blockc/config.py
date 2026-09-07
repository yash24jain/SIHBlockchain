import os
from dotenv import load_dotenv

load_dotenv()

# Etherscan API configuration
API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://api.etherscan.io/v2/api"
CHAIN_ID = 1  # Ethereum Mainnet

# Pagination and query parameters
PAGE_SIZE = 100
MAX_PAGES_PER_RANGE = 5
MAX_RESULTS_PER_RANGE = 10000
MIN_BLOCK_RANGE = 1000

# Testing and development flags
TEST_MODE = True
TEST_RECORD_LIMIT = 10

# Network and resilience settings
REQUEST_TIMEOUT = 15
MAX_API_RETRIES = 3
RETRY_DELAY = 1.0
RATE_LIMIT_DELAY = 2.0
REQUEST_DELAY = 0.2

# Contract cache
CONTRACT_CACHE_ENABLED = True