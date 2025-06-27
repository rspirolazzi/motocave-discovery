from motorciclye.spiders.motodelta import MotodeltaSpider
class MotomercadoSpider(MotodeltaSpider):
    name = "motomercado"
    allowed_domains = ["motomercado.com.ar"]
    start_urls = ["https://motomercado.com.ar"]

    XPATH_MENU_ITEMS='/html/body/header/div[3]/div/div[1]/div/ul/li'
    XPATH_SUBMENU = './/ul'
    XPATH_MENU_LINK = './div/a'
    XPATH_PRODUCT_LINKS = '/html/body/section[3]/div/div/div[2]/div[1]/div/div/div/div[1]/div/a/@href'
    XPATH_NEXT_PAGE = '//div[@class="NONE"]'
    HANDLE_PAGINATION = False
    XPATH_PRODUCT_NAME = '//h1/text()'
    XPATH_PRODUCT_PRICE = '//*[@id="price_display"]/text()'
    XPATH_PRODUCT_IMAGES = '//*[@id="single-product"]/div[1]/div/div[1]/div/div[2]/div[1]/div[2]//a/img[1]/@src'
    XPATH_PRODUCT_DESCRIPTION = '//*[@id="single-product"]/div[2]/div/div[1]/div[1]/p[1]/text()'
    XPATH_BREADCRUMB_LAST = '//*[@id="single-product"]/div[1]/div/div[2]/div[1]/section/div/a[last()]'

    def parse_product_price(self, response):
        raw_price = response.xpath(self.XPATH_PRODUCT_PRICE).get()
        if raw_price:
            return float(raw_price
                         .replace('$', '')
                         .replace('.', '')
                         .replace(',', '.')
                         .strip())
        return None
    
    def parse_product_images(self, response):
        return list(map(lambda x: response.urljoin(x), response.xpath(self.XPATH_PRODUCT_IMAGES).getall()))
