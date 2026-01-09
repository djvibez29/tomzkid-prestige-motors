# utils.py
import requests
from datetime import datetime, timedelta

# Global variable to store the cached rate
cached_rate = None
last_updated = None

def get_usd_to_ngn_rate():
    global cached_rate, last_updated

    now = datetime.now()

    # If rate exists and was updated within the last hour, return it
    if cached_rate and last_updated and (now - last_updated) < timedelta(hours=1):
        return cached_rate

    # Fetch new rate from API
    try:
        response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=NGN")
        if response.status_code == 200:
            data = response.json()
            rate = float(data["rates"]["NGN"])
            cached_rate = rate
            last_updated = now
            return rate
    except:
        pass

    # Fallback if API fails
    return 1430  # current approximate USD → NGN
