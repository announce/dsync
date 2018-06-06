import logging
import sys


class Logger:
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    AVAILABLE_LEVEL = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARN': logging.WARNING,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }

    def __init__(self):
        pass

    @classmethod
    def create(cls, name, level=logging.INFO, fmt=FORMAT):
        root_logger = logging.getLogger(name)
        root_logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        return root_logger

    @classmethod
    def available_levels(cls):
        return cls.AVAILABLE_LEVEL.values()
