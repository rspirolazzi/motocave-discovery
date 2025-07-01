import requests
from lxml import html
import re

def find_discount_elements():
    """Busca elementos relacionados con descuentos en motomercado"""
    
    # URLs para testear
    urls = [
        "https://www.motomercado.com.ar/productos/kit-de-cubiertas-pirelli-super-city-80-100-18-90-90-18/",
        "https://motomercado.com.ar/cubiertas/cubiertas-para-moto/",
        "https://www.motomercado.com.ar/productos/3064-sensor-p-estator-honda-cg-125-150/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        print(f"\n=== Analizando: {url} ===")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                tree = html.fromstring(response.content)
                
                # Buscar palabras clave relacionadas con descuentos
                discount_keywords = [
                    'descuento', 'desc', 'oferta', 'promo', 'sale', 'rebaja', 
                    'antes', 'ahora', 'precio', 'original', 'especial',
                    'discount', 'offer', '%', 'off'
                ]
                
                # Buscar en el texto de la página
                page_text = response.text.lower()
                found_keywords = []
                for keyword in discount_keywords:
                    if keyword in page_text:
                        found_keywords.append(keyword)
                
                print(f"Palabras clave encontradas: {found_keywords}")
                
                # Buscar elementos con clases que puedan contener descuentos
                discount_classes = [
                    'discount', 'sale', 'offer', 'promo', 'price-old', 'price-original',
                    'price-before', 'price-was', 'descuento', 'oferta', 'rebaja'
                ]
                
                for disc_class in discount_classes:
                    elements = tree.xpath(f"//*[contains(@class, '{disc_class}')]")
                    if elements:
                        print(f"Elementos con clase '{disc_class}': {len(elements)}")
                        for elem in elements[:3]:  # Mostrar solo los primeros 3
                            print(f"  - Texto: {elem.text_content().strip()[:100]}")
                            print(f"  - XPath sugerido: //*[contains(@class, '{disc_class}')]")
                
                # Buscar elementos que contengan símbolos de porcentaje
                percent_elements = tree.xpath("//*[contains(text(), '%')]")
                if percent_elements:
                    print(f"Elementos con '%': {len(percent_elements)}")
                    for elem in percent_elements[:3]:
                        text = elem.text_content().strip()
                        if text and len(text) < 50:  # Solo textos cortos
                            print(f"  - Texto: {text}")
                            print(f"  - Tag: {elem.tag}")
                            print(f"  - Clases: {elem.get('class', 'N/A')}")
                
                # Buscar precios tachados o con estilo especial
                strikethrough_elements = tree.xpath("//*[contains(@style, 'line-through') or contains(@style, 'text-decoration')]")
                if strikethrough_elements:
                    print(f"Elementos tachados: {len(strikethrough_elements)}")
                    for elem in strikethrough_elements[:3]:
                        print(f"  - Texto: {elem.text_content().strip()}")
                        print(f"  - XPath: //*[contains(@style, 'line-through')]")
                
            else:
                print(f"Error: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error al procesar {url}: {e}")

if __name__ == "__main__":
    find_discount_elements()
