import scrapy
from .motodelta import MotodeltaSpider

class MotojoseSpider(MotodeltaSpider):
    """Spider optimizado para motojose.com.ar con extracción mejorada"""
    name = "motojose"
    allowed_domains = ["motojose.com.ar"]
    start_urls = ["https://motojose.com.ar"]


    XPATH_MENU_ITEMS = '//*[@id="mainNav"]/li[2]/ul//a'
    XPATH_MENU_LINK_HREF = './@href'
    XPATH_MENU_LINK_TEXT = 'normalize-space(string())'
    XPATH_PRODUCT_LINKS = '/html/body/div[3]/div/div/div[2]/div[2]/div[1]/div/span/a[2]/@href'
    XPATH_NEXT_PAGE = None
    XPATH_PRODUCT_NAME = '//h1/text()'
    XPATH_PRODUCT_PRICE = '/html/body/div[3]/div/div/div[2]/div/div[2]/div/p[1]/span/text()'
    XPATH_PRODUCT_IMAGES = '//div[@class="owl-carousel owl-theme"]//img/@src'
    XPATH_PRODUCT_DESCRIPTION = '/html/body/div[3]/div/div/div[2]/div/div[2]/div/p[2]/text()'
    XPATH_BREADCRUMB_LAST = '/html/body/div[3]/div/div/div[2]/div/div[2]/div/div[2]/span/a[last()]'
    HANDLE_PAGINATION = False  # Deshabilitar paginación para este sitio

    XPATH_SOURCE_IMG_LOGO = '//*[@id="header"]/div/div/div/div[1]/div/div/a/img/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="footer"]/div[1]/div/div[4]/ul[1]/li/p/text()'
    XPATH_SOURCE_FB = None
    XPATH_SOURCE_IG = None
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="footer"]/div[1]/div/div[3]/ul/li[2]/p/a/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="footer"]/div[1]/div/div[3]/ul/li[3]/p/a/@href'
    XPATH_SOURCE_WS = '//*[@id="footer"]/div[1]/div/div[3]/ul/li[2]/p/a/@href'
    XPATH_BUSINESS_HOURS_TEXT = '//*[@id="footer"]/div[1]/div/div[4]/ul[2]/li/p/text()'

    def parse(self, response):
        # Solo parsea la fuente si no se parseó antes (es decir, si no se usó SOURCE_INFO_URL)
        if not self.source_parsed:
            # Parseamos la fuente y hacemos yield del item para el pipeline
            for item in self.parse_source(response):
                yield item
        self.logger.info(f"Parseando menú principal: {response.url}")
        menu_links = response.xpath(self.XPATH_MENU_ITEMS)
        for link in menu_links:
            href = link.xpath(self.XPATH_MENU_LINK_HREF).get()
            name = link.xpath(self.XPATH_MENU_LINK_TEXT).get()
            if href:
                self.logger.info(f"Menú: {name} - {href}")
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_list_of_products,
                    meta={'menu_name': name, 'menu_url': response.urljoin(href)}
                )

    def parse_product_description(self, response):
        """Extrae descripción concatenando múltiples elementos"""
        descriptions = self.safe_xpath_getall(response, self.XPATH_PRODUCT_DESCRIPTION)
        return '\r'.join(descriptions) if descriptions else None

    def parse_product_images(self, response):
        """Extrae imágenes y las convierte a URLs absolutas"""
        images = self.safe_xpath_getall(response, self.XPATH_PRODUCT_IMAGES)
        return [response.urljoin(img) for img in images] if images else None

    def parse_product_price(self, response):
        """Parse de precio que maneja casos especiales como 'consultar'"""
        price_text = self.safe_xpath_get(response, self.XPATH_PRODUCT_PRICE)
        if price_text and 'consultar' in price_text.lower():
            return None
        return self.clean_price(price_text)