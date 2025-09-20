from django.shortcuts import render
from rest_framework import viewsets, status , permissions
from .models import Kline , priceAlert , ETHline
from .serializers import BTCPriceSerializer, PriceAlertSerializer , ChartDataSerializer , ETHPriceSerializer
from .services import AlertService
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from binance.client import Client
from datetime import datetime , timedelta
import time
import requests
import random


class BTCPriceViewSet(viewsets.ModelViewSet):
  queryset = Kline.objects.all().order_by('-open_time')
  serializer_class = BTCPriceSerializer

  @action(detail=False, methods=['post'])
  def fetch_prices(self, request):

    try:
        precios_guardados = self.obtener_precios_btc()
        serializer = self.get_serializer(precios_guardados, many=True)
        return Response({
           'message':f'se han guardado {len(precios_guardados)} precios',
           'data': serializer.data
        })

    except Exception as e:
      return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  @action(detail=False, methods=['get'])  
  def latest_prices(self, request):
    
    limit = request.GET.get('limit', 100)
    prices = Kline.objects.all().order_by('-open_time')[:int(limit)]
    serializer = self.get_serializer(prices, many=True)
    return Response(serializer.data)
  

  def calculate_24h_change(self, prices):
        if not prices or len(prices) < 2:
            return 0.0
        first = prices[0]
        last = prices[-1]
        return ((last - first) / first) * 100 if first else 0.0

    
  @action(detail=False, methods=['get'])
  def stats(self, request):
        try:
            since = timezone.now() - timedelta(hours=24)
            recent = Kline.objects.filter(open_time__gte=since)

            if not recent.exists():
                return Response({'error': 'No hay datos ETH recientes'}, status=status.HTTP_404_NOT_FOUND)

            prices = [float(item.close) for item in recent]

            stats = {
                'current_price': prices[-1] if prices else 0,
                '24h_high': max(prices) if prices else 0,
                '24h_low': min(prices) if prices else 0,
                '24h_volume': recent.count(),          
                '24h_change': self.calculate_24h_change(prices),
            }
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



  
  def obtener_precios_btc(self):
    try:
        
        url = "https://api.kraken.com/0/public/OHLC"
        params = {
            'pair': 'XBTUSD', 
            'interval': 1,     
            'limit': 10        
        }
        
       
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                
                response = requests.get(
                    url, 
                    params=params, 
                    timeout=30
                )
                
                if response.status_code == 429:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Rate limit 429. Reintento {attempt + 1} en {wait_time} segundos...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code != 200:
                    print(f"Error Kraken: {response.status_code}, Response: {response.text}")
                    return []
                
                data = response.json()
                
               
                if data.get('error'):
                    print(f"Error Kraken API: {data['error']}")
                    return []
                
              
                ohlc_data = data['result']['XXBTZUSD']  
                print(f"Datos recibidos de Kraken: {len(ohlc_data)} velas") 
                break
                    
            except Exception as e:
                print(f"Error en attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return []
                time.sleep(retry_delay * (2 ** attempt))
        else:
            print("Todos los intentos fallaron")
            return []
        
        precio_guardados = []
        previous_price = None
        last_price = Kline.objects.order_by('-open_time').first()  
        
        if last_price:
            previous_price = last_price.close  

        
        for vela in ohlc_data:
            
            timestamp = vela[0]
            open_time = datetime.fromtimestamp(timestamp)
            open_time = timezone.make_aware(open_time)
            
            open_price = vela[1]
            high_price = vela[2]
            low_price = vela[3]
            close_price = vela[4]
            close_time = open_time + timedelta(minutes=1)

            if not Kline.objects.filter(open_time=open_time).exists():
                current_price = float(close_price)
                
                precio = Kline(
                    open_time=open_time,
                    open=float(open_price),
                    high=float(high_price),
                    low=float(low_price),
                    close=float(close_price),
                    close_time=close_time
                )

                precio.save()
                precio_guardados.append(precio)

                if previous_price is not None:
                    AlertService.check_price_alerts(current_price, previous_price, 'BTC')
                    
                previous_price = current_price  
        
        print(f"Precios guardados: {len(precio_guardados)}")  
        return precio_guardados
        
    except KeyError as e:
        print(f"Error en estructura de datos de Kraken: {e}")
        print(f"Respuesta completa: {data}")
        return []
    except Exception as e:
        print(f"Error final en obtener_precios_btc: {e}")
        return []
    
  @action(detail=False, methods=['get'])
  def chart_data(self, request):
        
        try:
            interval = request.GET.get('interval', '1h')
            limit = int(request.GET.get('limit', 100))
            
            
            data = Kline.objects.all().order_by('-open_time')[:limit]
            serializer = self.get_serializer(data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
       

class PriceAlerViewSet(viewsets.ModelViewSet):
   serializer_class = PriceAlertSerializer
   permission_classes = [permissions.AllowAny]

   def get_queryset(self):
        
      email = self.request.query_params.get('email')
      if email:
          return priceAlert.objects.filter(email=email)
      return priceAlert.objects.all()


############################ EHT view ######################################

class ETHPriceViewSet(viewsets.ModelViewSet):
  queryset = ETHline.objects.all().order_by('-open_time')
  serializer_class = ETHPriceSerializer

  @action(detail=False, methods=['post'])
  def fetch_prices(self, request):

    try:
        precios_guardados = self.obtener_precios_eth()
        serializer = self.get_serializer(precios_guardados, many=True)
        return Response({
           'message':f'se han guardado {len(precios_guardados)} precios',
           'data': serializer.data
        })

    except Exception as e:
      return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  @action(detail=False, methods=['get'])  
  def latest_prices(self, request):
    
    limit = request.GET.get('limit', 100)
    prices = ETHline.objects.all().order_by('-open_time')[:int(limit)]
    serializer = self.get_serializer(prices, many=True)
    return Response(serializer.data)
  
  def calculate_24h_change(self, prices):
        if not prices or len(prices) < 2:
            return 0.0
        first = prices[0]
        last = prices[-1]
        return ((last - first) / first) * 100 if first else 0.0

    
  @action(detail=False, methods=['get'])
  def stats(self, request):
        try:
            since = timezone.now() - timedelta(hours=24)
            recent = ETHline.objects.filter(open_time__gte=since)

            if not recent.exists():
                return Response({'error': 'No hay datos ETH recientes'}, status=status.HTTP_404_NOT_FOUND)

            prices = [float(item.close) for item in recent]

            stats = {
                'current_price': prices[-1] if prices else 0,
                '24h_high': max(prices) if prices else 0,
                '24h_low': min(prices) if prices else 0,
                '24h_volume': recent.count(),          
                '24h_change': self.calculate_24h_change(prices),
            }
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

  
  def obtener_precios_eth(self):
    try:
        
        url = "https://api.kraken.com/0/public/OHLC"
        params = {
            'pair': 'ETHUSD',   
            'interval': 1,       
            'limit': 10          
        }
        

        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    timeout=30
                )
                
                if response.status_code == 429:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Rate limit 429. Reintento {attempt + 1} en {wait_time} segundos...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code != 200:
                    print(f"Error Kraken: {response.status_code}, Response: {response.text}")
                    return []
                
                data = response.json()
                
                if data.get('error'):
                    print(f"Error Kraken API: {data['error']}")
                    return []
                
                
                ohlc_data = data['result']['XETHZUSD']  
                print(f"Datos ETH recibidos de Kraken: {len(ohlc_data)} velas")
                break
                    
            except Exception as e:
                print(f"Error en attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return []
                time.sleep(retry_delay * (2 ** attempt))
        else:
            print("Todos los intentos fallaron")
            return []
        
        precio_guardados = []
        previous_price = None

        last_price = ETHline.objects.order_by('-open_time').first()  
        if last_price:
            previous_price = last_price.close  

       
        for vela in ohlc_data[-10:]:  
            
            timestamp = vela[0]
            open_time = datetime.fromtimestamp(timestamp)
            open_time = timezone.make_aware(open_time)
            
            close_time = open_time + timedelta(minutes=1)

            if not ETHline.objects.filter(open_time=open_time).exists():
                current_price = float(vela[4]) 
                
                precio = ETHline(
                    open_time=open_time,
                    open=float(vela[1]),    
                    high=float(vela[2]),    
                    low=float(vela[3]),     
                    close=float(vela[4]),  
                    close_time=close_time
                )

                precio.save()
                precio_guardados.append(precio)

                if previous_price is not None:
                    AlertService.check_price_alerts(current_price, previous_price, 'ETH')
                    
                previous_price = current_price  
                
        return precio_guardados
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
    


  @action(detail=False, methods=['get'])
  def chart_data(self, request):
        
        try:
            interval = request.GET.get('interval', '1h')
            limit = int(request.GET.get('limit', 100))
            
            
            data = ETHline.objects.all().order_by('-open_time')[:limit]
            serializer = self.get_serializer(data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)  
        

