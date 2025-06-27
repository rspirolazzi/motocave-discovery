import json
import time
from datetime import datetime
from .rabbit_connection import get_rabbit_connection, publish_message
from .config import load_config

class SourceProcessedPipeline:
    """Pipeline que publica información de fuente en RabbitMQ"""
    
    def __init__(self):
        self.sources_processed = 0
        self.connection = get_rabbit_connection()
        self.channel = self.connection.channel()
        
    
    def open_spider(self, spider):
        """Se ejecuta cuando se abre el spider"""
        spider.logger.info(f"SourceProcessedPipeline: Iniciando publicación de fuentes para spider {spider.name}")
    
    def process_item(self, item, spider):
        """Se ejecuta por cada item. Solo procesa items de tipo 'source'"""
        # Solo procesar si es información de fuente
        if item.get('item_type') == 'source':
            self.sources_processed += 1
            
            # Log básico
            spider.logger.info(f"SourcePipeline: Procesando fuente #{self.sources_processed}: {item.get('name', 'Sin nombre')}")
            
            # Publicar en RabbitMQ
            self._publish_source_to_rabbitmq(item, spider)
            
        return item
    
    def _publish_source_to_rabbitmq(self, source_item, spider):
        """
        Publica cada fuente en el exchange de RabbitMQ.
        """
        cfg = load_config()['rabbitmq']

        try:
            source_message = json.dumps(source_item, ensure_ascii=False)
            routing_key = f'{cfg["routing_key_prefix"]}.sources'
            publish_message(self.channel, routing_key, source_message)
            spider.logger.info(f"Publicado fuente en RabbitMQ: {source_item.get('name', 'Sin nombre')}")
        except Exception as e:
            spider.logger.error(f"Error publicando fuente: {e}")
        
    
    def close_spider(self, spider):
        """Se ejecuta al finalizar el spider"""
        if self.sources_processed > 0:
            spider.logger.info(f"SourcePipeline: Total fuentes publicadas en RabbitMQ: {self.sources_processed}")
        self.channel.close()
        self.connection.close()
