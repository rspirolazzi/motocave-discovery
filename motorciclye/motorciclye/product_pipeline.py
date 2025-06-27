import json
import time
from datetime import datetime
from .rabbit_connection import get_rabbit_connection, publish_message
from .config import load_config

class ProductProcessedPipeline:
    """Pipeline que publica productos en RabbitMQ"""
    
    def __init__(self):
        self.processed_count = 0
        self.connection = get_rabbit_connection()
        self.channel = self.connection.channel()
        
    
    def open_spider(self, spider):
        """Se ejecuta cuando se abre el spider"""
        spider.logger.info(f"ProductProcessedPipeline: Iniciando publicación de productos para spider {spider.name}")
    
    def process_item(self, item, spider):
        """Se ejecuta por cada item. Solo procesa items de tipo 'product'"""
        # Solo procesar si es un producto
        if item.get('item_type') == 'product':
            self.processed_count += 1
            
            # Log básico
            spider.logger.info(f"Pipeline: Procesando producto #{self.processed_count}: {item.get('name', 'Sin nombre')}")
            
            # Publicar en RabbitMQ
            self._publish_product_to_rabbitmq(item, spider)
        
        return item
    
    def _publish_product_to_rabbitmq(self, product_item, spider):
        cfg = load_config()['rabbitmq']

        try:
            message = json.dumps(product_item, ensure_ascii=False)
            routing_key = f'{cfg["routing_key_prefix"]}.products.{spider.name}'
            publish_message(self.channel, routing_key, message)
            spider.logger.info(f"Publicado producto en RabbitMQ: {product_item.get('name', 'Sin nombre')}")
        except Exception as e:
            spider.logger.error(f"Error publicando producto: {e}")
        
    
    def close_spider(self, spider):
        """Se ejecuta al finalizar el spider"""
        if self.processed_count > 0:
            spider.logger.info(f"Pipeline: Total productos publicados en RabbitMQ: {self.processed_count}")
        self.channel.close()
        self.connection.close()
