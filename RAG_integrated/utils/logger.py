import logging
import colorlog
from datetime import datetime, timezone, timedelta
import os

# Define Singapore Time (SGT) as UTC+8
SGT = timezone(timedelta(hours=8))

class SGTimeFormatter(colorlog.ColoredFormatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone(SGT)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " SGT"  # Trim microseconds to 3 digits

    def format(self, record):
        # Add file:function:line info
        record.filename_func_line = f"{record.filename}:{record.funcName}:{record.lineno}"
        return super().format(record)

# Log format: [TIME] | [LEVEL] | [FILE:FUNC:LINE] - [MESSAGE]
log_format = (
    "%(green)s%(asctime)s %(reset)s| "
    "%(log_color)s%(levelname)-8s %(reset)s| "
    "%(cyan)s%(filename_func_line)s %(reset)s- "
    "%(white)s%(message)s"
)

formatter = SGTimeFormatter(
    fmt=log_format,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# Handler and logger setup
handler = colorlog.StreamHandler()
handler.setFormatter(formatter)

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False