import pika
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from .config import load_config

def get_rabbit_connection():
    cfg = load_config()['rabbitmq']
    credentials = pika.PlainCredentials(cfg['user'], cfg['password'])
    parameters = pika.ConnectionParameters(
        host=cfg['host'],
        port=cfg['port'],
        virtual_host=cfg.get('vhost', '/'),
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

def publish_message(channel, routing_key, message):
    cfg = load_config()['rabbitmq']
    channel.basic_publish(
        exchange=cfg['exchange'],
        routing_key=routing_key,
        body=message
    )
