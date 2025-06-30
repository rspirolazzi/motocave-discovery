#!/usr/bin/env python3
"""
Sistema de testing para spiders de motorcycle.

Este módulo permite probar cada spider individualmente para verificar:
- Que extrae información correctamente
- Que los XPATHs funcionan
- Que la estructura de datos es correcta
- Que los pipelines procesan correctamente

Uso:
    python test_spiders.py motodelta
    python test_spiders.py --all
    python test_spiders.py --list
"""

import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

# Agregar el path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import Spider


class SpiderTestResult:
    """Clase para almacenar resultados de tests de spider"""
    
    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.start_time = None
        self.end_time = None
        self.sources_found = 0
        self.products_found = 0
        self.categories_found = set()
        self.errors = []
        self.warnings = []
        self.sample_products = []
        self.source_data = None
        
    def start_test(self):
        self.start_time = datetime.now()
        
    def end_test(self):
        self.end_time = datetime.now()
        
    def add_source(self, source_item):
        self.sources_found += 1
        self.source_data = source_item
        
    def add_product(self, product_item):
        self.products_found += 1
        if product_item.get('category_name'):
            self.categories_found.add(product_item['category_name'])
        
        # Guardar muestra de productos (primeros 5)
        if len(self.sample_products) < 5:
            self.sample_products.append({
                'name': product_item.get('name'),
                'price': product_item.get('price'),
                'url': product_item.get('product_url'),
                'brand': product_item.get('brand'),
                'images_count': len(product_item.get('images', []))
            })
    
    def add_error(self, error_msg):
        self.errors.append(error_msg)
        
    def add_warning(self, warning_msg):
        self.warnings.append(warning_msg)
        
    def get_duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
        
    def get_success_rate(self):
        total_items = self.sources_found + self.products_found
        if total_items == 0:
            return 0
        return ((total_items - len(self.errors)) / total_items) * 100


class TestPipeline:
    """Pipeline de testing que captura items para validación"""
    
    def __init__(self):
        self.test_result = None
        
    @classmethod
    def from_crawler(cls, crawler):
        """Crear pipeline desde crawler"""
        pipeline = cls()
        # Obtener test_result del spider
        pipeline.test_result = getattr(crawler.spider, 'test_result', None)
        return pipeline
        
    def open_spider(self, spider):
        self.test_result.start_test()
        spider.logger.info(f"🧪 Iniciando test para spider: {spider.name}")
        
    def process_item(self, item, spider):
        try:
            # Validar estructura básica del item
            if not isinstance(item, dict):
                self.test_result.add_error(f"Item no es un diccionario: {type(item)}")
                return item
                
            item_type = item.get('item_type')
            
            if item_type == 'source':
                self._test_source_item(item, spider)
                self.test_result.add_source(item)
                
            elif item_type == 'product':
                self._test_product_item(item, spider)
                self.test_result.add_product(item)
                
            else:
                self.test_result.add_warning(f"Tipo de item desconocido: {item_type}")
                
        except Exception as e:
            self.test_result.add_error(f"Error procesando item: {e}")
            
        return item
        
    def close_spider(self, spider):
        self.test_result.end_test()
        spider.logger.info(f"🧪 Test completado para spider: {spider.name}")
        
    def _test_source_item(self, item, spider):
        """Validar item de tipo source"""
        required_fields = ['name', 'source_url']
        for field in required_fields:
            if not item.get(field):
                self.test_result.add_error(f"Source sin campo requerido: {field}")
                
        # Validar contact_methods
        contact_methods = item.get('contact_methods', {})
        if not contact_methods or not any(contact_methods.values()):
            self.test_result.add_warning("Source sin métodos de contacto")
            
        # Validar URL
        source_url = item.get('source_url')
        if source_url and not source_url.startswith('http'):
            self.test_result.add_error(f"Source URL inválida: {source_url}")
            
    def _test_product_item(self, item, spider):
        """Validar item de tipo product"""
        required_fields = ['name', 'product_url']
        for field in required_fields:
            if not item.get(field):
                self.test_result.add_error(f"Producto sin campo requerido: {field}")
                
        # Validar URL del producto
        product_url = item.get('product_url')
        if product_url and not product_url.startswith('http'):
            self.test_result.add_error(f"Product URL inválida: {product_url}")
            
        # Validaciones opcionales con warnings
        if not item.get('price'):
            self.test_result.add_warning("Producto sin precio")
            
        if not item.get('images') or len(item.get('images', [])) == 0:
            self.test_result.add_warning("Producto sin imágenes")
            
        if not item.get('brand'):
            self.test_result.add_warning("Producto sin marca")
            
        if not item.get('category_name'):
            self.test_result.add_warning("Producto sin categoría")


