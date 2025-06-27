from motorciclye.spiders.motodelta import MotodeltaSpider
from scrapy_selenium import SeleniumRequest
import scrapy

class FasmotosSpider(MotodeltaSpider):
    name = "fasmotos"
    allowed_domains = ["fasmotos.com.ar"]
    start_urls = [
        {
            "menu_name":"Cubiertas",
            "menu_url":"https://www.fasmotos.com.ar/listado/accesorios-vehiculos/neumaticos/cubiertas-motos/"
        },
        {
            "menu_name":"Cascos",
            "menu_url":"https://www.fasmotos.com.ar/listado/accesorios-vehiculos/acc-motos-cuatriciclos/cascos/"
        },
        {
            "menu_name":"Indumentaria",
            "menu_url":"https://www.fasmotos.com.ar/listado/ropa-accesorios/"
        },
        {
            "menu_name":"Repuestos y Accesorios",
            "menu_url":"https://www.fasmotos.com.ar/listado/accesorios-vehiculos/repuestos-motos-cuatriciclos/"
        }
        ]

    XPATH_MENU_ITEMS = '//*[@id="sidebar-menu-list"]/ul/li'
    XPATH_MENU_LINK = './a'
    XPATH_SUBMENU = './ul/li'
    XPATH_SUB_LINKS = './a'
    XPATH_PRODUCT_LINKS = '/html/body/main/div/div[2]/section/ol/li/div/div/div[1]/section/div[2]/div/div/div/a/@href'
    HANDLE_PAGINATION = False  # Deshabilitar paginación por defecto

    def start_requests(self):
        # Usar SeleniumRequest para poder interactuar con el DOM
        for opction in self.start_urls:
            self.logger.info(f"Requesting URL: {opction}")
            yield SeleniumRequest(url=opction.get('menu_url'), callback=self.parse_list_of_products,
                                  meta={
                        'menu_name': opction.get('menu_name'),
                        'menu_url': opction.get('menu_url')
                    })


    def parse_list_of_products(self, response):
        self.logger.info(f"Parseando listado de productos: {response.url}")
        # Captura las urls de productos del listado
        product_links = response.xpath(self.XPATH_PRODUCT_LINKS).getall()
        self.logger.info(f"Encontrados {len(product_links)} productos en {response.url}")
        for href in product_links:
            self.logger.debug(f"Producto encontrado: {href}")
            yield scrapy.Request(
                url=response.urljoin(href),
                callback=self.parse_product,
                meta={
                    'menu_name': response.meta.get('menu_name'),
                    'menu_url': response.meta.get('menu_url')
                }
            )
        # PAGINADO
        if self.HANDLE_PAGINATION:
            self.logger.info("Paginación habilitada, buscando más páginas.")
            next_page = response.xpath(self.XPATH_NEXT_PAGE).get()
            if next_page:
                self.logger.info(f"Siguiente página encontrada: {next_page}")
                yield scrapy.Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_list_of_products,
                    meta={
                        'menu_name': response.meta.get('menu_name'),
                        'menu_url': response.meta.get('menu_url')
                    }
                )


    def parse_product_description(self, response):
        return '\r'.join(response.xpath(self.XPATH_PRODUCT_DESCRIPTION).getall())
