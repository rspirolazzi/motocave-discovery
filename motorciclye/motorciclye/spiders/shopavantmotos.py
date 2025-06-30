from .gaonamotos import GaonamotosSpider

class ShopavantmotosSpider(GaonamotosSpider):
    name = "shopavantmotos"
    allowed_domains = ["shopavantmotos.com.ar"]
    start_urls = ["https://shopavantmotos.com.ar"]