class SpiderTester:
    """Clase principal para testing de spiders"""
    
    def __init__(self):
        self.available_spiders = self._discover_spiders()
        
    def _discover_spiders(self):
        """Descubrir spiders disponibles en el directorio"""
        spiders_dir = Path(__file__).parent / "spiders"
        spider_files = list(spiders_dir.glob("*.py"))
        
        spiders = []
        for spider_file in spider_files:
            if spider_file.name.startswith('_') or spider_file.name == '__init__.py':
                continue
            if spider_file.name in ['base_spider.py']:
                continue
                
            spider_name = spider_file.stem
            spiders.append(spider_name)
            
        return sorted(spiders)
        
    def list_spiders(self):
        """Listar spiders disponibles"""
        print("🕷️  Spiders disponibles para testing:")
        print("-" * 40)
        for spider in self.available_spiders:
            print(f"   • {spider}")
        print("-" * 40)
        print(f"Total: {len(self.available_spiders)} spiders")
        
    def test_spider(self, spider_name, max_products=10):
        """Ejecutar test para un spider específico"""
        if spider_name not in self.available_spiders:
            print(f"❌ Spider '{spider_name}' no encontrado")
            print(f"Spiders disponibles: {', '.join(self.available_spiders)}")
            return None
            
        print(f"🧪 Iniciando test para spider: {spider_name}")
        print("-" * 60)
        
        # Crear resultado de test
        test_result = SpiderTestResult(spider_name)
        
        # Configurar settings para test
        settings = get_project_settings()
        settings.update({
            'ITEM_PIPELINES': {
                'test_spiders.TestPipeline': 100,
            },
            'ROBOTSTXT_OBEY': False,
            'DOWNLOAD_DELAY': 1,
            'RANDOMIZE_DOWNLOAD_DELAY': False,
            'AUTOTHROTTLE_ENABLED': True,
            'AUTOTHROTTLE_START_DELAY': 1,
            'AUTOTHROTTLE_MAX_DELAY': 3,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 2,
            'CLOSESPIDER_ITEMCOUNT': max_products + 5,  # +5 para source y categorías
            'LOG_LEVEL': 'INFO',
        })
        
        # Ejecutar spider
        try:
            process = CrawlerProcess(settings)
            
            # Crear spider y asignar test_result
            def spider_opened(spider):
                spider.test_result = test_result
                
            process.crawl(spider_name)
            process.start(stop_after_crawl=True)
            
        except Exception as e:
            test_result.add_error(f"Error ejecutando spider: {e}")
            
        return test_result
        
    def test_all_spiders(self, max_products=5):
        """Ejecutar tests para todos los spiders"""
        print(f"🧪 Ejecutando tests para {len(self.available_spiders)} spiders")
        print("=" * 80)
        
        results = {}
        
        for spider_name in self.available_spiders:
            print(f"\n📊 Testing {spider_name}...")
            result = self.test_spider(spider_name, max_products)
            results[spider_name] = result
            
            if result:
                self._print_quick_summary(result)
                
        return results
        
    def _print_quick_summary(self, result):
        """Imprimir resumen rápido del test"""
        duration = result.get_duration()
        success_rate = result.get_success_rate()
        
        status = "✅" if len(result.errors) == 0 else "❌"
        print(f"   {status} {result.products_found} productos, {len(result.errors)} errores, {duration:.1f}s")


