#!/usr/bin/env python3
"""
Sistema de testing simplificado para spiders de motorcycle.

Este script permite probar cada spider de manera individual y generar reportes
detallados sobre el funcionamiento de cada uno.

Uso:
    python test_runner.py motodelta
    python test_runner.py --all
    python test_runner.py --list
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

# Agregar el path del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SpiderTestRunner:
    """Sistema de testing para spiders"""
    
    def __init__(self):
        self.spiders_dir = project_root / "motorciclye" / "spiders"
        self.available_spiders = self._discover_spiders()
        
    def _discover_spiders(self):
        """Descubrir spiders disponibles en el directorio"""
        spider_files = list(self.spiders_dir.glob("*.py"))
        
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
        
    def test_spider(self, spider_name, max_items=10):
        """Ejecutar test para un spider específico"""
        if spider_name not in self.available_spiders:
            print(f"❌ Spider '{spider_name}' no encontrado")
            print(f"Spiders disponibles: {', '.join(self.available_spiders)}")
            return None
            
        print(f"🧪 Iniciando test para spider: {spider_name}")
        print("-" * 60)
        
        # Crear directorio temporal para resultados
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_dir = project_root / "test_results" / f"{spider_name}_{timestamp}"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = test_dir / f"{spider_name}.json"
        log_file = test_dir / f"{spider_name}.log"
        
        # Comando para ejecutar el spider
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-s", f"CLOSESPIDER_ITEMCOUNT={max_items}",
            "-s", "ROBOTSTXT_OBEY=False",
            "-s", "DOWNLOAD_DELAY=1",
            "-s", "AUTOTHROTTLE_ENABLED=True",
            "-s", "AUTOTHROTTLE_START_DELAY=1",
            "-s", "AUTOTHROTTLE_MAX_DELAY=3",
            "-s", "AUTOTHROTTLE_TARGET_CONCURRENCY=2",
            "-s", "LOG_LEVEL=INFO",
            "-o", str(output_file),
            "-L", "INFO"
        ]
        
        # Ejecutar spider
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analizar resultados
            return self._analyze_results(
                spider_name, output_file, result, duration, test_dir
            )
            
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout ejecutando spider {spider_name} (5 minutos)")
            return None
            
        except Exception as e:
            print(f"❌ Error ejecutando spider {spider_name}: {e}")
            return None
            
    def _analyze_results(self, spider_name, output_file, result, duration, test_dir):
        """Analizar resultados del spider"""
        analysis = {
            'spider_name': spider_name,
            'duration': duration,
            'return_code': result.returncode,
            'success': result.returncode == 0,
            'items': [],
            'sources': [],
            'products': [],
            'categories': set(),
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Guardar logs
        log_file = test_dir / f"{spider_name}.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== STDOUT ===\\n")
            f.write(result.stdout)
            f.write("\\n\\n=== STDERR ===\\n")
            f.write(result.stderr)
        
        # Leer items si existen
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    if not isinstance(items, list):
                        items = [items]
                    
                    analysis['items'] = items
                    
                    # Clasificar items
                    for item in items:
                        if item.get('item_type') == 'source':
                            analysis['sources'].append(item)
                        elif item.get('item_type') == 'product':
                            analysis['products'].append(item)
                            if item.get('category_name'):
                                analysis['categories'].add(item['category_name'])
                                
            except Exception as e:
                analysis['errors'].append(f"Error leyendo resultados: {e}")
        
        # Extraer estadísticas del log
        self._extract_stats_from_log(result.stdout, analysis)
        
        # Validar items
        self._validate_items(analysis)
        
        return analysis
        
    def _extract_stats_from_log(self, log_output, analysis):
        """Extraer estadísticas del log de Scrapy"""
        lines = log_output.split('\\n')
        
        for line in lines:
            if 'ERROR' in line:
                analysis['errors'].append(line.strip())
            elif 'WARNING' in line:
                analysis['warnings'].append(line.strip())
            elif 'downloader/request_count' in line:
                # Extraer estadísticas de Scrapy
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'downloader/request_count' in part:
                            count = parts[i].split(':')[1]
                            analysis['stats']['requests'] = int(count)
                        elif 'downloader/response_count' in part:
                            count = parts[i].split(':')[1]
                            analysis['stats']['responses'] = int(count)
                        elif 'item_scraped_count' in part:
                            count = parts[i].split(':')[1]
                            analysis['stats']['items_scraped'] = int(count)
                except:
                    pass
                    
    def _validate_items(self, analysis):
        """Validar items extraídos"""
        # Validar sources
        for source in analysis['sources']:
            if not source.get('name'):
                analysis['warnings'].append("Source sin nombre")
            if not source.get('source_url'):
                analysis['warnings'].append("Source sin URL")
            
            contact_methods = source.get('contact_methods', {})
            if not contact_methods or not any(contact_methods.values()):
                analysis['warnings'].append("Source sin métodos de contacto")
                
        # Validar products
        for product in analysis['products']:
            if not product.get('name'):
                analysis['warnings'].append("Producto sin nombre")
            if not product.get('product_url'):
                analysis['warnings'].append("Producto sin URL")
            if not product.get('price'):
                analysis['warnings'].append("Producto sin precio")
            if not product.get('images') or len(product.get('images', [])) == 0:
                analysis['warnings'].append("Producto sin imágenes")
            if not product.get('brand'):
                analysis['warnings'].append("Producto sin marca")
                
    def print_analysis(self, analysis):
        """Imprimir análisis detallado"""
        if not analysis:
            return
            
        print("\\n" + "=" * 80)
        print(f"📊 REPORTE: {analysis['spider_name']}")
        print("=" * 80)
        
        # Status general
        status = "✅ ÉXITO" if analysis['success'] else "❌ FALLO"
        print(f"🏁 STATUS: {status}")
        print(f"⏱️  DURACIÓN: {analysis['duration']:.1f}s")
        print(f"🔄 CÓDIGO RETORNO: {analysis['return_code']}")
        
        # Estadísticas de items
        print(f"\\n📊 ESTADÍSTICAS:")
        print(f"   🏪 Sources: {len(analysis['sources'])}")
        print(f"   📦 Products: {len(analysis['products'])}")
        print(f"   🏷️  Categories: {len(analysis['categories'])}")
        print(f"   📄 Total Items: {len(analysis['items'])}")
        
        # Estadísticas de red
        stats = analysis.get('stats', {})
        if stats:
            print(f"\\n🌐 ESTADÍSTICAS DE RED:")
            print(f"   📡 Requests: {stats.get('requests', 0)}")
            print(f"   📥 Responses: {stats.get('responses', 0)}")
            print(f"   📋 Items Scraped: {stats.get('items_scraped', 0)}")
        
        # Source info
        if analysis['sources']:
            source = analysis['sources'][0]
            print(f"\\n🏪 INFORMACIÓN DE LA FUENTE:")
            print(f"   • Nombre: {source.get('name', 'N/A')}")
            print(f"   • URL: {source.get('source_url', 'N/A')}")
            print(f"   • Dirección: {source.get('address', 'N/A')}")
            
            contact_methods = source.get('contact_methods', {})
            contacts = [k for k, v in contact_methods.items() if v]
            print(f"   • Contactos: {', '.join(contacts) if contacts else 'Ninguno'}")
        
        # Categories
        if analysis['categories']:
            print(f"\\n🏷️  CATEGORÍAS ENCONTRADAS:")
            for category in sorted(analysis['categories']):
                print(f"   • {category}")
        
        # Sample products
        if analysis['products']:
            print(f"\\n📦 MUESTRA DE PRODUCTOS:")
            for i, product in enumerate(analysis['products'][:5], 1):
                print(f"   {i}. {product.get('name', 'N/A')}")
                print(f"      💰 Precio: {product.get('price', 'N/A')}")
                print(f"      🏷️  Marca: {product.get('brand', 'N/A')}")
                print(f"      🖼️  Imágenes: {len(product.get('images', []))}")
                print(f"      🔗 URL: {product.get('product_url', 'N/A')}")
                print()
        
        # Errores y warnings
        if analysis['errors']:
            print(f"\\n❌ ERRORES ({len(analysis['errors'])}):")
            for error in analysis['errors'][:10]:  # Solo primeros 10
                print(f"   • {error}")
            if len(analysis['errors']) > 10:
                print(f"   ... y {len(analysis['errors']) - 10} errores más")
        
        if analysis['warnings']:
            print(f"\\n⚠️  WARNINGS ({len(analysis['warnings'])}):")
            for warning in analysis['warnings'][:10]:  # Solo primeros 10
                print(f"   • {warning}")
            if len(analysis['warnings']) > 10:
                print(f"   ... y {len(analysis['warnings']) - 10} warnings más")
        
        print("=" * 80)
        
    def test_all_spiders(self, max_items=5):
        """Ejecutar tests para todos los spiders"""
        print(f"🧪 Ejecutando tests para {len(self.available_spiders)} spiders")
        print("=" * 80)
        
        results = {}
        
        for spider_name in self.available_spiders:
            print(f"\\n📊 Testing {spider_name}...")
            analysis = self.test_spider(spider_name, max_items)
            results[spider_name] = analysis
            
            if analysis:
                status = "✅" if analysis['success'] else "❌"
                print(f"   {status} {len(analysis['products'])} productos, {len(analysis['errors'])} errores, {analysis['duration']:.1f}s")
                
        # Resumen final
        print("\\n" + "=" * 80)
        print("📊 RESUMEN FINAL")
        print("=" * 80)
        
        for spider_name, analysis in results.items():
            if analysis:
                status = "✅" if analysis['success'] else "❌"
                products = len(analysis['products'])
                errors = len(analysis['errors'])
                duration = analysis['duration']
                print(f"{status} {spider_name:15} | {products:3} productos | {errors:2} errores | {duration:5.1f}s")
        
        return results


def main():
    """Función principal"""
    runner = SpiderTestRunner()
    
    if len(sys.argv) < 2:
        print("🧪 Sistema de Testing para Spiders de Motorcycle")
        print("")
        print("USO:")
        print("   python test_runner.py <spider_name>  # Test un spider específico")
        print("   python test_runner.py --all          # Test todos los spiders")
        print("   python test_runner.py --list         # Listar spiders disponibles")
        print("")
        print("EJEMPLOS:")
        print("   python test_runner.py motodelta")
        print("   python test_runner.py motodelta 20   # Máximo 20 items")
        print("   python test_runner.py --all")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == '--list':
        runner.list_spiders()
        
    elif command == '--all':
        max_items = 10
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            max_items = int(sys.argv[2])
            
        runner.test_all_spiders(max_items)
        
    else:
        # Test spider específico
        spider_name = command
        max_items = 20
        
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            max_items = int(sys.argv[2])
            
        analysis = runner.test_spider(spider_name, max_items)
        if analysis:
            runner.print_analysis(analysis)


if __name__ == "__main__":
    main()
