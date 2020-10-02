import logging
from logzero import setup_logger

loglevel: int = logging.WARNING


def setup(loglvl: int = loglevel) -> logging.Logger:
    global logger
    lg: logging.Logger = setup_logger(name="url_metadata", level=loglvl)
    logger = lg
    return lg


logger: logging.Logger = setup()
