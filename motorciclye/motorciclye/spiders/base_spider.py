import os
import scrapy
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from ..logger import get_logger
from scrapy import signals

class BaseSpider(scrapy.Spider):
    """
    Spider base optimizado con funcionalidades comunes para todos los spiders.
    
    Características:
    - Configuración automática de directorios y logs
    - Extracción de datos con XPaths configurables
    - Manejo robusto de errores y URLs ignoradas
    - Métodos helpers para parsing optimizado
    """
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
    XPATH_PRODUCT_BRAND = None
    XPATH_PRODUCT_ATTRS = None
    XPATH_PRODUCT_ATTRS_KEY = None
    XPATH_PRODUCT_ATTRS_VALUE = None
    XPATH_PRODUCT_DISCOUNT_TEXT = None
    XPATH_PRODUCT_STOCK = None
    XPATH_PRODUCT_PAYMENTS = None
    XPATH_BREADCRUMB_LAST = None
    HANDLE_PAGINATION = True  # Habilitar paginación por defecto

    # URLs a ignorar (optimizado con set para O(1) lookup)
    ignored_urls = set()
    
    def should_ignore_url(self, url: str) -> bool:
        """Verifica si una URL debe ser ignorada usando búsqueda optimizada"""
        return any(ignored in url for ignored in self.ignored_urls)


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
        'brand': 'parse_product_brand',
        'attrs': 'parse_product_attrs',
        'discount': 'parse_product_discount_text',
        'category_url': 'parse_product_category_url',
        'stock': 'parse_product_stock',
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
        """
        Extrae todos los campos de un producto usando el mapeo de métodos.
        Optimizado para manejo de errores y logging.
        """
        self.logger.info(f"Parseando producto: {response.url}")
        data = {'source': self.name}  # Agregar source por defecto
        
        for field, method_name in self.product_field_mapping.items():
            try:
                method = getattr(self, method_name, None)
                if method:
                    value = method(response)
                    if value is not None:  # Solo agregar valores no None
                        data[field] = value
                else:
                    self.logger.debug(f"Método {method_name} no implementado para {field}")
            except Exception as e:
                self.logger.warning(f"Error extrayendo {field} con {method_name}: {e}")
                
        yield data

    def safe_xpath_get(self, response, xpath: str, default: Any = None) -> Any:
        """Helper para extraer valores XPath con manejo de errores"""
        try:
            return response.xpath(xpath).get() if xpath else default
        except Exception as e:
            self.logger.debug(f"Error en XPath {xpath}: {e}")
            return default
    
    def safe_xpath_getall(self, response, xpath: str, default: List = None) -> List:
        """Helper para extraer listas XPath con manejo de errores"""
        try:
            return response.xpath(xpath).getall() if xpath else (default or [])
        except Exception as e:
            self.logger.debug(f"Error en XPath {xpath}: {e}")
            return default or []
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Limpia y convierte texto de precio a float"""
        if not price_text:
            return None
        try:
            # Remover caracteres no numéricos excepto punto y coma
            cleaned = re.sub(r'[^\d.,]', '', price_text.strip())
            # Reemplazar coma por punto para decimales
            cleaned = cleaned.replace(',', '.')
            # Si hay múltiples puntos, mantener solo el último como decimal
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            self.logger.debug(f"No se pudo convertir precio: {price_text}")
            return None

    # Métodos por defecto optimizados (pueden ser sobrescritos en subclases)
    def parse_product_menu_name(self, response):
        return response.meta.get('menu_name')

    def parse_product_menu_url(self, response):
        return response.meta.get('menu_url')

    def parse_product_url(self, response):
        return response.url

    def parse_product_name(self, response):
        return self.safe_xpath_get(response, self.XPATH_PRODUCT_NAME)

    def parse_product_price(self, response):
        raw_price = self.safe_xpath_get(response, self.XPATH_PRODUCT_PRICE)
        return self.clean_price(raw_price)

    def parse_product_images(self, response):
        return self.safe_xpath_getall(response, self.XPATH_PRODUCT_IMAGES)

    def parse_product_brand(self, response):
        return self.safe_xpath_get(response, self.XPATH_PRODUCT_BRAND)
    
    def parse_product_attrs(self, response):
        return self.safe_xpath_getall(response, self.XPATH_PRODUCT_ATTRS)

    def parse_product_discount_text(self, response):
        return self.safe_xpath_get(response, self.XPATH_PRODUCT_DISCOUNT_TEXT)
    
    def parse_product_stock(self, response):
        return self.safe_xpath_get(response, self.XPATH_PRODUCT_STOCK)
    
    def parse_product_payments(self, response):
        payments_text = []
        if self.XPATH_PRODUCT_PAYMENTS:
            try:
                for payment in response.xpath(self.XPATH_PRODUCT_PAYMENTS):
                    payment_text = payment.xpath('string(.)').get()
                    if payment_text and payment_text.strip():
                        payments_text.append(payment_text.strip())
            except Exception as e:
                self.logger.debug(f"Error extrayendo pagos: {e}")
        return payments_text or None

    def parse_product_description(self, response):
        return self.safe_xpath_get(response, self.XPATH_PRODUCT_DESCRIPTION)

    def parse_product_category_name(self, response):
        if not self.XPATH_BREADCRUMB_LAST:
            return None
        try:
            breadcrumb = response.xpath(self.XPATH_BREADCRUMB_LAST)
            if breadcrumb:
                return breadcrumb.xpath('normalize-space(string())').get()
        except Exception as e:
            self.logger.debug(f"Error extrayendo categoría: {e}")
        return None

    def parse_product_category_url(self, response):
        if not self.XPATH_BREADCRUMB_LAST:
            return None
        try:
            breadcrumb = response.xpath(self.XPATH_BREADCRUMB_LAST)
            if breadcrumb:
                return breadcrumb.xpath('./@href').get()
        except Exception as e:
            self.logger.debug(f"Error extrayendo URL categoría: {e}")
        return None

    def on_feed_exporter_closed(self):
        """
        Se ejecuta cuando el archivo de feed (json) fue cerrado y está listo para ser leído.
        """
        self.logger.info(f"Feed exportado: {self.output_filename}")

    def close(self, reason):
        self.logger.info(f"Spider {self.name} finalizado. Motivo: {reason}")
        # No llamar a handle_publish aquí, se hace en on_feed_exporter_closed
