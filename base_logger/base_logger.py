import logging

logger = logging
level = logging.INFO
logger.basicConfig(
    format='%(name)s %(asctime)s [%(levelname)s] - %(message)s', level=level,
    handlers=[logging.StreamHandler()]
)
