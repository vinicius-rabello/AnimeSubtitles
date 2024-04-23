import logging

logger = logging
level = logging.INFO
logger.basicConfig(
    format='%(asctime)s - %(message)s', level=level,
    handlers=[logging.StreamHandler()]
)
