from .motodelta import MotodeltaSpider
import scrapy

class MotosportSpider(MotodeltaSpider):
    """
    Spider optimizado para motosport.com.ar con configuraciones anti-bot
    y manejo robusto de errores 403.
    """
    name = "motosport"
    allowed_domains = ["motosport.com.ar"]
    start_urls = ["https://motosport.com.ar"]
    
    # URLs a ignorar (convertido a set para optimización)
    ignored_urls = {
        "/categoria/motos/",  # Categoría sin productos
    }
    
    # Configuración anti-bot optimizada
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'motorciclye.middlewares.RotateUserAgentMiddleware': 400,
            'motorciclye.middlewares.RefererMiddleware': 410,
        }
    }

    SOURCE_INFO_URL = None  # Si la info de la fuente está en otra URL, pon aquí el path relativo o None (ej: "/contacto")

    # XPATHS como atributos de clase
    XPATH_MENU_ITEMS = '//*[@id="masthead"]/div/div[3]/ul/li'
    XPATH_SUBMENU = None
    XPATH_MENU_LINK = './a'
    XPATH_MENU_LINK_HREF = './@href'
    XPATH_MENU_LINK_TEXT = 'normalize-space(string())'
    XPATH_SUB_LINKS = None
    XPATH_PRODUCT_LINKS = '//*[@id="main"]/div/div[1]/div/div[3]/div/div/div[2]/div[1]/div[1]/a/@href'
    XPATH_NEXT_PAGE = '//*[@id="main"]/div/div[1]/div/div[4]/nav/ul/li[9]/a/@href'
    XPATH_PRODUCT_NAME = '//h1/text()'
    XPATH_PRODUCT_PRICE = '//*[@class="price-wrapper"]/p//span[@class="woocommerce-Price-amount amount"]/bdi/text()'
    XPATH_PRODUCT_IMAGES = '//img[@class="wp-post-image ux-skip-lazy"]/@src'
    XPATH_PRODUCT_DESCRIPTION = '//div[@class="product-short-description"]/p/text()'
    XPATH_PRODUCT_BRAND = None
    XPATH_PRODUCT_ATTRS = '//*[@id="accordion-additional_information-content"]/table//tr[th and td]'
    XPATH_PRODUCT_ATTRS_KEY = './/th//text()'
    XPATH_PRODUCT_ATTRS_VALUE = './/td/p/text()'
    XPATH_BREADCRUMB_LAST = None
    XPATH_PRODUCT_DISCOUNT_TEXT = '/html/body/div[1]/main/div/div[3]/div/section/div[2]/div[2]/div/div/div[1]/div/div[1]/div[1]/div/div/span/text()'
    XPATH_PRODUCT_PAYMENTS = '//div[@class="text text-promo"]/ul/li'
    HANDLE_PAGINATION = True  # Habilitar paginación por defecto

    XPATH_SOURCE_IMG_LOGO = '//*[@id="logo"]/a/img[1]/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="col-2083106921"]/div/div[2]/text()'
    XPATH_SOURCE_FB = '//*[@id="col-1623850890"]/div/div/a[1]/@href'
    XPATH_SOURCE_IG = '//*[@id="col-1623850890"]/div/div/a[2]/@href'
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="col-783333030"]/div/div/div[2]/a/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="col-1623850890"]/div/div/a[3]/@href'
    XPATH_SOURCE_WS = '//*[@id="col-783333030"]/div/div/div[2]/a/text()'
    XPATH_BUSINESS_HOURS_TEXT = None


    def parse(self, response):
        """
        Parse optimizado con validaciones robustas y logging mejorado.
        """
        # Verificar si la URL actual debe ser ignorada
        if self.should_ignore_url(response.url):
            self.logger.info(f"Ignorando URL: {response.url}")
            return
        
        # Validaciones de respuesta
        if not self._is_valid_response(response):
            return
            
        # Log de éxito con emoji (manejado en logger)
        self.logger.info(f"Respuesta exitosa de {response.url} - Tamaño: {len(response.body)} bytes")
        
        # Continuar con el parse normal del spider padre
        return super().parse(response)
    
    def _is_valid_response(self, response) -> bool:
        """Valida que la respuesta sea procesable"""
        if response.status != 200:
            self.logger.warning(f"Código de estado no exitoso: {response.status} para {response.url}")
            return False
            
        content_type = response.headers.get('content-type', b'').decode('utf-8').lower()
        if 'text/html' not in content_type:
            self.logger.warning(f"Contenido no es HTML: {content_type} para {response.url}")
            return False
            
        return True
        
    def parse_product_price(self, response):
        """Parse de precio optimizado para motosport"""
        raw_prices = self.safe_xpath_getall(response, self.XPATH_PRODUCT_PRICE)
        if raw_prices:
            # Tomar el último precio (generalmente el más relevante)
            last_price = raw_prices[-1]
            return self.clean_price(last_price)
        return None
    
    def parse_product_category_name(self, response):
        """Obtiene el nombre de categoría desde los metadatos"""
        return response.meta.get('menu_name')
    
    def start_requests(self):
        """Generar requests iniciales con headers anti-bot optimizados"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=headers,
                meta={
                    'dont_cache': True,  # No usar cache para el primer request
                }
            )