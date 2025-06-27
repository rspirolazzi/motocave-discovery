from scrapy import signals
from scrapy.exceptions import NotConfigured

class ProductSignalMiddleware:
    """Middleware que usa señales para reaccionar a eventos del spider"""
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.products_count = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('PRODUCT_SIGNAL_MIDDLEWARE_ENABLED', True):
            raise NotConfigured('ProductSignalMiddleware is disabled')
        
        middleware = cls(crawler)
        
        # Conectar a las señales
        crawler.signals.connect(middleware.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        
        return middleware
    
    def spider_opened(self, spider):
        spider.logger.info(f'ProductSignalMiddleware: Spider {spider.name} abierto')
    
    def spider_closed(self, spider):
        spider.logger.info(f'ProductSignalMiddleware: Spider {spider.name} cerrado. Total productos: {self.products_count}')
    
    def item_scraped(self, item, response, spider):
        """Se ejecuta cada vez que se extrae un item (producto)"""
        self.products_count += 1
        spider.logger.info(f'ProductSignalMiddleware: Producto extraído #{self.products_count}: {item.get("name", "Sin nombre")}')
        
        # Aquí puedes agregar tu lógica personalizada
        # Por ejemplo, enviar una notificación cada N productos
        if self.products_count % 5 == 0:
            spider.logger.info(f'Milestone: {self.products_count} productos procesados!')
        
        # Ejemplo: guardar checkpoint cada 20 productos
        if self.products_count % 20 == 0:
            spider.logger.info(f'Guardando checkpoint en producto #{self.products_count}')
            # self.save_checkpoint(spider, self.products_count)
