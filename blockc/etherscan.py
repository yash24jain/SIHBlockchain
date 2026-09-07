import os
import requests

from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ETHERSCAN_API_KEY")

BASE_URL = "https://api.etherscan.io/v2/api"


def get_transactions(wallet_address):

    params = {
        "chainid": "1",
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,
        "sort": "asc",
        "apikey": API_KEY
    }

    response = requests.get(
        BASE_URL,
        params=params
    )

    response.raise_for_status()

    data = response.json()

    return data