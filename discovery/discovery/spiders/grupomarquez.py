from .rodo import RodoSpider
from scrapy_selenium import SeleniumRequest


class GrupomarquezSpider(RodoSpider):
    name = "grupomarquez"
    allowed_domains = ["grupomarquez.com.ar"]
    start_urls = ["https://grupomarquez.com.ar"]
    # Puedes sobreescribir XPATHs o métodos si es necesario para este sitio
    start_requests_url = "https://grupomarquez.com.ar"
    menu_xpath = '//*[@id="menu-width"]//a'
    product_link_xpath = '//*[@id="body"]/div/div/div[2]/div/div/div[2]/ul/li//a/@href'
    name_xpath = '//*[@id="body"]/div/div[3]/div[3]/h1/text()'
    price_xpath = '//*[@id="final_price"]/text()'
    images_xpath = '//*[@id="g_image"]//img/@src'
    brand_label = 'Marca'
    sku_label = 'SKU'
    attr_table_xpath = '//*[@id="tab-especs"]/div/div/div/table'
    ignore_urls = [
        # Agrega aquí las URLs (o partes de URLs) que quieras ignorar
        # Ejemplo:
        # 'https://grupomarquez.com.ar/ofertas',
        # '/promociones',
        '/list/Add/Compare',  # Ignora cualquier URL que contenga este fragmento
    ]