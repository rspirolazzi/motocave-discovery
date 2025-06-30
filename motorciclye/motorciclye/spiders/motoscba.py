import scrapy
from .gaonamotos import GaonamotosSpider

class MotoscbaSpider(GaonamotosSpider):
    name = "motoscba"
    allowed_domains = ["motoscba.com.ar"]
    start_urls = ["https://motoscba.com.ar"]

    # XPATHS como atributos de clase
    XPATH_NEXT_PAGE = '//*[@id="root-app"]/div/div[2]/section/nav//li[contains(@class, "andes-pagination__button--next")]/a/@href'

    XPATH_SOURCE_IMG_LOGO = '//*[@id="logo-wrapper"]/img/@src'
    XPATH_SOURCE_ADDRESS = '//*[@id="footer-container"]/footer/div[1]/div/div/div[8]/ul/li[3]/a/text()'
    XPATH_SOURCE_FB = '//*[@id="footer-container"]/footer/div[1]/div/div/div[8]/div/a[1]/@href'
    XPATH_SOURCE_IG = '//*[@id="footer-container"]/footer/div[1]/div/div/div[8]/div/a[2]/@href'
    XPATH_SOURCE_X = None
    XPATH_SOURCE_PHONE = '//*[@id="footer-container"]/footer/div[1]/div/div/div[8]/ul/li[1]/a/text()'
    XPATH_SOURCE_EMAIL = '//*[@id="footer-container"]/footer/div[1]/div/div/div[8]/ul/li[2]/a/text()'
    XPATH_SOURCE_WS = None
    XPATH_PRODUCT_DISCOUNT_TEXT = '//*[@id="pills"]/div/div/p/span/text()'

