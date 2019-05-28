import logging
import os

if not os.path.exists('logs/'):
    os.mkdir('logs')

logger = logging.getLogger('Fonz')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('./logs/logs.txt')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

GLOBAL_LOGGER = logger