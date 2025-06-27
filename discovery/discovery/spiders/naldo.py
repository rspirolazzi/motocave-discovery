import scrapy


class NaldoSpider(scrapy.Spider):
    name = "naldo"
    allowed_domains = ["naldo.com.ar"]
    start_urls = ["https://naldo.com.ar"]

    def parse(self, response):
        pass
