#!/usr/bin/env python3
"""
Validador de completitud de campos para spiders.

Este script verifica que todos los productos extraídos contengan
todos los campos requeridos y que estén correctamente formateados.

Uso:
    python field_validator.py motodelta
    python field_validator.py --all
    python field_validator.py --detailed motodelta
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Agregar el path del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class FieldCompletenessValidator:
    """Validador de completitud de campos"""
    
    def __init__(self):
        self.results_dir = project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Campos requeridos para todos los productos
        self.required_fields = [
            'menu_name',
            'menu_url', 
            'product_url',
            'name',
            'price',
            'brand',
            'attrs',
            'discount_text',
            'images',
            'description',
            'category_name',
            'category_url',
            'source'
        ]
        
        # Campos críticos (no pueden estar vacíos)
        self.critical_fields = [
            'product_url',
            'name',
            'price'
        ]
        
        # Campos opcionales pero recomendados
        self.recommended_fields = [
            'brand',
            'images',
            'category_name',
            'description'
        ]
        
    def validate_spider(self, spider_name, max_items=30):
        """Validar completitud de campos para un spider"""
        print(f"🔍 Validando completitud de campos para: {spider_name}")
        print("-" * 60)
        
        # Ejecutar spider
        result = self._run_spider(spider_name, max_items)
        if not result:
            print("❌ Error ejecutando spider")
            return None
            
        items = result.get('items', [])
        products = [item for item in items if item.get('item_type') == 'product']
        
        if not products:
            print("❌ No se encontraron productos")
            return None
            
        print(f"📦 Analizando {len(products)} productos...")
        
        # Analizar completitud
        analysis = self._analyze_completeness(products)
        
        # Imprimir reporte
        self._print_completeness_report(spider_name, analysis)
        
        # Guardar reporte detallado
        self._save_detailed_report(spider_name, analysis, products)
        
        return analysis
        
    def validate_all_spiders(self):
        """Validar todos los spiders"""
        spiders = ['motodelta', 'gaonamotos', 'masxmoto', 'motojose', 'motoscba', 'shopavantmotos', 'motosport']
        
        print("🔍 Validando completitud para todos los spiders")
        print("=" * 70)
        
        results = {}
        
        for spider_name in spiders:
            print(f"\\n📊 Validando {spider_name}...")
            analysis = self.validate_spider(spider_name, max_items=20)
            results[spider_name] = analysis
            
        # Resumen comparativo
        print("\\n" + "=" * 80)
        print("📊 RESUMEN COMPARATIVO DE COMPLETITUD")
        print("=" * 80)
        
        self._print_comparative_summary(results)
        
        return results
        
    def _run_spider(self, spider_name, max_items):
        """Ejecutar spider y obtener resultados"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = self.results_dir / f"{spider_name}_fields_{timestamp}.json"
        
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", spider_name,
            "-s", f"CLOSESPIDER_ITEMCOUNT={max_items}",
            "-s", "ROBOTSTXT_OBEY=False",
            "-s", "DOWNLOAD_DELAY=0.5",
            "-s", "LOG_LEVEL=ERROR",
            "-o", str(output_file)
        ]
        
        try:
            subprocess.run(cmd, cwd=str(project_root), capture_output=True, timeout=180)
            
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    
                # Limpiar archivo temporal
                output_file.unlink()
                
                return {'items': items if isinstance(items, list) else [items]}
        except:
            pass
            
        return None
        
    def _analyze_completeness(self, products):
        """Analizar completitud de campos"""
        analysis = {
            'total_products': len(products),
            'field_stats': {},
            'critical_issues': [],
            'recommended_missing': [],
            'completeness_score': 0,
            'products_100_complete': 0,
            'products_critical_complete': 0
        }
        
        # Analizar cada campo
        for field in self.required_fields:
            stats = self._analyze_field(products, field)
            analysis['field_stats'][field] = stats
            
            # Identificar issues críticos
            if field in self.critical_fields and stats['empty_percentage'] > 0:
                analysis['critical_issues'].append({
                    'field': field,
                    'empty_count': stats['empty_count'],
                    'empty_percentage': stats['empty_percentage']
                })
                
            # Identificar campos recomendados faltantes
            if field in self.recommended_fields and stats['empty_percentage'] > 50:
                analysis['recommended_missing'].append({
                    'field': field,
                    'empty_percentage': stats['empty_percentage']
                })
                
        # Calcular score de completitud general
        total_completeness = sum(stats['completeness'] for stats in analysis['field_stats'].values())
        analysis['completeness_score'] = total_completeness / len(self.required_fields)
        
        # Contar productos 100% completos
        for product in products:
            if self._is_product_complete(product, self.required_fields):
                analysis['products_100_complete'] += 1
            if self._is_product_complete(product, self.critical_fields):
                analysis['products_critical_complete'] += 1
                
        return analysis
        
    def _analyze_field(self, products, field):
        """Analizar un campo específico"""
        total = len(products)
        present_count = 0
        empty_count = 0
        valid_count = 0
        
        values = []
        
        for product in products:
            value = product.get(field)
            
            # Campo presente
            if field in product:
                present_count += 1
                
                # Campo con valor válido
                if self._is_value_valid(value, field):
                    valid_count += 1
                    values.append(value)
                else:
                    empty_count += 1
            else:
                empty_count += 1
                
        return {
            'present_count': present_count,
            'empty_count': empty_count,
            'valid_count': valid_count,
            'present_percentage': (present_count / total) * 100,
            'empty_percentage': (empty_count / total) * 100,
            'valid_percentage': (valid_count / total) * 100,
            'completeness': (valid_count / total) * 100,
            'sample_values': values[:3] if values else [],
            'unique_values_count': len(set(str(v) for v in values)) if values else 0
        }
        
    def _is_value_valid(self, value, field):
        """Verificar si un valor es válido para un campo"""
        if value is None:
            return False
            
        if isinstance(value, str) and value.strip() == "":
            return False
            
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
            
        # Validaciones específicas por tipo de campo
        if field in ['menu_url', 'product_url', 'category_url']:
            return isinstance(value, str) and value.startswith(('http://', 'https://'))
            
        if field == 'price':
            return isinstance(value, (int, float)) and value > 0
            
        if field == 'images':
            return isinstance(value, list) and len(value) > 0
            
        if field == 'attrs':
            return isinstance(value, dict)
            
        if field == 'source':
            return isinstance(value, bool)
            
        return True
        
    def _is_product_complete(self, product, required_fields):
        """Verificar si un producto está completo"""
        for field in required_fields:
            if not self._is_value_valid(product.get(field), field):
                return False
        return True
        
    def _print_completeness_report(self, spider_name, analysis):
        """Imprimir reporte de completitud"""
        print(f"\\n📊 REPORTE DE COMPLETITUD: {spider_name}")
        print("=" * 60)
        
        total = analysis['total_products']
        score = analysis['completeness_score']
        
        # Score general
        if score >= 95:
            status = "🟢 EXCELENTE"
        elif score >= 85:
            status = "🟡 BUENO"
        elif score >= 70:
            status = "🟠 REGULAR"
        else:
            status = "🔴 DEFICIENTE"
            
        print(f"📈 SCORE GENERAL: {score:.1f}% - {status}")
        print(f"📦 Productos analizados: {total}")
        print(f"✅ Productos 100% completos: {analysis['products_100_complete']} ({(analysis['products_100_complete']/total)*100:.1f}%)")
        print(f"🔑 Productos con campos críticos: {analysis['products_critical_complete']} ({(analysis['products_critical_complete']/total)*100:.1f}%)")
        
        # Campos críticos faltantes
        if analysis['critical_issues']:
            print(f"\\n🚨 ISSUES CRÍTICOS:")
            for issue in analysis['critical_issues']:
                field = issue['field']
                count = issue['empty_count']
                percentage = issue['empty_percentage']
                print(f"   ❌ {field}: {count} productos ({percentage:.1f}%) sin valor")
                
        # Resumen por campo
        print(f"\\n📋 COMPLETITUD POR CAMPO:")
        
        for field in self.required_fields:
            stats = analysis['field_stats'][field]
            completeness = stats['completeness']
            
            if completeness >= 95:
                icon = "🟢"
            elif completeness >= 85:
                icon = "🟡"
            elif completeness >= 70:
                icon = "🟠"
            else:
                icon = "🔴"
                
            critical_mark = " 🔑" if field in self.critical_fields else ""
            recommended_mark = " ⭐" if field in self.recommended_fields else ""
            
            print(f"   {icon} {field:<15} {completeness:5.1f}% ({stats['valid_count']:3}/{total:3}){critical_mark}{recommended_mark}")
            
        print("\\n   🔑 = Campo crítico")
        print("   ⭐ = Campo recomendado")
        
    def _print_comparative_summary(self, results):
        """Imprimir resumen comparativo"""
        print(f"{'Spider':<15} {'Score':<8} {'100% Completos':<15} {'Críticos OK':<12} {'Issues':<6}")
        print("-" * 70)
        
        for spider_name, analysis in results.items():
            if not analysis:
                print(f"{spider_name:<15} {'ERROR':<8}")
                continue
                
            score = analysis['completeness_score']
            total = analysis['total_products']
            complete_100 = analysis['products_100_complete']
            critical_ok = analysis['products_critical_complete']
            critical_issues = len(analysis['critical_issues'])
            
            complete_100_pct = (complete_100 / total) * 100 if total > 0 else 0
            critical_ok_pct = (critical_ok / total) * 100 if total > 0 else 0
            
            print(f"{spider_name:<15} {score:6.1f}% {complete_100:3}/{total:3} ({complete_100_pct:4.1f}%) {critical_ok:3}/{total:3} ({critical_ok_pct:4.1f}%) {critical_issues:5}")
            
        print("\\n🏆 Ranking por completitud:")
        
        # Ordenar por score
        sorted_results = [(name, analysis) for name, analysis in results.items() if analysis]
        sorted_results.sort(key=lambda x: x[1]['completeness_score'], reverse=True)
        
        for i, (spider_name, analysis) in enumerate(sorted_results[:3], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            score = analysis['completeness_score']
            print(f"   {medal} {spider_name}: {score:.1f}%")
            
    def _save_detailed_report(self, spider_name, analysis, products):
        """Guardar reporte detallado en JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"completeness_{spider_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        detailed_report = {
            'spider_name': spider_name,
            'timestamp': timestamp,
            'analysis': analysis,
            'sample_incomplete_products': []
        }
        
        # Agregar muestra de productos incompletos
        incomplete_products = []
        for i, product in enumerate(products):
            if not self._is_product_complete(product, self.required_fields):
                missing_fields = []
                for field in self.required_fields:
                    if not self._is_value_valid(product.get(field), field):
                        missing_fields.append(field)
                        
                incomplete_products.append({
                    'index': i,
                    'name': product.get('name', 'N/A'),
                    'url': product.get('product_url', 'N/A'),
                    'missing_fields': missing_fields
                })
                
        detailed_report['sample_incomplete_products'] = incomplete_products[:10]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)
            
        print(f"\\n💾 Reporte detallado guardado: {filename}")


def main():
    """Función principal"""
    validator = FieldCompletenessValidator()
    
    if len(sys.argv) < 2:
        print("🔍 VALIDADOR DE COMPLETITUD DE CAMPOS")
        print("")
        print("USO:")
        print("   python field_validator.py <spider_name>    # Validar un spider")
        print("   python field_validator.py --all            # Validar todos los spiders")
        print("   python field_validator.py --detailed <name> # Análisis detallado")
        print("")
        print("CAMPOS REQUERIDOS:")
        for field in validator.required_fields:
            critical = " 🔑" if field in validator.critical_fields else ""
            recommended = " ⭐" if field in validator.recommended_fields else ""
            print(f"   • {field}{critical}{recommended}")
        print("")
        print("   🔑 = Campo crítico (no puede estar vacío)")
        print("   ⭐ = Campo recomendado")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == '--all':
        validator.validate_all_spiders()
    elif command == '--detailed':
        if len(sys.argv) < 3:
            print("❌ Especifica el nombre del spider para análisis detallado")
            sys.exit(1)
        spider_name = sys.argv[2]
        validator.validate_spider(spider_name, max_items=50)
    else:
        spider_name = command
        validator.validate_spider(spider_name)


if __name__ == "__main__":
    main()