def print_detailed_report(test_result):
    """Imprimir reporte detallado del test"""
    if not test_result:
        return
        
    print("\n" + "=" * 80)
    print(f"📊 REPORTE DETALLADO: {test_result.spider_name}")
    print("=" * 80)
    
    # Estadísticas generales
    duration = test_result.get_duration()
    success_rate = test_result.get_success_rate()
    
    print(f"⏱️  TIEMPO: {duration:.1f}s")
    print(f"📈 TASA DE ÉXITO: {success_rate:.1f}%")
    print(f"🏪 FUENTES: {test_result.sources_found}")
    print(f"📦 PRODUCTOS: {test_result.products_found}")
    print(f"🏷️  CATEGORÍAS: {len(test_result.categories_found)}")
    print(f"❌ ERRORES: {len(test_result.errors)}")
    print(f"⚠️  WARNINGS: {len(test_result.warnings)}")
    
    # Información de la fuente
    if test_result.source_data:
        print(f"\n🏪 INFORMACIÓN DE LA FUENTE:")
        source = test_result.source_data
        print(f"   • Nombre: {source.get('name', 'N/A')}")
        print(f"   • URL: {source.get('source_url', 'N/A')}")
        print(f"   • Dirección: {source.get('address', 'N/A')}")
        
        contact_methods = source.get('contact_methods', {})
        contacts = [k for k, v in contact_methods.items() if v]
        print(f"   • Contactos: {', '.join(contacts) if contacts else 'Ninguno'}")
    
    # Categorías encontradas
    if test_result.categories_found:
        print(f"\n🏷️  CATEGORÍAS ENCONTRADAS:")
        for category in sorted(test_result.categories_found):
            print(f"   • {category}")
    
    # Muestra de productos
    if test_result.sample_products:
        print(f"\n📦 MUESTRA DE PRODUCTOS:")
        for i, product in enumerate(test_result.sample_products, 1):
            print(f"   {i}. {product['name']}")
            print(f"      💰 Precio: {product['price'] or 'N/A'}")
            print(f"      🏷️  Marca: {product['brand'] or 'N/A'}")
            print(f"      🖼️  Imágenes: {product['images_count']}")
            print(f"      🔗 URL: {product['url']}")
            print()
    
    # Errores
    if test_result.errors:
        print(f"\n❌ ERRORES:")
        for error in test_result.errors:
            print(f"   • {error}")
    
    # Warnings
    if test_result.warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in test_result.warnings:
            print(f"   • {warning}")
    
    print("=" * 80)


def main():
    """Función principal"""
    tester = SpiderTester()
    
    if len(sys.argv) < 2:
        print("🧪 Sistema de Testing para Spiders de Motorcycle")
        print("")
        print("USO:")
        print("   python test_spiders.py <spider_name>  # Test un spider específico")
        print("   python test_spiders.py --all          # Test todos los spiders")
        print("   python test_spiders.py --list         # Listar spiders disponibles")
        print("")
        print("EJEMPLOS:")
        print("   python test_spiders.py motodelta")
        print("   python test_spiders.py --all")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == '--list':
        tester.list_spiders()
        
    elif command == '--all':
        max_products = 10
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            max_products = int(sys.argv[2])
            
        results = tester.test_all_spiders(max_products)
        
        # Reporte final
        print("\n" + "=" * 80)
        print("📊 RESUMEN FINAL")
        print("=" * 80)
        
        for spider_name, result in results.items():
            if result:
                status = "✅" if len(result.errors) == 0 else "❌"
                print(f"{status} {spider_name:15} | {result.products_found:3} productos | {len(result.errors):2} errores")
        
    else:
        # Test spider específico
        spider_name = command
        max_products = 20
        
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            max_products = int(sys.argv[2])
            
        result = tester.test_spider(spider_name, max_products)
        if result:
            print_detailed_report(result)


if __name__ == "__main__":
    main()
