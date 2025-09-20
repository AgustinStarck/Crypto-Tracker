from django.db import models
from django.contrib.auth.models import User

class Kline(models.Model):
    open_time = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    close_time = models.DateTimeField()

    class Meta:
        db_table = 'btc_prices'
        indexes = [
            models.Index(fields=['open_time']),
            models.Index(fields=['close_time']),
        ]
        ordering = ['-open_time']
    def __str__(self):
        return f"BTC Price at {self.open_time}"

class ETHline(models.Model):
    open_time = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    close_time = models.DateTimeField()

    class Meta:
        db_table = 'eth_prices'
        indexes = [
            models.Index(fields=['open_time']),
            models.Index(fields=['close_time']),
        ]
        ordering = ['-open_time']
    def __str__(self):
        return f"ETH Price at {self.open_time}"

class email(models.Model):
    email = models.EmailField(unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.email
    
class priceAlert(models.Model):

    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    ]

    ALERT_TYPES = [
        ('above', 'Precio por encima de'),
        ('below', 'Precio por debajo de'),
        ('change', 'Cambio porcentual'),
    ]

    email = models.CharField(max_length=255, unique=False)  
    crypto = models.CharField(max_length=3, choices=CRYPTO_CHOICES, default='BTC')
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    target_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.alert_type == 'change':
            return f"{self.email} - {self.percentage_change}% change for {self.crypto}"
        return f"{self.email} - {self.alert_type} {self.target_price} for {self.crypto}"