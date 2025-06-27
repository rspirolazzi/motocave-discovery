from .motodelta import MotodeltaSpider
import scrapy

class GaonamotosSpider(MotodeltaSpider):
    name = "gaonamotos"
    allowed_domains = ["gaonamotos.com"]
    start_urls = ["https://gaonamotos.com"]

    # XPATHS como atributos de clase
    XPATH_MENU_ITEMS = '//*[@id="nav-list"]/li'
    XPATH_MENU_LINK = './a'
    XPATH_SUBMENU = '//*[@id="nav-popover-list"]//li'
    XPATH_NEXT_PAGE = '//*[@id="root-app"]/div/div[2]/section/nav//li[contains(@class, "andes-pagination__button--next")]/a/@href'

    XPATH_SOURCE_IMG_LOGO = '//*[@id="logo-wrapper"]/img/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[3]/a/text()'
    XPATH_SOURCE_FB = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/div/a[1]/@href'
    XPATH_SOURCE_IG = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/div/a[2]/@href'
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[1]/a/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[2]/a/text()'
    XPATH_SOURCE_WS = None


    def parse(self, response):
        # Solo parsea la fuente si no se parseó antes (es decir, si no se usó SOURCE_INFO_URL)
        if not self.source_parsed:
            # Parseamos la fuente y hacemos yield del item para el pipeline
            for item in self.parse_source(response):
                yield item
        self.logger.info(f"Parseando menú principal: {response.url}")
        # Selecciona los items del menú principal
        menu_items = response.xpath(self.XPATH_MENU_ITEMS)
        another_menu = response.xpath(self.XPATH_SUBMENU)

        menus = menu_items + another_menu

        for item in menus:
            link = item.xpath(self.XPATH_MENU_LINK)
            href = link.xpath(self.XPATH_MENU_LINK_HREF).get()
            name = link.xpath(self.XPATH_MENU_LINK_TEXT).get()
            # Si tiene submenús, recorrer los submenús
            if href:
                self.logger.info(f"Menú sin submenú: {name} - {href}")
                yield scrapy.Request(
                    url=response.urljoin(href),
                    callback=self.parse_list_of_products,
                    meta={'menu_name': name, 'menu_url': response.urljoin(href)}
                )