#!/usr/bin/env python3
"""
Suite completa de testing y benchmarking para spiders.

Este script combina testing básico, validación avanzada, benchmarking
y análisis de performance para todos los spiders.

Uso:
    python test_suite.py --quick          # Test rápido de todos los spiders
    python test_suite.py --full           # Test completo con validaciones
    python test_suite.py --benchmark      # Benchmark de performance
    python test_suite.py --compare        # Comparar todos los spiders
    python test_suite.py spider_name      # Test individual detallado
"""

import os
import sys
import json
import time
import statistics
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import psutil

# Agregar el path del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SpiderTestSuite:
    """Suite completa de testing para spiders"""
    
    def __init__(self):
        self.spiders_dir = project_root / "motorciclye" / "spiders"
        self.results_dir = project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Configuración de spiders
        self.spider_configs = {
            'motodelta': {
                'name': 'Moto Delta',
                'url': 'https://www.motodelta.com.ar',
                'expected_categories': 4,
                'expected_min_products': 10
            },
            'gaonamotos': {
                'name': 'Gaona Motos',
                'url': 'https://www.gaonamotos.com',
                'expected_categories': 5,
                'expected_min_products': 15
            },
            'masxmoto': {
                'name': 'Mas x Moto',
                'url': 'https://www.masxmoto.com',
                'expected_categories': 4,
                'expected_min_products': 12
            },
            'motojose': {
                'name': 'Moto José',
                'url': 'https://www.motojose.com.ar',
                'expected_categories': 4,
                'expected_min_products': 10
            },
            'motoscba': {
                'name': 'Motos CBA',
                'url': 'https://www.motoscba.com.ar',
                'expected_categories': 4,
                'expected_min_products': 12
            },
            'shopavantmotos': {
                'name': 'Shop Avant Motos',
                'url': 'https://shopavantmotos.com.ar',
                'expected_categories': 5,
                'expected_min_products': 12
            },
            'motosport': {
                'name': 'Moto Sport',
                'url': 'https://motosport.com.ar',
                'expected_categories': 4,
                'expected_min_products': 10
            }
        }
        
    def run_quick_test(self):
        """Test rápido de todos los spiders"""
        print("⚡ QUICK TEST - Todos los spiders")
        print("=" * 60)
        
        results = {}
        start_time = time.time()
        
        for spider_name in self.spider_configs.keys():
            print(f"🕷️  Testing {spider_name}...", end=" ")
            sys.stdout.flush()
            
            spider_start = time.time()
            result = self._run_spider_test(spider_name, max_items=5, quiet=True)
            spider_duration = time.time() - spider_start
            
            if result and result.get('success'):
                products = len([item for item in result.get('items', []) 
                              if item.get('item_type') == 'product'])
                print(f"✅ {products} productos ({spider_duration:.1f}s)")
            else:
                print("❌ Error")
                
            results[spider_name] = result
            
        total_duration = time.time() - start_time
        
        # Resumen
        print("\\n" + "=" * 60)
        print(f"⏱️  Tiempo total: {total_duration:.1f}s")
        
        successful = len([r for r in results.values() if r and r.get('success')])
        print(f"✅ Spiders exitosos: {successful}/{len(results)}")
        
        total_products = sum(len([item for item in r.get('items', []) 
                                 if item.get('item_type') == 'product'])
                            for r in results.values() if r)
        print(f"📦 Total productos extraídos: {total_products}")
        
        return results
        
    def run_full_test(self):
        """Test completo con validaciones"""
        print("🔍 FULL TEST - Análisis completo")
        print("=" * 60)
        
        results = {}
        
        for spider_name in self.spider_configs.keys():
            print(f"\\n📊 Analizando {spider_name}...")
            print("-" * 40)
            
            result = self._run_comprehensive_test(spider_name)
            results[spider_name] = result
            
            if result:
                self._print_spider_summary(spider_name, result)
                
        # Resumen comparativo
        print("\\n" + "=" * 80)
        print("📈 RESUMEN COMPARATIVO")
        print("=" * 80)
        
        self._print_comparative_summary(results)
        
        return results
        
    def run_benchmark(self):
        """Benchmark de performance"""
        print("🏃 BENCHMARK - Test de rendimiento")
        print("=" * 60)
        
        benchmark_results = {}
        
        for spider_name in self.spider_configs.keys():
            print(f"\\n⚡ Benchmarking {spider_name}...")
            
            # Múltiples ejecuciones para promediar
            durations = []
            items_counts = []
            memory_usage = []
            
            for run in range(3):
                print(f"   Run {run + 1}/3...", end=" ")
                sys.stdout.flush()
                
                # Monitorear memoria antes
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                start_time = time.time()
                result = self._run_spider_test(spider_name, max_items=10, quiet=True)
                duration = time.time() - start_time
                
                # Memoria después
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                if result and result.get('success'):
                    products = len([item for item in result.get('items', []) 
                                  if item.get('item_type') == 'product'])
                    durations.append(duration)
                    items_counts.append(products)
                    memory_usage.append(memory_after - memory_before)
                    print(f"{duration:.1f}s ({products} items)")
                else:
                    print("❌")
                    
            if durations:
                benchmark_results[spider_name] = {
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'avg_items': statistics.mean(items_counts),
                    'avg_memory': statistics.mean(memory_usage),
                    'items_per_second': statistics.mean(items_counts) / statistics.mean(durations)
                }
                
        # Mostrar resultados del benchmark
        self._print_benchmark_results(benchmark_results)
        
        return benchmark_results
        
    def run_comparison(self):
        """Comparar todos los spiders"""
        print("⚖️  COMPARACIÓN - Análisis comparativo")
        print("=" * 70)
        
        results = {}
        
        # Ejecutar test estándar para todos
        for spider_name in self.spider_configs.keys():
            print(f"🕷️  Ejecutando {spider_name}...")
            result = self._run_spider_test(spider_name, max_items=15, quiet=False)
            results[spider_name] = result
            
        # Análisis comparativo
        print("\\n" + "=" * 70)
        print("📊 ANÁLISIS COMPARATIVO")
        print("=" * 70)
        
        self._print_detailed_comparison(results)
        
        return results
        
    def test_individual_spider(self, spider_name):
        """Test individual detallado de un spider"""
        if spider_name not in self.spider_configs:
            print(f"❌ Spider '{spider_name}' no encontrado")
            print(f"Spiders disponibles: {', '.join(self.spider_configs.keys())}")
            return None
            
        config = self.spider_configs[spider_name]
        
        print(f"🔍 TEST INDIVIDUAL: {config['name']}")
        print("=" * 60)
        print(f"🌐 URL: {config['url']}")
        print(f"🎯 Categorías esperadas: {config['expected_categories']}")
        print(f"📦 Productos mínimos: {config['expected_min_products']}")
        print("-" * 60)
        
        # Test completo
        result = self._run_comprehensive_test(spider_name, max_items=25)
        
        if result:
            self._print_detailed_individual_report(spider_name, result)
            
        return result
        
    def _run_spider_test(self, spider_name, max_items=10, quiet=False):
        """Ejecutar test básico de spider"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.results_dir / f"{spider_name}_{timestamp}.json"
        
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-s", f"CLOSESPIDER_ITEMCOUNT={max_items}",
            "-s", "ROBOTSTXT_OBEY=False",
            "-s", "DOWNLOAD_DELAY=0.5",
            "-s", "LOG_LEVEL=ERROR" if quiet else "WARNING",
            "-o", str(output_file)
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=str(project_root), 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            response = {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'items': []
            }
            
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    try:
                        items = json.load(f)
                        response['items'] = items if isinstance(items, list) else [items]
                    except:
                        pass
                        
                # Limpiar archivo temporal
                try:
                    output_file.unlink()
                except:
                    pass
                    
            return response
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _run_comprehensive_test(self, spider_name, max_items=20):
        """Test comprehensivo con análisis detallado"""
        result = self._run_spider_test(spider_name, max_items, quiet=True)
        
        if not result or not result.get('success'):
            return result
            
        items = result.get('items', [])
        
        # Análisis detallado
        analysis = {
            'basic_stats': self._analyze_basic_stats(items),
            'data_quality': self._analyze_data_quality(items),
            'categories': self._analyze_categories(items),
            'urls': self._analyze_urls(items),
            'prices': self._analyze_prices(items),
            'images': self._analyze_images(items),
            'source': self._analyze_source(items)
        }
        
        result['analysis'] = analysis
        return result
        
    def _analyze_basic_stats(self, items):
        """Análisis de estadísticas básicas"""
        sources = [item for item in items if item.get('item_type') == 'source']
        products = [item for item in items if item.get('item_type') == 'product']
        
        return {
            'total_items': len(items),
            'sources': len(sources),
            'products': len(products),
            'categories': len(set(p.get('category_name') for p in products if p.get('category_name')))
        }
        
    def _analyze_data_quality(self, items):
        """Análisis de calidad de datos"""
        products = [item for item in items if item.get('item_type') == 'product']
        
        if not products:
            return {'score': 0, 'issues': ['No hay productos']}
            
        issues = []
        
        # Verificar campos requeridos
        required_fields = ['name', 'price', 'product_url']
        for field in required_fields:
            missing = len([p for p in products if not p.get(field)])
            if missing > 0:
                percentage = (missing / len(products)) * 100
                issues.append(f"{field}: {percentage:.1f}% faltante")
                
        # Score basado en completitud
        completeness = []
        for product in products:
            filled_fields = sum(1 for field in required_fields if product.get(field))
            completeness.append(filled_fields / len(required_fields))
            
        avg_completeness = statistics.mean(completeness) if completeness else 0
        
        return {
            'score': avg_completeness * 100,
            'completeness': avg_completeness,
            'issues': issues
        }
        
    def _analyze_categories(self, items):
        """Análisis de categorías"""
        products = [item for item in items if item.get('item_type') == 'product']
        categories = [p.get('category_name') for p in products if p.get('category_name')]
        
        category_counts = defaultdict(int)
        for category in categories:
            category_counts[category] += 1
            
        return {
            'total_categories': len(category_counts),
            'categories_list': list(category_counts.keys()),
            'category_distribution': dict(category_counts),
            'products_with_category': len(categories),
            'products_without_category': len(products) - len(categories)
        }
        
    def _analyze_urls(self, items):
        """Análisis de URLs"""
        products = [item for item in items if item.get('item_type') == 'product']
        
        valid_urls = 0
        invalid_urls = []
        
        for product in products:
            url = product.get('product_url', '')
            if url and url.startswith('http'):
                valid_urls += 1
            else:
                invalid_urls.append(url)
                
        return {
            'valid_urls': valid_urls,
            'invalid_urls': len(invalid_urls),
            'url_coverage': (valid_urls / len(products)) * 100 if products else 0
        }
        
    def _analyze_prices(self, items):
        """Análisis de precios"""
        products = [item for item in items if item.get('item_type') == 'product']
        prices = [p.get('price') for p in products if isinstance(p.get('price'), (int, float)) and p.get('price') > 0]
        
        if not prices:
            return {'valid_prices': 0, 'price_coverage': 0}
            
        return {
            'valid_prices': len(prices),
            'invalid_prices': len(products) - len(prices),
            'price_coverage': (len(prices) / len(products)) * 100,
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': statistics.mean(prices),
            'median_price': statistics.median(prices)
        }
        
    def _analyze_images(self, items):
        """Análisis de imágenes"""
        products = [item for item in items if item.get('item_type') == 'product']
        
        with_images = 0
        total_images = 0
        
        for product in products:
            images = product.get('images', [])
            if images and len(images) > 0:
                with_images += 1
                total_images += len(images)
                
        return {
            'products_with_images': with_images,
            'products_without_images': len(products) - with_images,
            'image_coverage': (with_images / len(products)) * 100 if products else 0,
            'total_images': total_images,
            'avg_images_per_product': total_images / len(products) if products else 0
        }
        
    def _analyze_source(self, items):
        """Análisis de información de source"""
        sources = [item for item in items if item.get('item_type') == 'source']
        
        if not sources:
            return {'found': False}
            
        source = sources[0]
        contact_methods = source.get('contact_methods', {})
        active_contacts = [k for k, v in contact_methods.items() if v]
        
        return {
            'found': True,
            'name': source.get('name'),
            'url': source.get('source_url'),
            'address': source.get('address'),
            'active_contacts': active_contacts,
            'contact_count': len(active_contacts)
        }
        
    def _print_spider_summary(self, spider_name, result):
        """Imprimir resumen de spider"""
        if not result or not result.get('success'):
            print(f"   ❌ Error en {spider_name}")
            return
            
        analysis = result.get('analysis', {})
        basic = analysis.get('basic_stats', {})
        quality = analysis.get('data_quality', {})
        
        print(f"   ✅ {spider_name}")
        print(f"      📦 Productos: {basic.get('products', 0)}")
        print(f"      🏷️  Categorías: {basic.get('categories', 0)}")
        print(f"      📊 Calidad: {quality.get('score', 0):.1f}%")
        
    def _print_comparative_summary(self, results):
        """Imprimir resumen comparativo"""
        print(f"{'Spider':<15} {'Productos':<10} {'Categorías':<11} {'Calidad':<8} {'URLs':<6} {'Precios':<8}")
        print("-" * 70)
        
        for spider_name, result in results.items():
            if not result or not result.get('success'):
                print(f"{spider_name:<15} {'ERROR':<10}")
                continue
                
            analysis = result.get('analysis', {})
            basic = analysis.get('basic_stats', {})
            quality = analysis.get('data_quality', {})
            urls = analysis.get('urls', {})
            prices = analysis.get('prices', {})
            
            products = basic.get('products', 0)
            categories = basic.get('categories', 0)
            quality_score = quality.get('score', 0)
            url_coverage = urls.get('url_coverage', 0)
            price_coverage = prices.get('price_coverage', 0)
            
            print(f"{spider_name:<15} {products:<10} {categories:<11} {quality_score:<7.1f}% {url_coverage:<5.1f}% {price_coverage:<7.1f}%")
            
    def _print_benchmark_results(self, results):
        """Imprimir resultados del benchmark"""
        print("\\n" + "=" * 80)
        print("🏆 RESULTADOS DEL BENCHMARK")
        print("=" * 80)
        
        print(f"{'Spider':<15} {'Tiempo Avg':<12} {'Items/seg':<10} {'Memoria':<10} {'Mejor':<8}")
        print("-" * 80)
        
        for spider_name, data in results.items():
            avg_duration = data['avg_duration']
            items_per_sec = data['items_per_second']
            memory = data['avg_memory']
            best_time = data['min_duration']
            
            print(f"{spider_name:<15} {avg_duration:<11.1f}s {items_per_sec:<9.2f} {memory:<9.1f}MB {best_time:<7.1f}s")
            
        # Spider más rápido
        if results:
            fastest = min(results.items(), key=lambda x: x[1]['avg_duration'])
            most_efficient = max(results.items(), key=lambda x: x[1]['items_per_second'])
            
            print(f"\\n🥇 Más rápido: {fastest[0]} ({fastest[1]['avg_duration']:.1f}s)")
            print(f"⚡ Más eficiente: {most_efficient[0]} ({most_efficient[1]['items_per_second']:.2f} items/seg)")
            
    def _print_detailed_comparison(self, results):
        """Imprimir comparación detallada"""
        metrics = ['products', 'categories', 'quality_score', 'url_coverage', 'price_coverage', 'image_coverage']
        
        for metric in metrics:
            print(f"\\n📊 {metric.replace('_', ' ').title()}:")
            
            spider_values = []
            for spider_name, result in results.items():
                if result and result.get('success'):
                    analysis = result.get('analysis', {})
                    
                    if metric == 'products':
                        value = analysis.get('basic_stats', {}).get('products', 0)
                    elif metric == 'categories':
                        value = analysis.get('basic_stats', {}).get('categories', 0)
                    elif metric == 'quality_score':
                        value = analysis.get('data_quality', {}).get('score', 0)
                    elif metric == 'url_coverage':
                        value = analysis.get('urls', {}).get('url_coverage', 0)
                    elif metric == 'price_coverage':
                        value = analysis.get('prices', {}).get('price_coverage', 0)
                    elif metric == 'image_coverage':
                        value = analysis.get('images', {}).get('image_coverage', 0)
                    else:
                        value = 0
                        
                    spider_values.append((spider_name, value))
                    
            # Ordenar por valor y mostrar
            spider_values.sort(key=lambda x: x[1], reverse=True)
            
            for i, (spider_name, value) in enumerate(spider_values):
                icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
                if metric in ['quality_score', 'url_coverage', 'price_coverage', 'image_coverage']:
                    print(f"   {icon} {spider_name:<15} {value:6.1f}%")
                else:
                    print(f"   {icon} {spider_name:<15} {value:6}")
                    
    def _print_detailed_individual_report(self, spider_name, result):
        """Imprimir reporte individual detallado"""
        if not result or not result.get('success'):
            print("❌ Error ejecutando spider")
            return
            
        analysis = result.get('analysis', {})
        
        # Estadísticas básicas
        basic = analysis.get('basic_stats', {})
        print(f"\\n📊 ESTADÍSTICAS BÁSICAS:")
        print(f"   📄 Total items: {basic.get('total_items', 0)}")
        print(f"   🏪 Sources: {basic.get('sources', 0)}")
        print(f"   📦 Products: {basic.get('products', 0)}")
        print(f"   🏷️  Categories: {basic.get('categories', 0)}")
        
        # Calidad de datos
        quality = analysis.get('data_quality', {})
        print(f"\\n🎯 CALIDAD DE DATOS:")
        print(f"   📊 Score: {quality.get('score', 0):.1f}%")
        print(f"   ✅ Completitud: {quality.get('completeness', 0):.1f}")
        
        if quality.get('issues'):
            print("   ⚠️  Issues:")
            for issue in quality['issues']:
                print(f"      • {issue}")
                
        # Categorías
        categories = analysis.get('categories', {})
        print(f"\\n🏷️  CATEGORÍAS:")
        print(f"   📊 Total: {categories.get('total_categories', 0)}")
        print(f"   ✅ Con categoría: {categories.get('products_with_category', 0)}")
        print(f"   ❌ Sin categoría: {categories.get('products_without_category', 0)}")
        
        if categories.get('categories_list'):
            print("   📋 Lista:")
            for category in categories['categories_list']:
                count = categories.get('category_distribution', {}).get(category, 0)
                print(f"      • {category} ({count})")
                
        # URLs
        urls = analysis.get('urls', {})
        print(f"\\n🔗 URLs:")
        print(f"   ✅ Válidas: {urls.get('valid_urls', 0)}")
        print(f"   ❌ Inválidas: {urls.get('invalid_urls', 0)}")
        print(f"   📊 Cobertura: {urls.get('url_coverage', 0):.1f}%")
        
        # Precios
        prices = analysis.get('prices', {})
        if prices.get('valid_prices', 0) > 0:
            print(f"\\n💰 PRECIOS:")
            print(f"   ✅ Válidos: {prices.get('valid_prices', 0)}")
            print(f"   ❌ Inválidos: {prices.get('invalid_prices', 0)}")
            print(f"   📊 Cobertura: {prices.get('price_coverage', 0):.1f}%")
            print(f"   💵 Rango: ${prices.get('min_price', 0):,.0f} - ${prices.get('max_price', 0):,.0f}")
            print(f"   📈 Promedio: ${prices.get('avg_price', 0):,.0f}")
            print(f"   📊 Mediana: ${prices.get('median_price', 0):,.0f}")
            
        # Imágenes
        images = analysis.get('images', {})
        print(f"\\n🖼️  IMÁGENES:")
        print(f"   ✅ Con imágenes: {images.get('products_with_images', 0)}")
        print(f"   ❌ Sin imágenes: {images.get('products_without_images', 0)}")
        print(f"   📊 Cobertura: {images.get('image_coverage', 0):.1f}%")
        print(f"   🖼️  Total imágenes: {images.get('total_images', 0)}")
        print(f"   📈 Promedio por producto: {images.get('avg_images_per_product', 0):.1f}")
        
        # Source
        source = analysis.get('source', {})
        if source.get('found'):
            print(f"\\n🏪 INFORMACIÓN DE SOURCE:")
            print(f"   📛 Nombre: {source.get('name', 'N/A')}")
            print(f"   🌐 URL: {source.get('url', 'N/A')}")
            print(f"   📍 Dirección: {source.get('address', 'N/A')}")
            print(f"   📞 Contactos ({source.get('contact_count', 0)}): {', '.join(source.get('active_contacts', []))}")


def main():
    """Función principal"""
    suite = SpiderTestSuite()
    
    if len(sys.argv) < 2:
        print("🧪 SUITE COMPLETA DE TESTING PARA SPIDERS")
        print("")
        print("USO:")
        print("   python test_suite.py --quick          # Test rápido de todos")
        print("   python test_suite.py --full           # Test completo con validaciones")
        print("   python test_suite.py --benchmark      # Benchmark de performance")
        print("   python test_suite.py --compare        # Comparar todos los spiders")
        print("   python test_suite.py <spider_name>    # Test individual detallado")
        print("")
        print("SPIDERS DISPONIBLES:")
        for name, config in suite.spider_configs.items():
            print(f"   • {name:<12} - {config['name']}")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == '--quick':
        suite.run_quick_test()
    elif command == '--full':
        suite.run_full_test()
    elif command == '--benchmark':
        suite.run_benchmark()
    elif command == '--compare':
        suite.run_comparison()
    elif command in suite.spider_configs:
        suite.test_individual_spider(command)
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Usa: --quick, --full, --benchmark, --compare, o un nombre de spider")


if __name__ == "__main__":
    main()
