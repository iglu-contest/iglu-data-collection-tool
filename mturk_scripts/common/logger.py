import logging
import os


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        local_formatter = logging.Formatter(log_fmt)
        return local_formatter.format(record)


LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()


def get_stdout_handler():
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    stdout_handler = None
    if os.getenv('LOGCOLOR', 'FALSE').upper() != 'TRUE':
        logging.basicConfig(format=formatter, level=LOGLEVEL)
    else:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(CustomFormatter(formatter))


def get_logger(name: str) -> logging.Logger:
    stdout_handler = get_stdout_handler()
    logger = logging.getLogger(name)
    if stdout_handler is not None:
        logger.setLevel(LOGLEVEL)
        logger.addHandler(stdout_handler)
    return logger


def set_logger_level(logger_prefix, new_level=logging.WARNING):
    for logger_name in logging.Logger.manager.loggerDict.keys():
        if logger_prefix in logger_name:
            logging.getLogger(logger_name).setLevel(new_level)
