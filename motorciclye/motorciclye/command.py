#!/usr/bin/env python3
"""
Comando para reenviar datos desde archivos JSON a RabbitMQ.

Uso:
    python command.py resend <source> <timestamp>
    
Ejemplo:
    python command.py resend motodelta 20250625131936
    
Este script:
1. Lee el archivo build/<source>/<timestamp>/<source>.json
2. Publica cada fila en RabbitMQ usando la misma lógica que product_pipeline
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Agregar el path del proyecto para importar los módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motorciclye.rabbit_connection import get_rabbit_connection, publish_message
from motorciclye.config import load_config


class ResendCommand:
    """Comando para reenviar datos desde archivos JSON a RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.processed_count = 0
        self.error_count = 0
    
    def setup_rabbitmq(self):
        """Configurar conexión a RabbitMQ"""
        try:
            self.connection = get_rabbit_connection()
            self.channel = self.connection.channel()
            print("✓ Conexión a RabbitMQ establecida")
        except Exception as e:
            print(f"✗ Error conectando a RabbitMQ: {e}")
            sys.exit(1)
    
    def cleanup_rabbitmq(self):
        """Limpiar conexión a RabbitMQ"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
        print("✓ Conexión a RabbitMQ cerrada")
    
    def find_json_file(self, source, timestamp):
        """Buscar el archivo JSON en el directorio build"""
        # Buscar en el directorio actual
        json_file = Path(f"build/{source}/{timestamp}/{source}.json")
        
        if json_file.exists():
            return json_file
        
        # Buscar en el directorio motorciclye
        json_file = Path(f"motorciclye/build/{source}/{timestamp}/{source}.json")
        
        if json_file.exists():
            return json_file
        
        # Buscar en directorios padre
        for parent in [Path(".").parent, Path(".").parent.parent]:
            json_file = parent / f"build/{source}/{timestamp}/{source}.json"
            if json_file.exists():
                return json_file
            
            json_file = parent / f"motorciclye/build/{source}/{timestamp}/{source}.json"
            if json_file.exists():
                return json_file
        
        return None
    
    def load_json_data(self, json_file):
        """Cargar datos del archivo JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✓ Archivo JSON cargado: {json_file}")
            
            # Si es una lista, devolver tal como está
            if isinstance(data, list):
                print(f"✓ Encontrados {len(data)} elementos en el archivo")
                return data
            
            # Si es un objeto, convertir a lista
            elif isinstance(data, dict):
                print("✓ Convirtiendo objeto a lista")
                return [data]
            
            else:
                print(f"✗ Formato de archivo no soportado: {type(data)}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"✗ Error parseando JSON: {e}")
            return []
        except Exception as e:
            print(f"✗ Error leyendo archivo: {e}")
            return []
    
    def publish_item_to_rabbitmq(self, item, source):
        """Publicar un item en RabbitMQ (equivalente a _publish_product_to_rabbitmq)"""
        cfg = load_config()['rabbitmq']
        
        try:
            message = json.dumps(item, ensure_ascii=False)
            routing_key = f'{cfg["routing_key_prefix"]}.products.{source}'
            publish_message(self.channel, routing_key, message)
            
            self.processed_count += 1
            item_name = item.get('name', item.get('title', 'Sin nombre'))
            print(f"✓ [{self.processed_count}] Publicado: {item_name}")
            
        except Exception as e:
            self.error_count += 1
            print(f"✗ Error publicando item: {e}")
    
    def resend_command(self, source, timestamp):
        """Ejecutar comando resend"""
        print(f"🔄 Iniciando resend para source='{source}' timestamp='{timestamp}'")
        print("-" * 60)
        
        # 1. Buscar archivo JSON
        json_file = self.find_json_file(source, timestamp)
        if not json_file:
            print(f"✗ No se encontró el archivo: build/{source}/{timestamp}/{source}.json")
            print("✗ Ubicaciones buscadas:")
            print(f"   - build/{source}/{timestamp}/{source}.json")
            print(f"   - motorciclye/build/{source}/{timestamp}/{source}.json")
            return False
        
        # 2. Cargar datos
        data = self.load_json_data(json_file)
        if not data:
            print("✗ No hay datos para procesar")
            return False
        
        # 3. Configurar RabbitMQ
        self.setup_rabbitmq()
        
        # 4. Publicar cada item
        print(f"🚀 Publicando {len(data)} elementos...")
        print("-" * 60)
        
        start_time = datetime.now()
        
        for item in data:
            self.publish_item_to_rabbitmq(item, source)
        
        end_time = datetime.now()
        elapsed = end_time - start_time
        
        # 5. Resumen
        print("-" * 60)
        print(f"📊 RESUMEN:")
        print(f"   • Total procesados: {self.processed_count}")
        print(f"   • Errores: {self.error_count}")
        print(f"   • Tiempo: {elapsed.total_seconds():.1f}s")
        print(f"   • Velocidad: {self.processed_count/elapsed.total_seconds():.1f} items/s")
        
        # 6. Limpiar conexión
        self.cleanup_rabbitmq()
        
        return self.error_count == 0


def show_help():
    """Mostrar ayuda del comando"""
    print("🤖 Comando para reenviar datos a RabbitMQ")
    print("")
    print("USAGE:")
    print("   python command.py resend <source> <timestamp>")
    print("")
    print("ARGUMENTOS:")
    print("   source     - Nombre del spider/fuente (ej: motodelta)")
    print("   timestamp  - Timestamp del directorio (ej: 20250625131936)")
    print("")
    print("EJEMPLO:")
    print("   python command.py resend motodelta 20250625131936")
    print("")
    print("DESCRIPCIÓN:")
    print("   Este comando lee el archivo build/<source>/<timestamp>/<source>.json")
    print("   y publica cada elemento en RabbitMQ usando la misma lógica que")
    print("   el pipeline de productos.")


def main():
    """Función principal del comando"""
    
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "help" or command == "-h" or command == "--help":
        show_help()
        return
    
    elif command == "resend":
        if len(sys.argv) != 4:
            print("✗ Error: Comando resend requiere 2 argumentos")
            print("")
            print("USAGE: python command.py resend <source> <timestamp>")
            print("EJEMPLO: python command.py resend motodelta 20250625131936")
            sys.exit(1)
        
        source = sys.argv[2]
        timestamp = sys.argv[3]
        
        # Validar timestamp
        try:
            datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        except ValueError:
            print(f"✗ Error: Timestamp inválido '{timestamp}'")
            print("   Formato esperado: YYYYMMDDHHMMSS (ej: 20250625131936)")
            sys.exit(1)
        
        # Ejecutar comando
        resend_cmd = ResendCommand()
        success = resend_cmd.resend_command(source, timestamp)
        
        if success:
            print("✅ Resend completado exitosamente")
            sys.exit(0)
        else:
            print("❌ Resend falló")
            sys.exit(1)
    
    else:
        print(f"✗ Comando desconocido: '{command}'")
        print("")
        print("Comandos disponibles:")
        print("   resend - Reenviar datos desde archivo JSON a RabbitMQ")
        print("   help   - Mostrar esta ayuda")
        sys.exit(1)


if __name__ == "__main__":
    main()
