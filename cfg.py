import logging
import yaml

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('')

with open('cfg.yml', 'r') as f:
    REDDIT_CONFIG = yaml.safe_load(f.read())['reddit']
