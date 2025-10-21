import logging

log_format = '[%(levelname)s] | [%(filename)s] | %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)