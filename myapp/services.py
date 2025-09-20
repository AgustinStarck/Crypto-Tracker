from django.core.mail import send_mail
from django.utils.html import format_html , strip_tags
from django.conf import settings
from django.template.loader import render_to_string
from .models import priceAlert, Kline, ETHline
from django.contrib.auth.models import User
import decimal

class AlertService:
    @staticmethod
    def check_price_alerts(current_price, previous_price, crypto='BTC'):
        
        if previous_price is None:
            return
        
        price_change = ((current_price - previous_price) / previous_price) * 100
        
        
        change_alerts = priceAlert.objects.filter(
            crypto=crypto,
            alert_type='change', 
            is_active=True
        )
        
        for alert in change_alerts:
            if abs(price_change) >= alert.percentage_change:
                AlertService.send_alert_email(alert, current_price, price_change, crypto)
                
                alert.is_active = False
                alert.save()
        
        price_alerts = priceAlert.objects.filter(
            crypto=crypto,
            alert_type__in=['above', 'below'], 
            is_active=True
        )
        
        for alert in price_alerts:
            if (alert.alert_type == 'above' and current_price >= alert.target_price) or \
               (alert.alert_type == 'below' and current_price <= alert.target_price):
                AlertService.send_alert_email(alert, current_price, price_change, crypto)
                
                alert.is_active = False
                alert.save()
    
    @staticmethod
    def send_alert_email(alert, current_price, price_change, crypto):
        subject = f"🚨 Alerta de {crypto} - ${current_price:.2f}"
        
        
        if alert.alert_type == 'change':
            subject = f"📈 Alerta de cambio activada: {crypto}"
            html_content = f"""
            <html>
            <body style="margin:0;padding:0;background-color:#f4f6fb;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6fb;">
                <tr>
                    <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="margin:40px auto;background:#ffffff;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.1);">
                        <tr>
                        <td style="padding:40px 48px 24px;">
                            <h2 style="margin:0;color:#1a1a1a;font-size:24px;">📈 Alerta de cambio porcentual</h2>
                            <p style="margin:12px 0 0;color:#555;font-size:16px;">Tu alerta para <strong>{crypto}</strong> se ha activado.</p>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding:0 48px 32px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;border-radius:6px;padding:20px;">
                            <tr><td style="font-size:15px;color:#333;"><strong>Criptomoneda:</strong> {crypto}</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Precio actual:</strong> ${current_price:.2f}</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Cambio:</strong> {price_change:.2f}%</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Cambio objetivo:</strong> {alert.percentage_change}%</td></tr>
                            </table>
                            <p style="margin:24px 0 0;color:#777;font-size:14px;">Esta alerta ha sido <strong>desactivada automáticamente</strong>.</p>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding:24px 48px 40px;background:#f1f3f5;border-radius:0 0 8px 8px;text-align:center;">
                            <p style="margin:0;color:#888;font-size:13px;">Saludos,<br><strong>Sistema de Alertas Crypto Tracker</strong></p>
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>
                </table>
            </body>
            </html>
            """
        else:
            action = "superado" if alert.alert_type == "above" else "bajado de"
            subject = f"💰 Alerta de precio activada: {crypto}"
            html_content = f"""
            <html>
            <body style="margin:0;padding:0;background-color:#f4f6fb;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6fb;">
                <tr>
                    <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="margin:40px auto;background:#ffffff;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.1);">
                        <tr>
                        <td style="padding:40px 48px 24px;">
                            <h2 style="margin:0;color:#1a1a1a;font-size:24px;">💰 Alerta de precio</h2>
                            <p style="margin:12px 0 0;color:#555;font-size:16px;">Tu alerta para <strong>{crypto}</strong> se ha activado.</p>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding:0 48px 32px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;border-radius:6px;padding:20px;">
                            <tr><td style="font-size:15px;color:#333;"><strong>Criptomoneda:</strong> {crypto}</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Precio actual:</strong> ${current_price:.2f}</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Precio objetivo:</strong> ${alert.target_price:.2f}</td></tr>
                            <tr><td style="font-size:15px;color:#333;padding-top:8px;"><strong>Estado:</strong> El precio ha {action} tu objetivo</td></tr>
                            </table>
                            <p style="margin:24px 0 0;color:#777;font-size:14px;">Esta alerta ha sido <strong>desactivada automáticamente</strong>.</p>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding:24px 48px 40px;background:#f1f3f5;border-radius:0 0 8px 8px;text-align:center;">
                            <p style="margin:0;color:#888;font-size:13px;">Saludos,<br><strong>Sistema de Alertas Crypto Tracker</strong></p>
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>
                </table>
            </body>
            </html>
            """


        plain_message = strip_tags(html_content.replace('<br>', '\n').replace('</p>', '\n\n'))
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.email],
                fail_silently=False,
                html_message=html_content,
            )
            print(f"Email enviado a {alert.email} para alerta de {crypto}")
        except Exception as e:
            print(f"Error enviando email a {alert.email}: {e}")
            
            alert.is_active = True
            alert.save()