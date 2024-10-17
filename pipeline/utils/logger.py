import logging

from time import gmtime


def create_logger():
    log_format = f"[%(levelname)s %(funcName)s:%(lineno)d] %(message)s"
    logging.Formatter.converter = gmtime
    logging.basicConfig(
        format=log_format,
        level=logging.INFO,
    )
    logger = logging.getLogger(__name__)
    return logger


create_logger()
