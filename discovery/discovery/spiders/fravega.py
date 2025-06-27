import scrapy


class FravegaSpider(scrapy.Spider):
    name = "fravega"
    allowed_domains = ["fravega.com.ar"]
    start_urls = ["https://fravega.com.ar"]

    def parse(self, response):
        pass
