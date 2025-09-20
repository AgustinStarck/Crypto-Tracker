# app/management/commands/fetch_btc_prices.py
from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from myapp.views import BTCPriceViewSet
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'se obtendran precios cada 10 minutos'

    def handle(self, *args, **options):
        scheduler = BlockingScheduler()
        viewset = BTCPriceViewSet()
        
        def fetch_job():
            try:
                precios_guardados = viewset.obtener_precios_btc()
                logger.info(f'Guardados {len(precios_guardados)} precios nuevos a las {timezone.now()}')
            except Exception as e:
                logger.error(f'Error: {str(e)}')

        scheduler.add_job(
            fetch_job,
            trigger=IntervalTrigger(minutes=10),
            id='btc_price_fetcher',
            max_instances=1,
            replace_existing=True,
        )

        self.stdout.write(
            self.style.SUCCESS('btc fetcher activo')
        )
        
        try:
            scheduler.start()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('fetcher apagado')
            )
            scheduler.shutdown()