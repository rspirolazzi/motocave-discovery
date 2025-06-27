import scrapy
from scrapy_selenium import SeleniumRequest
import logging
import os


class RodoSpider(scrapy.Spider):
    name = "rodo"
    allowed_domains = ["rodo.com.ar"]
    start_urls = ["https://rodo.com.ar"]

    # XPATHs como atributos de clase
    menu_xpath = '//*[@id="lucian_header123"]/div[2]//a'
    menu_href_xpath = './@href'
    menu_text_xpath = 'normalize-space(string())'
    product_link_xpath = '//*[@id="maincontent"]/div[3]/div[1]/div[2]/div[2]/ul/li/div/div[1]/a/@href'
    next_onclick_xpath = '//*[@class="item pages-item-next"]/a[contains(@class, "next")]/@onclick'
    name_xpath = '//*[@id="maincontent"]/div[2]/div[1]/div[1]/div[1]/div[1]/text()'
    price_xpath = '//*[@id="maincontent"]/div[2]/div[1]/div[1]/div[2]/div[1]/span/span/span/text()'
    images_xpath = '//img/@src'
    brand_label = 'Marca'
    sku_label = 'SKU'
    attr_table_xpath = '//table[@id="product-attribute-specs-table"]'
    start_requests_url = "https://rodo.com.ar"

    ignore_urls = [
        # Agrega aquí las URLs (o partes de URLs) que quieras ignorar
        # Ejemplo:
        # 'https://rodo.com.ar/ofertas',
        # '/promociones',
    ]

    def __init__(self, *args, skip=0, limit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.skip = int(skip)
        self.limit = int(limit) if limit is not None else None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        from scrapy import signals
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider

    def spider_opened(self, spider):
        try:
            # Construir nombre de log custom según los argumentos
            skip = getattr(self, 'skip', 0)
            limit = getattr(self, 'limit', None)
            log_name = f"{self.name}{skip}-{limit if limit is not None else 'all'}.log"
            log_path = os.path.join(os.getcwd(), log_name)
            # Crear un handler de logging para este spider
            handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            # Agregar el handler solo si no existe
            root_logger = logging.getLogger()
            root_logger.addHandler(handler)
            self.logger.info(f"Log personalizado para spider: {log_path}")
            # Este método se ejecuta automáticamente cuando el spider inicia
            self.logger.info("Spider iniciado. Ejecutando lógica custom de inicio...")
            # Eliminar el archivo de salida si existe (detectado por FEEDS)
            feeds = self.settings.get('FEEDS')
            if feeds:
                output_file = list(feeds.keys())[0]
                if os.path.exists(output_file):
                    os.remove(output_file)
                self.logger.info(f"Archivo de salida {output_file} eliminado al iniciar el spider.")
            else:
                self.logger.info("No se encontró archivo de salida en settings['FEEDS']")
        
        except Exception as e:
            print(f"Error al configurar el logger: {e}")
            self.logger.error(f"Error al configurar el logger: {e}")
            raise

    def start_requests(self):
        yield SeleniumRequest(url=self.start_requests_url, callback=self.parse)

    def parse(self, response):
        # Descubrir links de menú (href y texto)
        menu_links = []
        for a in response.xpath(self.menu_xpath):
            href = a.xpath(self.menu_href_xpath).get()
            text = a.xpath(self.menu_text_xpath).get()
            if href:
                abs_href = response.urljoin(href)
                # Ignorar si la URL está en la lista de ignore_urls o contiene algún fragmento a ignorar
                if any(ignore in abs_href for ignore in self.ignore_urls):
                    continue
                menu_links.append({'href': abs_href, 'name': text})
        # Aplicar skip y limit
        selected_links = menu_links[self.skip:self.skip + self.limit if self.limit is not None else None]
        for menu in selected_links:
            yield SeleniumRequest(url=menu['href'], callback=self.parse_menu, meta={'menu_url': menu['href'], 'menu_name': menu['name']})

    def parse_menu(self, response):
        menu_url = response.meta.get('menu_url', response.url)
        menu_name = response.meta.get('menu_name', '')
        # Extraer productos de la página actual
        product_links = response.xpath(self.product_link_xpath).getall()
        for link in product_links:
            yield SeleniumRequest(url=response.urljoin(link), callback=self.parse_product, meta={'menu_url': menu_url, 'menu_name': menu_name})

        # Paginación AJAX: buscar el botón Siguiente y simular click usando el onclick
        # Buscar el atributo onclick del botón Siguiente
        next_onclick = response.xpath(self.next_onclick_xpath).get()
        if next_onclick:
            import re, time
            match = re.search(r"pt_ajax_layer.ajaxFilter\('([^']+)'\)", next_onclick)
            if match:
                next_url = match.group(1)
                # Esperar 3 segundos para simular el tiempo de carga AJAX
                time.sleep(3)
                yield SeleniumRequest(url=next_url, callback=self.parse_menu, meta={'menu_url': menu_url, 'menu_name': menu_name})

    def parse_product(self, response):
        # Extraer datos del producto
        name = response.xpath(self.name_xpath).get(default='').strip()
        price = response.xpath(self.price_xpath).get(default='').strip()
        images = response.xpath(self.images_xpath).getall()
        images = [img for img in images if 'catalog/product' in img]

        # Extraer marca y sku de la tabla de atributos
        def get_attr_from_table(label):
            xpath = f'{self.attr_table_xpath}//tr[th[contains(normalize-space(), "{label}")]]/td/text()'
            return response.xpath(xpath).get(default='').strip()
        brand = get_attr_from_table(self.brand_label)
        sku = get_attr_from_table(self.sku_label)

        # Guardar print de pantalla (solo si usas Selenium)
        file_name = f"screenshot_{self.name}_{hash(response.url)}.png"
        response.meta['driver'].save_screenshot(file_name) if 'driver' in response.meta else None
        self.logger.info(f"Screenshot guardado: {file_name}")

        menu_url = response.meta.get('menu_url', '')
        menu_name = response.meta.get('menu_name', '')

        yield {
            'url': response.url,
            'menu_url': menu_url,
            'menu_name': menu_name,
            'screenshot': file_name,
            'name': name,
            'price': price,
            'images': images,
            'brand': brand,
            'sku': sku
        }

    def close(self, reason):
        # Este método se ejecuta automáticamente cuando el spider finaliza
        self.logger.info(f"Spider finalizado. Motivo: {reason}")
        # Aquí puedes ejecutar cualquier lógica custom, por ejemplo:
        # - enviar un mail
        # - mover archivos
        # - procesar el JSON generado
        # - limpiar recursos
        # Ejemplo:
        # import shutil
        # shutil.move('productos.json', 'bkp/productos.json')
        pass

