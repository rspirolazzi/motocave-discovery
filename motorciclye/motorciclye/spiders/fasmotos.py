from motorciclye.spiders.motodelta import MotodeltaSpider
from scrapy_selenium import SeleniumRequest
import scrapy

class FasmotosSpider(MotodeltaSpider):
    """Spider optimizado para fasmotos.com.ar con debugging mejorado"""
    name = "fasmotos"
    allowed_domains = ["fasmotos.com.ar"]
    
    # URLs específicas para cada categoría
    start_urls = [
        {
            "menu_name": "Cubiertas",
            "menu_url": "https://www.fasmotos.com.ar/listado/accesorios-vehiculos/neumaticos/cubiertas-motos/"
        },
        {
            "menu_name": "Cascos",
            "menu_url": "https://www.fasmotos.com.ar/listado/accesorios-vehiculos/acc-motos-cuatriciclos/cascos/"
        },
        {
            "menu_name": "Indumentaria",
            "menu_url": "https://www.fasmotos.com.ar/listado/ropa-accesorios/"
        },
        {
            "menu_name": "Repuestos y Accesorios",
            "menu_url": "https://www.fasmotos.com.ar/listado/accesorios-vehiculos/repuestos-motos-cuatriciclos/"
        }
    ]

    # XPaths configurados para fasmotos
    XPATH_MENU_ITEMS = '//*[@id="sidebar-menu-list"]/ul/li'
    XPATH_MENU_LINK = './a'
    XPATH_SUBMENU = './ul/li'
    XPATH_SUB_LINKS = './a'
    XPATH_PRODUCT_LINKS = '//a[contains(@class, "poly-component__title")]/@href'
    XPATH_PRODUCT_NAME = '//h1/text()'
    XPATH_PRODUCT_PRICE = '//*[@id="price"]/div/div[1]/div[1]/span[1]/span/span[2]/text()'
    XPATH_PRODUCT_IMAGES = '//img[@data-zoom]/@data-zoom'
    XPATH_PRODUCT_DESCRIPTION = '//*[@id="ui-vpp-highlighted-specs"]'
    XPATH_PRODUCT_DISCOUNT_TEXT = '//*[@id="pills"]/div/div/p/span/text()'
    XPATH_PRODUCT_PAYMENTS = '//*[@id="pricing_price_subtitle"]'

    HANDLE_PAGINATION = False  # Deshabilitar paginación

    def safe_log(self, message, level='info'):
        """Safe logging method that handles Unicode characters"""
        try:
            # Remove or replace problematic Unicode characters
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            if hasattr(self.logger, level):
                getattr(self.logger, level)(safe_message)
            else:
                self.logger.info(safe_message)
        except Exception as e:
            # Fallback: log without Unicode
            fallback_msg = f"[Unicode Error] {str(e)}"
            self.logger.info(fallback_msg)

    def start_requests(self):
        """Generar requests con Selenium y debugging habilitado"""
        for option in self.start_urls:
            url = option.get('menu_url')
            menu_name = option.get('menu_name')
            
            self.safe_log(f"DEBUG: Requesting URL: {url} para categoria: {menu_name}")
            
            yield SeleniumRequest(
                url=url,
                callback=self.parse_list_of_products,  # Use normal parse method now
                meta={
                    'menu_name': menu_name,
                    'menu_url': url,
                    'selenium_debug': True
                },
                wait_time=5  # Esperar 5 segundos para que cargue JavaScript
            )

    def parse_list_of_products_debug(self, response):
        """Parse con debugging detallado para diagnosticar problemas"""
        self.logger.info(f"DEBUG parse_list_of_products para: {response.url}")
        
        # 1. Información básica de la respuesta
        self.logger.info(f"Status: {response.status}")
        self.logger.info(f"Content-Type: {response.headers.get('content-type', b'').decode('utf-8')}")
        self.logger.info(f"Body length: {len(response.body)} bytes")
        
        # 2. Verificar si es contenido HTML válido
        if 'text/html' not in response.headers.get('content-type', b'').decode('utf-8').lower():
            self.logger.warning(f"WARNING: La respuesta no es HTML: {response.headers.get('content-type')}")
            return
        
        # 3. Buscar el XPath específico
        product_links = response.xpath(self.XPATH_PRODUCT_LINKS).getall()
        self.safe_log(f"XPATH_PRODUCT_LINKS encontro: {len(product_links)} links")
        
        if not product_links:
            # 4. Debugging alternativo: probar XPaths similares
            self.debug_alternative_xpaths(response)
            
            # 5. Guardar HTML para inspección manual
            self.save_debug_html(response)
            
            # 6. Buscar patrones comunes
            self.search_common_patterns(response)
        else:
            self.safe_log(f"Productos encontrados: {product_links[:3]}...")  # Mostrar primeros 3
        
        # Continuar con el parsing normal
        return self.parse_list_of_products(response)

    def debug_alternative_xpaths(self, response):
        """Prueba XPaths alternativos para encontrar productos"""
        self.logger.info("Probando XPaths alternativos...")
        
        alternative_xpaths = [
            "//a[contains(@class, 'poly-component__title')]/@href",  # Product links with correct class
            "//a[contains(@href, '/MLA-')]/@href",  # Links típicos de MercadoLibre
            "//ol/li//a/@href",  # Lista ordenada con enlaces
            "//div[@class='ui-search-results']//a/@href",  # Resultados de búsqueda
            "//section//a[contains(@href, 'MLA')]/@href",  # Enlaces en sección
            "//li[contains(@class, 'ui-search-layout')]//a/@href",  # Items de layout
            "//a[contains(@class, 'ui-search-link')]/@href",  # Enlaces de búsqueda
        ]
        
        for i, xpath in enumerate(alternative_xpaths, 1):
            try:
                results = response.xpath(xpath).getall()
                self.logger.info(f"  {i}. {xpath} -> {len(results)} resultados")
                if results:
                    self.logger.info(f"     Ejemplo: {results[0]}")
            except Exception as e:
                self.logger.info(f"  {i}. {xpath} -> Error: {e}")

    def save_debug_html(self, response):
        """Guarda el HTML para inspección manual"""
        try:
            # Crear archivo de debug en el directorio build
            debug_filename = f"debug_fasmotos_{response.meta.get('menu_name', 'unknown')}.html"
            debug_path = f"build/fasmotos/debug_{debug_filename}"
            
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.logger.info(f"HTML guardado para inspección: {debug_path}")
        except Exception as e:
            self.logger.warning(f"No se pudo guardar HTML debug: {e}")

    def search_common_patterns(self, response):
        """Busca patrones comunes en el HTML"""
        self.logger.info("Buscando patrones comunes...")
        
        # Buscar elementos que podrían contener productos
        patterns = {
            "Links con MLA": "//a[contains(@href, 'MLA')]",
            "Elements con 'product'": "//*[contains(@class, 'product') or contains(@id, 'product')]",
            "Elements con 'item'": "//*[contains(@class, 'item') or contains(@id, 'item')]",
            "Links en listas": "//li//a[@href]",
            "Imágenes de productos": "//img[contains(@alt, 'producto') or contains(@src, 'product')]",
        }
        
        for pattern_name, xpath in patterns.items():
            try:
                count = len(response.xpath(xpath))
                self.logger.info(f"  {pattern_name}: {count} elementos")
            except Exception as e:
                self.logger.info(f"  {pattern_name}: Error - {e}")

    def parse_product_description(self, response):
        """Parse optimizado de descripción con debugging"""
        description_element = response.xpath(self.XPATH_PRODUCT_DESCRIPTION)
        if description_element:
            description_text = '\r'.join(description_element.xpath('string(.)').getall())
            return description_text if description_text.strip() else None
        return None
