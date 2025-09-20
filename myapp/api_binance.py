from binance.client import Client
import time
from datetime import datetime

def obtener_precios_btc():

  client = Client(api_key=None, api_secret=None)

  klines = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)

  precio_btc = []

  for vela in klines:
      precio = {
          "open-time": datetime.fromtimestamp(vela[0]/1000),
          "open": float(vela[1]),
          "high": float(vela[2]),
          "low": float(vela[3]),
          "close": float(vela[4]),
          "close-time": datetime.fromtimestamp(vela[6]/1000),
      }
      precio_btc.append(precio)

  return precio_btc






