import requests
from lxml import html

def test_discount_xpath():
    """Prueba el XPATH de descuento en productos de motomercado"""
    
    # XPATH que acabamos de crear
    XPATH_PRODUCT_DISCOUNT_TEXT = '//*[contains(@class, "offer") and contains(text(), "%") and contains(text(), "OFF")]/text() | //div[contains(@class, "text-uppercase") and contains(@class, "font-weight-bold") and contains(text(), "% Off")]/text() | //span[contains(@class, "offer") and contains(text(), "%")]/text()'
    
    # URLs de productos para testear
    test_urls = [
        "https://www.motomercado.com.ar/productos/kit-de-cubiertas-pirelli-super-city-80-100-18-90-90-18/",
        "https://www.motomercado.com.ar/productos/3064-sensor-p-estator-honda-cg-125-150/",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in test_urls:
        print(f"\n=== Probando: {url.split('/')[-2]} ===")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                tree = html.fromstring(response.content)
                
                # Probar el XPATH
                discount_texts = tree.xpath(XPATH_PRODUCT_DISCOUNT_TEXT)
                
                if discount_texts:
                    print("✅ DESCUENTOS ENCONTRADOS:")
                    for i, text in enumerate(discount_texts, 1):
                        clean_text = ' '.join(text.split())  # Limpiar espacios
                        print(f"   {i}. {clean_text}")
                else:
                    print("❌ No se encontraron descuentos")
                    
                # También mostrar el precio normal para contexto
                price_xpath = '//span[@class="price-current"]/text() | //*[@id="price_display"]/text() | //span[contains(@class, "price")]/text()'
                prices = tree.xpath(price_xpath)
                if prices:
                    print(f"💰 Precio: {prices[0].strip()}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_discount_xpath()
