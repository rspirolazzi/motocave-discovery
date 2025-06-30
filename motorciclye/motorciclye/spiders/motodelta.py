from urllib import response
import scrapy
from scrapy_selenium import SeleniumRequest
from .base_spider import BaseSpider

class MotodeltaSpider(BaseSpider):
    source_parsed = False  # Inicializar la fuente como None
    name = "motodelta"
    allowed_domains = ["www.motodelta.com.ar"]
    start_urls = ["https://www.motodelta.com.ar"]
    SOURCE_INFO_URL = None  # Si la info de la fuente está en otra URL, pon aquí el path relativo o None (ej: "/contacto")

    # XPATHS como atributos de clase
    XPATH_MENU_ITEMS = '//ul[@id="nav-list"]/li[contains(@class, "nav-list__item")]'
    XPATH_SUBMENU = './/ul[contains(@class, "nav-list__item-subcategory") or contains(@class, "nav-modern-list--vertical__attribute_container") or contains(@class, "grid-list")]'
    XPATH_MENU_LINK = './a[@class="nav-list__link"]'
    XPATH_MENU_LINK_HREF = './@href'
    XPATH_MENU_LINK_TEXT = 'normalize-space(string())'
    XPATH_SUB_LINKS = './/a'
    XPATH_PRODUCT_LINKS = '//*[@id="root-app"]/div/div[2]/section/ol/li//div[@class="poly-card__content"]/a/@href'
    XPATH_NEXT_PAGE = '//*[@id="root-app"]/div/div[2]/section/nav//li[contains(@class, "andes-pagination__button--next")]/a/@href'
    XPATH_PRODUCT_NAME = '//h1/text()'
    XPATH_PRODUCT_PRICE = '//*[@id="price"]/div/div[1]/div[1]/span/span/span[2]/text()'
    XPATH_PRODUCT_IMAGES = '//div//img/@data-zoom'
    XPATH_PRODUCT_DESCRIPTION = '//*[@class="ui-pdp-description__content"]/text()'
    XPATH_PRODUCT_BRAND = '//table//tr[th[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "marca")]]/td//span[@class="andes-table__column--value"]/text()'
    XPATH_PRODUCT_ATTRS = None
    XPATH_BREADCRUMB_LAST = '//*[contains(@class, "andes-breadcrumb")]//li[last()]/a'
    HANDLE_PAGINATION = True  # Habilitar paginación por defecto

    XPATH_SOURCE_IMG_LOGO = '//*[@id="image-logo"]/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="shop-address-link"]/span/text()'
    XPATH_SOURCE_FB = '//*[@id="footer-container"]/footer/div[1]/div[2]/div[1]/div[1]/a[1]/@href'
    XPATH_SOURCE_IG = '//*[@id="footer-container"]/footer/div[1]/div[2]/div[1]/div[1]/a[2]/@href'
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="shop-phone-link"]/span/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="shop-mail-link"]/span/text()'
    XPATH_SOURCE_WS = None
    XPATH_BUSINESS_HOURS_TEXT = None


    def start_requests(self):
        # Si SOURCE_INFO_URL está definido, primero parsea la fuente desde esa URL
        if self.SOURCE_INFO_URL:
            yield SeleniumRequest(
                url=self.start_urls[0] + self.SOURCE_INFO_URL,
                callback=self.parse_source_and_continue
            )
        else:
            yield SeleniumRequest(url=self.start_urls[0], callback=self.parse)

    def parse_source_and_continue(self, response):
        # Parseamos la fuente y hacemos yield del item para el pipeline
        for item in self.parse_source(response):
            yield item
        
        # Luego de parsear la fuente, sigue con el parseo normal del menú
        yield SeleniumRequest(url=self.start_urls[0], callback=self.parse)

    def parse_source(self, response):
        self.logger.info(f"Parseando fuente {self.name}: {response.url}")
        try:
            name = self.name
            logo = response.xpath(self.XPATH_SOURCE_IMG_LOGO).get() if self.XPATH_SOURCE_IMG_LOGO else None
            address = ' '.join(response.xpath(self.XPATH_SOURCE_ADDRESS).getall()) if self.XPATH_SOURCE_ADDRESS else None
            fb = response.xpath(self.XPATH_SOURCE_FB).get() if self.XPATH_SOURCE_FB else None
            ig = response.xpath(self.XPATH_SOURCE_IG).get() if self.XPATH_SOURCE_IG else None
            x = response.xpath(self.XPATH_SOURCE_X).get() if self.XPATH_SOURCE_X else None
            phone = response.xpath(self.XPATH_SOURCE_PHONE).get() if self.XPATH_SOURCE_PHONE else None
            email = response.xpath(self.XPATH_SOURCE_EMAIL).get() if self.XPATH_SOURCE_EMAIL else None
            ws = response.xpath(self.XPATH_SOURCE_WS).get() if self.XPATH_SOURCE_WS else None
            business_hours_text = response.xpath(self.XPATH_BUSINESS_HOURS_TEXT).get() if self.XPATH_BUSINESS_HOURS_TEXT else None

            source = {
                'source_url': response.url,
                'name': name,
                'address': address,
                'logo': logo,
                'contact_methods': {
                    'fb': fb,
                    'ig': ig,
                    'x': x,
                    'phone': phone,
                    'email': email,
                    'ws': ws,
                    'business_hours': business_hours_text
                }
            }
            
            # Crear un item para el pipeline con el tipo 'source'
            source_item = dict(source)
            source_item['item_type'] = 'source'
            self.source_parsed = True            
            # Enviar al pipeline para procesamiento
            yield source_item
        except Exception as e:
            self.logger.error(f"Error al parsear fuente: {response.url} - {e}")
            raise scrapy.exceptions.CloseSpider(f"Error al parsear fuente: {response.url} - {e}")

    def parse(self, response):
        # Verificar si la URL actual debe ser ignorada
        if self.should_ignore_url(response.url):
            self.logger.info(f"Ignorando URL: {response.url}")
            return
        
        # Solo parsea la fuente si no se parseó antes (es decir, si no se usó SOURCE_INFO_URL)
        if not self.source_parsed:
            # Parseamos la fuente y hacemos yield del item para el pipeline
            for item in self.parse_source(response):
                yield item
        
        self.logger.info(f"Parseando menú principal: {response.url}")
        # Selecciona los items del menú principal
        menu_items = response.xpath(self.XPATH_MENU_ITEMS)
        for item in menu_items:
            submenu = item.xpath(self.XPATH_SUBMENU) if self.XPATH_SUBMENU else []
            link = item.xpath(self.XPATH_MENU_LINK)
            href = link.xpath(self.XPATH_MENU_LINK_HREF).get()
            name = link.xpath(self.XPATH_MENU_LINK_TEXT).get()
            # Si tiene submenús, recorrer los submenús
            if submenu:
                sub_links = submenu.xpath(self.XPATH_SUB_LINKS)
                for sub in sub_links:
                    sub_href = sub.xpath(self.XPATH_MENU_LINK_HREF).get()
                    sub_name = sub.xpath(self.XPATH_MENU_LINK_TEXT).get()
                    if sub_href:
                        self.logger.info(f"Submenú: {sub_name} - {sub_href}")
                        yield scrapy.Request(
                            url=response.urljoin(sub_href),
                            callback=self.parse_list_of_products,
                            meta={'menu_name': sub_name, 'menu_url': response.urljoin(sub_href)}
                        )
            # Si no tiene submenús, ingresar al menú
            elif href:
                self.logger.info(f"Menú sin submenú: {name} - {href}")
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_list_of_products,
                    meta={'menu_name': name, 'menu_url': response.urljoin(href)}
                )

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

    def parse_product_attrs(self, response):
        """Extrae todos los atributos de la tabla de especificaciones"""
        if not self.XPATH_PRODUCT_ATTRS:
            # Si no hay XPATH específico, extraer toda la tabla
            attrs = {}
            rows = response.xpath('//table[@class="andes-table"]//tr[th and td]')
            for row in rows:
                key = row.xpath('.//th//text()').get()
                value = row.xpath('.//td//span[@class="andes-table__column--value"]/text()').get()
                if key and value:
                    attrs[key.strip()] = value.strip()
            return attrs
        else:
            return response.xpath(self.XPATH_PRODUCT_ATTRS).getall() if self.XPATH_PRODUCT_ATTRS else []

    def parse_product_brand(self, response):
        """Extrae la marca del producto desde la tabla de especificaciones"""
        brand = self.parse_product_attrs(response).get('Marca')
        if brand:
            return brand.strip()
        return None

    def parse_product(self, response):
        try:
            self.logger.info(f"Parseando producto: {response.url}")
            name = self.parse_product_name(response)
            price = self.parse_product_price(response)
            images = self.parse_product_images(response)
            description = self.parse_product_description(response)
            attrs = self.parse_product_attrs(response)
            brand = self.parse_product_brand(response)
            discount_text = self.parse_product_discount_text(response)
            payments = self.parse_product_payments(response)

            menu_name = response.meta.get('menu_name')
            menu_url = response.meta.get('menu_url')
            self.logger.debug(f"Extraído: name={name}, price={price}, images={len(images)} imágenes")

            # Extraer la categoría del último breadcrumb
            category_name = self.parse_product_category_name(response)
            category_url = self.parse_product_category_url(response)

            product = {
                'item_type': 'product',
                'menu_name': menu_name,
                'menu_url': menu_url,
                'product_url': response.url,
                'name': name,
                'price': price,
                'brand': brand,
                'attrs': attrs,
                'payments': payments,
                'discount_text': discount_text,
                'images': images,
                'description': description,
                'category_name': category_name,
                'category_url': category_url,
                'source': self.source_parsed,
            }
            yield product
        except Exception as e:
            self.logger.error(f"Error al parsear producto: {response.url} - {e}")
            raise scrapy.exceptions.CloseSpider(f"Error al parsear producto: {response.url} - {e}")
