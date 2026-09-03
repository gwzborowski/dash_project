import requests
import pandas as pd

url = "https://finance.yahoo.com/quote/BTC-USD/history/?period1=1756862410&period2=1788398410"

params = {
    "range": "1yr",
    "interval": "1d"
}

response = requests.get(url, params=params)

data = response.json()

print(data)