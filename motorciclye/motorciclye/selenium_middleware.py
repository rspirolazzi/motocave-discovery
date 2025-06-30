"""
Middleware para usar Selenium cuando hay bloqueo anti-bot severo.
Solo usar si las otras estrategias no funcionan.

Instalar dependencias:
pip install selenium
pip install scrapy-selenium
"""

from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random


class SeleniumMiddleware:
    """Middleware para usar Selenium con Chrome en modo headless"""
    
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Ejecutar sin interfaz gráfica
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Configuraciones anti-detección
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Ejecutar script para ocultar el hecho de que es un webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Error inicializando Selenium: {e}")
            self.driver = None
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def process_request(self, request, spider):
        """Solo usar Selenium para motosport si está configurado"""
        if not self.driver:
            return None
            
        # Solo usar Selenium para el spider motosport
        if getattr(spider, 'name', '') == 'motosport':
            return self._selenium_request(request, spider)
        
        return None
    
    def _selenium_request(self, request, spider):
        """Procesar request con Selenium"""
        try:
            spider.logger.info(f"Usando Selenium para: {request.url}")
            
            # Navegar a la página
            self.driver.get(request.url)
            
            # Simular comportamiento humano
            time.sleep(random.uniform(2, 5))
            
            # Scroll para simular lectura
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(random.uniform(1, 2))
            
            # Obtener el HTML final
            body = self.driver.page_source
            
            # Crear respuesta Scrapy
            return HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
        except Exception as e:
            spider.logger.error(f"Error con Selenium: {e}")
            return None
    
    def spider_closed(self, spider):
        """Cerrar el driver cuando termine el spider"""
        if self.driver:
            self.driver.quit()


# Para habilitar este middleware, agregar a settings.py o custom_settings:
# 'DOWNLOADER_MIDDLEWARES': {
#     'motorciclye.selenium_middleware.SeleniumMiddleware': 600,
# }
