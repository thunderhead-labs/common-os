import datetime
import os
import logging
import logaugment

from logging.handlers import RotatingFileHandler


def process_record(record):
    now = datetime.datetime.utcnow()
    try:
        delta = now - process_record.now
    except AttributeError:
        delta = 0
    process_record.now = now

    try:
        formatted = "{}ms".format(round(delta.total_seconds() * 1000), 2)
    except AttributeError:
        formatted = "0ms"
    return {"time_since_last": formatted}


def get_logger(
    path: str, service_name: str, name: str, serverless: bool = False
) -> logging.Logger:
    env = os.environ.get("env") if os.environ.get("env") else "dev"
    logger = logging.getLogger(f"{name}_{env}")
    logger.setLevel(logging.DEBUG)
    if env != "dev" and not serverless:
        fh = RotatingFileHandler(
            f"{path}/{name}_{env}.log", backupCount=10, maxBytes=200000000
        )
    else:
        fh = logging.StreamHandler()
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        f"[%(asctime)s][service={service_name}][log=%(name)s][LD=%(time_since_last)s][%(levelname)s]: %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logaugment.add(logger, process_record)
    return logger
