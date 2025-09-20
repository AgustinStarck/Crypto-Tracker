
import json
import requests

def proxiextractor():
  response = requests.get("https://proxyfreeonly.com/api/free-proxy-list?limit=500&page=1&country=AR&sortBy=lastChecked&sortType=desc")
  datos = response.json()  

  prox= []
  
  if isinstance(datos, list) and len(datos) > 0:
      
      if isinstance(datos[0], dict):
          ip = datos[0]["ip"]
          port = datos[0]["port"]
          
          for proxy in datos:    

              proxies = f"{proxy['ip']}:{proxy['port']}"

              prox.append(proxies)
  return prox

