import requests
from lxml import html

def get_discount_xpaths():
    """Obtiene XPaths específicos para descuentos en motomercado"""
    
    url = "https://www.motomercado.com.ar/productos/kit-de-cubiertas-pirelli-super-city-80-100-18-90-90-18/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            
            print("=== XPATHS PARA DESCUENTOS EN MOTOMERCADO ===\n")
            
            # 1. Texto del porcentaje de descuento (ej: "-19% OFF")
            offer_elements = tree.xpath("//*[contains(@class, 'offer')]")
            for elem in offer_elements:
                text = elem.text_content().strip()
                if '%' in text and 'OFF' in text:
                    print(f"1. DESCUENTO PRINCIPAL: {text}")
                    print(f"   XPath: //*[contains(@class, 'offer') and contains(text(), '%') and contains(text(), 'OFF')]/text()")
                    break
            
            # 2. Texto del descuento por método de pago
            discount_payment = tree.xpath("//div[contains(@class, 'text-uppercase') and contains(@class, 'font-weight-bold') and contains(text(), '% Off')]")
            for elem in discount_payment:
                text = elem.text_content().strip()
                print(f"2. DESCUENTO POR PAGO: {text}")
                print(f"   XPath: //div[contains(@class, 'text-uppercase') and contains(@class, 'font-weight-bold') and contains(text(), '% Off')]/text()")
                break
            
            # 3. Precio con descuento
            discount_price = tree.xpath("//*[contains(@class, 'discount')]//text()[contains(., '$')]")
            for text in discount_price[:2]:
                if '$' in text and text.strip():
                    print(f"3. PRECIO CON DESCUENTO: {text.strip()}")
                    print(f"   XPath: //*[contains(@class, 'discount')]//text()[contains(., '$')]")
                    break
            
            # 4. Buscar texto completo de descuento
            full_discount_text = tree.xpath("//div[contains(text(), '% de descuento')]")
            for elem in full_discount_text:
                text = elem.text_content().strip()
                print(f"4. TEXTO COMPLETO DESCUENTO: {text}")
                print(f"   XPath: //div[contains(text(), '% de descuento')]/text()")
                break
            
            # 5. XPath más específico para el badge de oferta
            offer_badge = tree.xpath("//span[contains(@class, 'offer')]")
            for elem in offer_badge:
                text = elem.text_content().strip()
                if '%' in text:
                    print(f"5. BADGE DE OFERTA: {text}")
                    print(f"   XPath: //span[contains(@class, 'offer') and contains(text(), '%')]/text()")
                    break
            
            print("\n=== XPATH RECOMENDADO ===")
            print("# Para el porcentaje principal de descuento:")
            print("XPATH_PRODUCT_DISCOUNT_TEXT = '//*[contains(@class, \"offer\") and contains(text(), \"%\") and contains(text(), \"OFF\")]/text() | //div[contains(@class, \"text-uppercase\") and contains(@class, \"font-weight-bold\") and contains(text(), \"% Off\")]/text()'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_discount_xpaths()
