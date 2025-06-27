from .motodelta import MotodeltaSpider

class MasxmotoSpider(MotodeltaSpider):
    name = "masxmoto"
    allowed_domains = ["masxmoto.com.ar"]
    start_urls = ["https://masxmoto.com.ar"]

    XPATH_MENU_ITEMS = '//*[@id="responsive-menu"]/ul/li'
    XPATH_MENU_LINK = './a'
    XPATH_SUBMENU = '//div[@class="none"]'
    HANDLE_PAGINATION = False  # Deshabilitar paginación por defecto

    XPATH_SOURCE_IMG_LOGO = '//*[@id="logo-wrapper"]/img/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[3]/a/text()'
    XPATH_SOURCE_FB = None
    XPATH_SOURCE_IG = None
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[1]/a/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="footer-container"]/footer/div[1]/div/div/div[6]/ul/li[2]/a/text()'
    XPATH_SOURCE_WS = None

    def parse_product_description(self, response):
        return '\r'.join(response.xpath(self.XPATH_PRODUCT_DESCRIPTION).getall())
