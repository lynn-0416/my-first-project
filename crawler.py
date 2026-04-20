import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import server

session = requests.Session()

retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
session.mount("https://", adapter)
session.mount("http://", adapter)

api_cache = {}

# =========================
# current market data
# =========================
def fetch_market_data(item_batch):
    ids_str = ",".join(map(str, item_batch))

    if ids_str in api_cache:
        return api_cache[ids_str]

    url = f"https://universalis.app/api/v2/{server}/{ids_str}"

    try:
        res = session.get(url, timeout=6)
        data = res.json()
        api_cache[ids_str] = data
        return data
    except Exception:
        return {"items": {}}


# =========================
# marketable items
# =========================
def fetch_marketable_items():
    url = "https://universalis.app/api/v2/marketable"
    return requests.get(url, timeout=10).json()


# =========================
# history 
# =========================
def fetch_item_history(item_id):
    url = f"https://universalis.app/api/v2/history/{server}/{item_id}"

    try:
        res = session.get(url, timeout=6)
        return res.json().get("entries", [])
    except Exception:
        return []