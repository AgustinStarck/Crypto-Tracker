from rest_framework import serializers
from .models import Kline , priceAlert , ETHline

class BTCPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kline
        fields = '__all__'
        read_only_fields = ['created_at']

class ETHPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ETHline
        fields = '__all__'
        read_only_fields = ['created_at']


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = priceAlert
        fields = ['id', 'email','crypto' ,'alert_type', 'target_price', 'percentage_change', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        
        if 'crypto' in data:
            data['crypto'] = data['crypto'].upper()
        
       
        if data['alert_type'] in ['above', 'below']:
            if not data.get('target_price'):
                raise serializers.ValidationError("target_price es requerido para alertas de precio")
          
            data['percentage_change'] = None
            
        elif data['alert_type'] == 'change':
            if not data.get('percentage_change'):
                raise serializers.ValidationError("percentage_change es requerido para alertas de cambio")
            
            data['target_price'] = None
            
        return data

class ChartDataSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = Kline
        fields = ['timestamp', 'open', 'high', 'low', 'close']  
    
    def get_timestamp(self, obj):
        return obj.open_time.timestamp()
    
class ETHChartDataSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = ETHline
        fields = ['timestamp', 'open', 'high', 'low', 'close']  
    
    def get_timestamp(self, obj):
        return obj.open_time.timestamp()