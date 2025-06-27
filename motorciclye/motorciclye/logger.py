import logging
from logging.handlers import RotatingFileHandler
from .config import load_config
cfg = load_config().get('logging', {})

def get_logger(name=__name__, filename=None):
    logger = logging.getLogger(name)
    log_filename = filename or cfg.get('filename', 'app.log')
    max_bytes = cfg.get('max_bytes', 10485760)
    backup_count = cfg.get('backup_count', 10)

    if not logger.handlers:
        handler = RotatingFileHandler(log_filename, maxBytes=max_bytes, backupCount=backup_count)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger