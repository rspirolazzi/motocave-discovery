import os
import scrapy
from datetime import datetime
from ..logger import get_logger
from scrapy import signals

class BaseSpider(scrapy.Spider):
    logger = None
    products = []
    source = None  # Información de la fuente, se puede sobrescribir en subclases

    # XPATHS como atributos de clase
    XPATH_MENU_ITEMS = None
    XPATH_SUBMENU = None
    XPATH_MENU_LINK = None
    XPATH_MENU_LINK_HREF = None
    XPATH_MENU_LINK_TEXT = None
    XPATH_SUB_LINKS = None
    XPATH_PRODUCT_LINKS = None
    XPATH_NEXT_PAGE = None
    XPATH_PRODUCT_NAME = None
    XPATH_PRODUCT_PRICE = None
    XPATH_PRODUCT_IMAGES = None
    XPATH_PRODUCT_DESCRIPTION = None
    XPATH_BREADCRUMB_LAST = None
    HANDLE_PAGINATION = True  # Habilitar paginación por defecto


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = None  # Se inicializa en init_crawler

    # Mapping de campos a métodos
    product_field_mapping = {
        'menu_name': 'parse_product_menu_name',
        'menu_url': 'parse_product_menu_url',
        'product_url': 'parse_product_url',
        'name': 'parse_product_name',
        'price': 'parse_product_price',
        'images': 'parse_product_images',
        'description': 'parse_product_description',
        'category_name': 'parse_product_category_name',
        'category_url': 'parse_product_category_url',
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.init_crawler()
        crawler.signals.connect(spider.on_feed_exporter_closed, signal=signals.feed_exporter_closed)
        return spider

    def init_crawler(self):
        """
        Crea el directorio de salida para el spider y configura rutas de log y output.
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        build_dir = os.path.join('build', self.name, timestamp)
        os.makedirs(build_dir, exist_ok=True)

        # Configurar archivo de log y output en el directorio build
        output_filename = os.path.join(build_dir, f'{self.name}.json')
        self.logger = get_logger(self.name, f'{os.path.join(build_dir, 'app.log')}')
        self.output_filename = output_filename
        self.logger.info(f"Directorio de build creado: {build_dir}")
        
        self.crawler.settings.set('FEEDS', {
            output_filename: {
                'format': 'json',
                'overwrite': True
            }
        })
        

    def parse_product(self, response):
        self.logger.info(f"Parseando producto: {response.url}")
        data = {}
        for field, method_name in self.product_field_mapping.items():
            method = getattr(self, method_name, None)
            if method:
                data[field] = method(response)
            else:
                self.logger.warning(f"No se encontró el método {method_name} para el campo {field}")
        yield data

    # Métodos por defecto (pueden ser sobrescritos en subclases)
    def parse_product_menu_name(self, response):
        return response.meta.get('menu_name')

    def parse_product_menu_url(self, response):
        return response.meta.get('menu_url')

    def parse_product_url(self, response):
        return response.url

    def parse_product_name(self, response):
        return response.xpath(self.XPATH_PRODUCT_NAME).get()

    def parse_product_price(self, response):
        raw_price = response.xpath(self.XPATH_PRODUCT_PRICE).get()
        if raw_price:
            return float(raw_price.replace('$', '').replace('.', '').strip())
        return None

    def parse_product_images(self, response):
        return response.xpath(self.XPATH_PRODUCT_IMAGES).getall()

    def parse_product_description(self, response):
        return response.xpath(self.XPATH_PRODUCT_DESCRIPTION).get()

    def parse_product_category_name(self, response):
        breadcrumb = response.xpath(self.XPATH_BREADCRUMB_LAST)
        return breadcrumb.xpath('normalize-space(string())').get()

    def parse_product_category_url(self, response):
        breadcrumb = response.xpath(self.XPATH_BREADCRUMB_LAST)
        return breadcrumb.xpath('./@href').get()

    def on_feed_exporter_closed(self):
        """
        Se ejecuta cuando el archivo de feed (json) fue cerrado y está listo para ser leído.
        """
        self.logger.info(f"Feed exportado: {self.output_filename}")

    def close(self, reason):
        self.logger.info(f"Spider {self.name} finalizado. Motivo: {reason}")
        # No llamar a handle_publish aquí, se hace en on_feed_exporter_closed
