from motorciclye.spiders.motodelta import MotodeltaSpider
import scrapy

class MotomercadoSpider(MotodeltaSpider):
    name = "motomercado"
    allowed_domains = ["motomercado.com.ar"]
    start_urls = ["https://motomercado.com.ar"]

    # Custom settings para manejar rate limiting
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Espera 2 segundos entre requests
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,  # Randomiza el delay hasta 1.5 veces
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Solo 1 request concurrente por dominio
        'RETRY_TIMES': 3,  # Reintentar hasta 3 veces en caso de error
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],  # Códigos de error a reintentar
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    XPATH_MENU_ITEMS='/html/body/header/div[3]/div/div[1]/div/ul/li'
    XPATH_SUBMENU = './/ul'
    XPATH_MENU_LINK = './div/a'
    XPATH_PRODUCT_LINKS = '//div[contains(@class, "item-product")]//a/@href'
    XPATH_NEXT_PAGE = '//a[@class="pagination-next"]/@href'
    HANDLE_PAGINATION = True
    XPATH_PRODUCT_NAME = '//h1[@class="product-name"]/text() | //h1/text()'
    XPATH_PRODUCT_PRICE = '//span[@class="price-current"]/text() | //*[@id="price_display"]/text() | //span[contains(@class, "price")]/text()'
    XPATH_PRODUCT_IMAGES = '//div[@class="product-images"]//img/@src | //div[contains(@class, "image")]//img/@src'
    XPATH_PRODUCT_DESCRIPTION = '//div[@class="product-description"]//text() | //div[contains(@class, "description")]//text() | //*[@id="single-product"]//p/text()'
    XPATH_BREADCRUMB_LAST = '//nav[@class="breadcrumb"]//a[last()] | //ol[@class="breadcrumb"]//a[last()] | //*[contains(@class, "breadcrumb")]//a[last()]'
    XPATH_PRODUCT_ATTRS = '//*[@id="single-product"]/div[2]/div/div[1]/div[1]/ul/li'
    XPATH_PRODUCT_ATTRS_KEY = './/strong/text()'
    XPATH_PRODUCT_ATTRS_VALUE = './text()'
    XPATH_PRODUCT_DISCOUNT_TEXT = '//*[contains(@class, "offer") and contains(text(), "%") and contains(text(), "OFF")]/text() | //div[contains(@class, "text-uppercase") and contains(@class, "font-weight-bold") and contains(text(), "% Off")]/text() | //span[contains(@class, "offer") and contains(text(), "%")]/text()'

    def parse_product_price(self, response):
        # Intentar múltiples selectores para el precio
        raw_price = response.xpath(self.XPATH_PRODUCT_PRICE).get()
        
        if not raw_price:
            # Selectores alternativos para precios
            price_selectors = [
                '//span[contains(@class, "price")]/text()',
                '//div[contains(@class, "price")]//text()',
                '//*[contains(text(), "$")]//text()',
                '//span[contains(text(), "$")]/text()'
            ]
            
            for selector in price_selectors:
                raw_price = response.xpath(selector).get()
                if raw_price and '$' in raw_price:
                    break
        
        if raw_price:
            # Limpiar el precio de caracteres especiales
            import re
            # Buscar números con punto o coma como separadores decimales
            price_match = re.search(r'[\$]?\s*([0-9]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)', raw_price.replace(' ', ''))
            if price_match:
                price_str = price_match.group(1)
                # Convertir formato argentino (punto para miles, coma para decimales)
                if ',' in price_str and '.' in price_str:
                    # Formato: 1.234,56
                    price_str = price_str.replace('.', '').replace(',', '.')
                elif ',' in price_str:
                    # Formato: 1234,56 o 1,234 (miles)
                    if len(price_str.split(',')[1]) == 2:
                        # Es decimal: 1234,56
                        price_str = price_str.replace(',', '.')
                    else:
                        # Son miles: 1,234
                        price_str = price_str.replace(',', '')
                
                try:
                    return float(price_str)
                except ValueError:
                    pass
        
        return None
    
    def parse_product_images(self, response):
        images = response.xpath(self.XPATH_PRODUCT_IMAGES).getall()
        # Filtrar placeholders y URLs vacías
        filtered_images = []
        for img_url in images:
            if img_url and 'empty-placeholder' not in img_url and 'placeholder' not in img_url:
                full_url = response.urljoin(img_url)
                filtered_images.append(full_url)
        return filtered_images

    def parse_product_description(self, response):
        # Intentar múltiples selectores para la descripción
        description_texts = response.xpath(self.XPATH_PRODUCT_DESCRIPTION).getall()
        if description_texts:
            # Limpiar y unir los textos
            cleaned_texts = [text.strip() for text in description_texts if text.strip()]
            return ' '.join(cleaned_texts) if cleaned_texts else None
        return None
