import requests
import pandas as pd
from datetime import datetime

url = "https://finance.yahoo.com/quote/BTC-USD/history"  # Example for Apple Inc. You can change the ticker symbol as needed.

headers = {
    "User-Agent": "Mozilla/5.0"
}

params = {
    "range": "1yr",
    "interval": "1d"
}

response = requests.get(
    url,
    params=params,
    headers=headers
)

response.raise_for_status()

data = response.json()

result = data["chart"]["result"][0]

quote = result["indicators"]["quote"][0]

df = pd.DataFrame({
    "Date": pd.to_datetime(result["timestamp"], unit="s"),
    "Open": quote["open"],
    "High": quote["high"],
    "Low": quote["low"],
    "Close": quote["close"],
    "Adj Close": result["indicators"]["adjclose"][0]["adjclose"],
    "Volume": quote["volume"]
})

print(df)