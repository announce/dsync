import logging
import sys


class Logger:
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __init__(self):
        pass

    @classmethod
    def create(cls, name, level=logging.DEBUG, fmt=FORMAT):
        root_logger = logging.getLogger(name)
        root_logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        return root_logger
