from datetime import datetime

import logging
from colorlog import ColoredFormatter

current_time = datetime.now().strftime("%H_%M_%S %d-%m-%Y")
LOG_LEVEL = logging.INFO
LOG_FORMAT = " %(log_color)s%(asctime)s %(levelname)s %(filename)s[%(lineno)d]: %(message)s%(reset)s"
formatter_stream = ColoredFormatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
formatter_file = logging.Formatter(fmt="%(asctime)s %(levelname)s %(filename)s[%(lineno)d]: %(message)s",
                                   datefmt="%Y-%m-%d %H:%M:%S")

stream_handler = logging.StreamHandler()
stream_handler.setLevel(LOG_LEVEL)
stream_handler.setFormatter(formatter_stream)

file_handler = logging.FileHandler(filename=f"logs/{current_time}.log", mode='w', encoding="utf-8")
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter_file)

logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, stream_handler])

logger = logging.getLogger(__name__)
