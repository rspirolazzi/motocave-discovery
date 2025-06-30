#!/usr/bin/env python3
"""
Sistema de testing avanzado con validaciones específicas para spiders.

Este módulo incluye tests específicos para cada spider y validaciones
detalladas de los datos extraídos.

Uso:
    python advanced_test.py motodelta --deep
    python advanced_test.py --validate-all
    python advanced_test.py --benchmark
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

# Agregar el path del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class AdvancedSpiderValidator:
    """Validador avanzado para spiders con tests específicos"""
    
    def __init__(self):
        self.spiders_dir = project_root / "motorciclye" / "spiders"
        self.test_results_dir = project_root / "test_results"
        self.test_results_dir.mkdir(exist_ok=True)
        
        # Configuraciones específicas por spider
        self.spider_configs = {
            'motodelta': {
                'expected_categories': ['Cascos', 'Intercomunicadores', 'Mochilas', 'Portaequipajes'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],  # Campos críticos que no pueden estar vacíos
                'price_range': (10000, 5000000),  # Rango de precios esperado
                'min_images': 1,
                'base_url': 'https://www.motodelta.com.ar'
            },
            'gaonamotos': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Filtros', 'Cadenas'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (5000, 1000000),
                'min_images': 1,
                'base_url': 'https://www.gaonamotos.com'
            },
            'masxmoto': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Aceites', 'Repuestos'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (5000, 800000),
                'min_images': 1,
                'base_url': 'https://www.masxmoto.com'
            },
            'motojose': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Aceites', 'Accesorios'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (10000, 2000000),
                'min_images': 1,
                'base_url': 'https://www.motojose.com.ar'
            },
            'motoscba': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Aceites', 'Repuestos'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (5000, 1500000),
                'min_images': 1,
                'base_url': 'https://www.motoscba.com.ar'
            },
            'shopavantmotos': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Filtros', 'Cadenas'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (5000, 1000000),
                'min_images': 1,
                'base_url': 'https://shopavantmotos.com.ar'
            },
            'motosport': {
                'expected_categories': ['Cascos', 'Cubiertas', 'Aceites', 'Accesorios'],
                'required_fields': ['menu_name', 'menu_url', 'product_url', 'name', 'price', 'brand', 'attrs', 'discount_text', 'images', 'description', 'category_name', 'category_url', 'source'],
                'critical_fields': ['name', 'price', 'product_url'],
                'price_range': (5000, 2000000),
                'min_images': 1,
                'base_url': 'https://motosport.com.ar'
            }
        }
        
    def run_deep_validation(self, spider_name, max_items=20):
        """Ejecutar validación profunda de un spider"""
        print(f"🔍 Ejecutando validación profunda para {spider_name}")
        print("-" * 60)
        
        # Ejecutar spider con más items
        result = self._run_spider(spider_name, max_items)
        if not result:
            return None
            
        # Validaciones específicas
        validation_result = {
            'spider_name': spider_name,
            'timestamp': datetime.now().isoformat(),
            'items_analyzed': len(result.get('items', [])),
            'validations': {
                'structure': self._validate_structure(spider_name, result),
                'data_quality': self._validate_data_quality(spider_name, result),
                'urls': self._validate_urls(spider_name, result),
                'prices': self._validate_prices(spider_name, result),
                'images': self._validate_images(spider_name, result),
                'categories': self._validate_categories(spider_name, result),
                'source_info': self._validate_source_info(spider_name, result)
            },
            'score': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Calcular score
        validation_result['score'] = self._calculate_score(validation_result['validations'])
        
        # Guardar resultado
        self._save_validation_result(validation_result)
        
        return validation_result
        
    def _run_spider(self, spider_name, max_items):
        """Ejecutar spider y obtener resultados"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.test_results_dir / f"{spider_name}_{timestamp}.json"
        
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-s", f"CLOSESPIDER_ITEMCOUNT={max_items}",
            "-s", "ROBOTSTXT_OBEY=False",
            "-s", "DOWNLOAD_DELAY=0.5",
            "-s", "LOG_LEVEL=WARNING",
            "-o", str(output_file)
        ]
        
        try:
            subprocess.run(cmd, cwd=str(project_root), capture_output=True, timeout=300)
            
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    return {'items': items if isinstance(items, list) else [items]}
        except:
            pass
            
        return None
        
    def _validate_structure(self, spider_name, result):
        """Validar estructura de los items"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        items = result.get('items', [])
        if not items:
            validation['issues'].append("No se encontraron items")
            return validation
            
        config = self.spider_configs.get(spider_name, {})
        required_fields = config.get('required_fields', [])
        critical_fields = config.get('critical_fields', ['name', 'price', 'product_url'])
        
        sources = [item for item in items if item.get('item_type') == 'source']
        products = [item for item in items if item.get('item_type') == 'product']
        
        validation['details']['sources_count'] = len(sources)
        validation['details']['products_count'] = len(products)
        
        # Validar que hay al menos una source
        if not sources:
            validation['issues'].append("No se encontró información de source")
        else:
            validation['score'] += 15
            
        if not products:
            validation['issues'].append("No se encontraron productos")
            return validation
            
        # Validar campos requeridos en productos
        field_completeness = {}
        critical_field_issues = {}
        
        for field in required_fields:
            missing_count = 0
            empty_count = 0
            
            for product in products:
                value = product.get(field)
                
                # Campo completamente ausente
                if field not in product:
                    missing_count += 1
                # Campo presente pero vacío/None
                elif not value or (isinstance(value, (list, dict)) and len(value) == 0):
                    empty_count += 1
                    
            total_issues = missing_count + empty_count
            completeness = ((len(products) - total_issues) / len(products)) * 100
            field_completeness[field] = {
                'completeness': completeness,
                'missing': missing_count,
                'empty': empty_count,
                'total_issues': total_issues
            }
            
            # Reportar issues
            if total_issues > 0:
                percentage = (total_issues / len(products)) * 100
                issue_msg = f"Campo '{field}': {percentage:.1f}% incompleto"
                if missing_count > 0:
                    issue_msg += f" ({missing_count} ausentes"
                if empty_count > 0:
                    issue_msg += f", {empty_count} vacíos" if missing_count > 0 else f" ({empty_count} vacíos"
                issue_msg += ")"
                
                validation['issues'].append(issue_msg)
                
                # Campos críticos con penalización mayor
                if field in critical_fields:
                    critical_field_issues[field] = percentage
                    
        validation['details']['field_completeness'] = field_completeness
        validation['details']['critical_field_issues'] = critical_field_issues
        
        # Calcular score basado en completitud
        if field_completeness:
            avg_completeness = sum(f['completeness'] for f in field_completeness.values()) / len(field_completeness)
            validation['score'] += (avg_completeness / 100) * 70  # 70% del score basado en completitud
            
            # Penalización extra por campos críticos faltantes
            if critical_field_issues:
                avg_critical_issues = sum(critical_field_issues.values()) / len(critical_field_issues)
                penalty = (avg_critical_issues / 100) * 30  # Penalización hasta 30 puntos
                validation['score'] = max(0, validation['score'] - penalty)
        
        # Validar tipos de datos
        type_issues = self._validate_data_types(products)
        validation['issues'].extend(type_issues)
        
        if not type_issues:
            validation['score'] += 15
            
        # Validar estructura específica de campos
        structure_issues = self._validate_field_structures(products)
        validation['issues'].extend(structure_issues)
        validation['details']['structure_issues'] = structure_issues
        
        return validation
        
    def _validate_data_quality(self, spider_name, result):
        """Validar calidad de los datos"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        products = [item for item in result.get('items', []) if item.get('item_type') == 'product']
        
        if not products:
            validation['issues'].append("No hay productos para validar")
            return validation
            
        # Validar nombres de productos
        names_quality = self._check_names_quality(products)
        validation['details']['names_quality'] = names_quality
        if names_quality['score'] > 80:
            validation['score'] += 25
        else:
            validation['issues'].extend(names_quality['issues'])
            
        # Validar precios
        prices_quality = self._check_prices_quality(products)
        validation['details']['prices_quality'] = prices_quality
        if prices_quality['score'] > 80:
            validation['score'] += 25
        else:
            validation['issues'].extend(prices_quality['issues'])
            
        # Validar marcas
        brands_quality = self._check_brands_quality(products)
        validation['details']['brands_quality'] = brands_quality
        if brands_quality['score'] > 70:
            validation['score'] += 25
        else:
            validation['issues'].extend(brands_quality['issues'])
            
        # Validar duplicados
        duplicates = self._check_duplicates(products)
        validation['details']['duplicates'] = duplicates
        if duplicates['count'] == 0:
            validation['score'] += 25
        else:
            validation['issues'].append(f"Se encontraron {duplicates['count']} productos duplicados")
            
        return validation
        
    def _validate_urls(self, spider_name, result):
        """Validar URLs de productos"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        products = [item for item in result.get('items', []) if item.get('item_type') == 'product']
        config = self.spider_configs.get(spider_name, {})
        base_url = config.get('base_url', '')
        
        if not products:
            return validation
            
        valid_urls = 0
        invalid_urls = []
        
        for product in products:
            url = product.get('product_url', '')
            if not url:
                invalid_urls.append("URL vacía")
                continue
                
            if not url.startswith('http'):
                invalid_urls.append(f"URL sin protocolo: {url}")
                continue
                
            if base_url and not url.startswith(base_url):
                invalid_urls.append(f"URL de dominio incorrecto: {url}")
                continue
                
            valid_urls += 1
            
        validation['details']['valid_urls'] = valid_urls
        validation['details']['invalid_urls'] = len(invalid_urls)
        
        if len(invalid_urls) == 0:
            validation['score'] = 100
        else:
            validation['score'] = (valid_urls / len(products)) * 100
            validation['issues'].extend(invalid_urls[:5])  # Solo primeros 5
            
        return validation
        
    def _validate_prices(self, spider_name, result):
        """Validar precios de productos"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        products = [item for item in result.get('items', []) if item.get('item_type') == 'product']
        config = self.spider_configs.get(spider_name, {})
        price_range = config.get('price_range', (0, float('inf')))
        
        if not products:
            return validation
            
        valid_prices = 0
        price_issues = []
        
        for product in products:
            price = product.get('price')
            
            if price is None:
                price_issues.append(f"Producto sin precio: {product.get('name', 'N/A')[:50]}")
                continue
                
            if not isinstance(price, (int, float)):
                price_issues.append(f"Precio no numérico: {price}")
                continue
                
            if price <= 0:
                price_issues.append(f"Precio inválido: {price}")
                continue
                
            if not (price_range[0] <= price <= price_range[1]):
                price_issues.append(f"Precio fuera de rango: {price}")
                continue
                
            valid_prices += 1
            
        validation['details']['valid_prices'] = valid_prices
        validation['details']['invalid_prices'] = len(price_issues)
        
        if len(price_issues) == 0:
            validation['score'] = 100
        else:
            validation['score'] = (valid_prices / len(products)) * 100
            validation['issues'].extend(price_issues[:5])
            
        return validation
        
    def _validate_images(self, spider_name, result):
        """Validar imágenes de productos"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        products = [item for item in result.get('items', []) if item.get('item_type') == 'product']
        config = self.spider_configs.get(spider_name, {})
        min_images = config.get('min_images', 1)
        
        if not products:
            return validation
            
        products_with_images = 0
        image_issues = []
        
        for product in products:
            images = product.get('images', [])
            
            if not images or len(images) == 0:
                image_issues.append(f"Producto sin imágenes: {product.get('name', 'N/A')[:50]}")
                continue
                
            if len(images) < min_images:
                image_issues.append(f"Pocas imágenes ({len(images)}): {product.get('name', 'N/A')[:50]}")
                continue
                
            # Validar URLs de imágenes
            valid_image_urls = 0
            for img_url in images:
                if isinstance(img_url, str) and img_url.startswith('http'):
                    valid_image_urls += 1
                    
            if valid_image_urls == 0:
                image_issues.append(f"Sin URLs válidas de imágenes: {product.get('name', 'N/A')[:50]}")
                continue
                
            products_with_images += 1
            
        validation['details']['products_with_images'] = products_with_images
        validation['details']['products_without_images'] = len(image_issues)
        
        if len(image_issues) == 0:
            validation['score'] = 100
        else:
            validation['score'] = (products_with_images / len(products)) * 100
            validation['issues'].extend(image_issues[:5])
            
        return validation
        
    def _validate_categories(self, spider_name, result):
        """Validar categorías encontradas"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        products = [item for item in result.get('items', []) if item.get('item_type') == 'product']
        config = self.spider_configs.get(spider_name, {})
        expected_categories = config.get('expected_categories', [])
        
        if not products:
            return validation
            
        found_categories = set()
        products_with_category = 0
        
        for product in products:
            category = product.get('category_name')
            if category:
                found_categories.add(category)
                products_with_category += 1
                
        validation['details']['found_categories'] = list(found_categories)
        validation['details']['products_with_category'] = products_with_category
        validation['details']['expected_categories'] = expected_categories
        
        # Score basado en productos con categoría
        category_coverage = (products_with_category / len(products)) * 100
        validation['score'] = category_coverage
        
        if category_coverage < 80:
            validation['issues'].append(f"Solo {category_coverage:.1f}% de productos tienen categoría")
            
        # Verificar categorías esperadas
        if expected_categories:
            missing_categories = set(expected_categories) - found_categories
            if missing_categories:
                validation['issues'].append(f"Categorías faltantes: {', '.join(missing_categories)}")
                
        return validation
        
    def _validate_source_info(self, spider_name, result):
        """Validar información de la fuente"""
        validation = {'score': 0, 'issues': [], 'details': {}}
        
        sources = [item for item in result.get('items', []) if item.get('item_type') == 'source']
        
        if not sources:
            validation['issues'].append("No se encontró información de source")
            return validation
            
        source = sources[0]  # Tomamos la primera source
        
        required_source_fields = ['name', 'source_url', 'contact_methods']
        missing_fields = [field for field in required_source_fields if not source.get(field)]
        
        if missing_fields:
            validation['issues'].append(f"Campos faltantes en source: {', '.join(missing_fields)}")
            validation['score'] = 50
        else:
            validation['score'] = 80
            
        # Validar métodos de contacto
        contact_methods = source.get('contact_methods', {})
        active_contacts = [k for k, v in contact_methods.items() if v]
        
        validation['details']['active_contacts'] = active_contacts
        
        if len(active_contacts) >= 2:
            validation['score'] = 100
        elif len(active_contacts) == 1:
            validation['score'] = max(validation['score'], 70)
        else:
            validation['issues'].append("Sin métodos de contacto activos")
            
        return validation
        
    def _check_names_quality(self, products):
        """Verificar calidad de nombres de productos"""
        result = {'score': 0, 'issues': []}
        
        if not products:
            return result
            
        short_names = 0
        empty_names = 0
        very_long_names = 0
        
        for product in products:
            name = product.get('name', '')
            
            if not name:
                empty_names += 1
            elif len(name) < 10:
                short_names += 1
            elif len(name) > 200:
                very_long_names += 1
                
        total = len(products)
        
        if empty_names > 0:
            result['issues'].append(f"{empty_names} productos sin nombre")
        if short_names > total * 0.2:
            result['issues'].append(f"{short_names} productos con nombres muy cortos")
        if very_long_names > total * 0.1:
            result['issues'].append(f"{very_long_names} productos con nombres muy largos")
            
        # Calcular score
        issues_percentage = (empty_names + short_names + very_long_names) / total
        result['score'] = max(0, (1 - issues_percentage) * 100)
        
        return result
        
    def _check_prices_quality(self, products):
        """Verificar calidad de precios"""
        result = {'score': 0, 'issues': []}
        
        if not products:
            return result
            
        prices = [p.get('price') for p in products if p.get('price') is not None]
        
        if not prices:
            result['issues'].append("No hay precios válidos")
            return result
            
        # Verificar consistencia de precios
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        if max_price / min_price > 1000:  # Ratio muy alto
            result['issues'].append(f"Rango de precios muy amplio: ${min_price} - ${max_price}")
            
        # Score basado en productos con precio
        price_coverage = len(prices) / len(products)
        result['score'] = price_coverage * 100
        
        return result
        
    def _check_brands_quality(self, products):
        """Verificar calidad de marcas"""
        result = {'score': 0, 'issues': []}
        
        if not products:
            return result
            
        brands = [p.get('brand') for p in products if p.get('brand')]
        
        # Score basado en productos con marca
        brand_coverage = len(brands) / len(products)
        result['score'] = brand_coverage * 100
        
        if brand_coverage < 0.8:
            result['issues'].append(f"Solo {brand_coverage*100:.1f}% de productos tienen marca")
            
        return result
        
    def _check_duplicates(self, products):
        """Verificar productos duplicados"""
        result = {'count': 0, 'duplicates': []}
        
        seen_urls = set()
        seen_names = set()
        
        for product in products:
            url = product.get('product_url')
            name = product.get('name')
            
            if url and url in seen_urls:
                result['count'] += 1
                result['duplicates'].append(f"URL duplicada: {url}")
            else:
                seen_urls.add(url)
                
            if name and name in seen_names:
                result['count'] += 1
                result['duplicates'].append(f"Nombre duplicado: {name}")
            else:
                seen_names.add(name)
                
        return result
        
    def _validate_data_types(self, products):
        """Validar tipos de datos"""
        issues = []
        
        for product in products:
            # Validar precio
            price = product.get('price')
            if price is not None and not isinstance(price, (int, float)):
                issues.append(f"Precio no numérico: {type(price)}")
                
            # Validar imágenes
            images = product.get('images')
            if images is not None and not isinstance(images, list):
                issues.append(f"Imágenes no es lista: {type(images)}")
                
            # Validar URL
            url = product.get('product_url')
            if url is not None and not isinstance(url, str):
                issues.append(f"URL no es string: {type(url)}")
                
        return issues
        
    def _validate_field_structures(self, products):
        """Validar estructuras específicas de campos"""
        issues = []
        
        for i, product in enumerate(products):
            product_id = f"Producto {i+1}"
            
            # Validar que attrs es un diccionario
            attrs = product.get('attrs')
            if attrs is not None and not isinstance(attrs, dict):
                issues.append(f"{product_id}: 'attrs' debe ser un diccionario, encontrado {type(attrs)}")
                
            # Validar que images es una lista
            images = product.get('images')
            if images is not None and not isinstance(images, list):
                issues.append(f"{product_id}: 'images' debe ser una lista, encontrado {type(images)}")
            elif isinstance(images, list):
                # Validar que las URLs de imágenes son strings
                for j, img in enumerate(images):
                    if not isinstance(img, str):
                        issues.append(f"{product_id}: imagen {j+1} debe ser string, encontrado {type(img)}")
                        
            # Validar que price es numérico
            price = product.get('price')
            if price is not None and not isinstance(price, (int, float)):
                issues.append(f"{product_id}: 'price' debe ser numérico, encontrado {type(price)}")
                
            # Validar que las URLs son strings válidas
            for url_field in ['menu_url', 'product_url', 'category_url']:
                url = product.get(url_field)
                if url is not None:
                    if not isinstance(url, str):
                        issues.append(f"{product_id}: '{url_field}' debe ser string, encontrado {type(url)}")
                    elif url and not url.startswith(('http://', 'https://')):
                        issues.append(f"{product_id}: '{url_field}' debe ser URL válida: {url}")
                        
            # Validar que source es boolean
            source = product.get('source')
            if source is not None and not isinstance(source, bool):
                issues.append(f"{product_id}: 'source' debe ser boolean, encontrado {type(source)}")
                
        return issues[:10]  # Limitar a 10 issues para no saturar el reporte
        
    def _calculate_score(self, validations):
        """Calcular score general basado en todas las validaciones"""
        scores = [v.get('score', 0) for v in validations.values()]
        return sum(scores) / len(scores) if scores else 0
        
    def _save_validation_result(self, result):
        """Guardar resultado de validación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{result['spider_name']}_{timestamp}.json"
        filepath = self.test_results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    def print_validation_report(self, result):
        """Imprimir reporte de validación detallado"""
        if not result:
            return
            
        print("\\n" + "=" * 80)
        print(f"🔍 VALIDACIÓN PROFUNDA: {result['spider_name']}")
        print("=" * 80)
        
        # Score general
        score = result['score']
        if score >= 90:
            status = "🟢 EXCELENTE"
        elif score >= 75:
            status = "🟡 BUENO"
        elif score >= 60:
            status = "🟠 REGULAR"
        else:
            status = "🔴 NECESITA MEJORAS"
            
        print(f"📊 SCORE GENERAL: {score:.1f}/100 - {status}")
        print(f"📄 Items analizados: {result['items_analyzed']}")
        print(f"⏰ Timestamp: {result['timestamp']}")
        
        # Resultados por categoría
        print("\\n🔍 RESULTADOS POR CATEGORÍA:")
        validations = result['validations']
        
        for category, validation in validations.items():
            score = validation.get('score', 0)
            issues_count = len(validation.get('issues', []))
            
            if score >= 90:
                icon = "🟢"
            elif score >= 75:
                icon = "🟡"
            elif score >= 60:
                icon = "🟠"
            else:
                icon = "🔴"
                
            print(f"   {icon} {category.replace('_', ' ').title():20} | {score:5.1f}/100 | {issues_count:2} issues")
            
        # Issues principales
        all_issues = []
        for validation in validations.values():
            all_issues.extend(validation.get('issues', []))
            
        if all_issues:
            print(f"\\n⚠️  ISSUES ENCONTRADOS ({len(all_issues)}):")
            for issue in all_issues[:10]:  # Solo primeros 10
                print(f"   • {issue}")
            if len(all_issues) > 10:
                print(f"   ... y {len(all_issues) - 10} issues más")
                
        print("=" * 80)


def main():
    """Función principal"""
    validator = AdvancedSpiderValidator()
    
    if len(sys.argv) < 2:
        print("🔍 Sistema de Validación Avanzada para Spiders")
        print("")
        print("USO:")
        print("   python advanced_test.py <spider_name> --deep    # Validación profunda")
        print("   python advanced_test.py --validate-all         # Validar todos los spiders")
        print("")
        print("EJEMPLOS:")
        print("   python advanced_test.py motodelta --deep")
        print("   python advanced_test.py --validate-all")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == '--validate-all':
        print("🔍 Ejecutando validación profunda para todos los spiders")
        print("=" * 80)
        
        results = {}
        for spider_name in validator.spider_configs.keys():
            print(f"\\n📊 Validando {spider_name}...")
            result = validator.run_deep_validation(spider_name, max_items=30)
            results[spider_name] = result
            
            if result:
                score = result['score']
                issues = sum(len(v.get('issues', [])) for v in result['validations'].values())
                print(f"   Score: {score:.1f}/100, Issues: {issues}")
                
        # Resumen final
        print("\\n" + "=" * 80)
        print("📊 RESUMEN DE VALIDACIONES")
        print("=" * 80)
        
        for spider_name, result in results.items():
            if result:
                score = result['score']
                if score >= 90:
                    icon = "🟢"
                elif score >= 75:
                    icon = "🟡"
                elif score >= 60:
                    icon = "🟠"
                else:
                    icon = "🔴"
                print(f"{icon} {spider_name:15} | {score:5.1f}/100")
                
    else:
        # Validación de spider específico
        spider_name = command
        deep = '--deep' in sys.argv
        
        if spider_name not in validator.spider_configs:
            print(f"❌ Spider '{spider_name}' no configurado")
            print(f"Spiders disponibles: {', '.join(validator.spider_configs.keys())}")
            sys.exit(1)
            
        max_items = 30 if deep else 15
        result = validator.run_deep_validation(spider_name, max_items)
        
        if result:
            validator.print_validation_report(result)


if __name__ == "__main__":
    main()
