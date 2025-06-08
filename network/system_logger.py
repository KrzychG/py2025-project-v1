import logging
import os

os.makedirs("logs/system", exist_ok=True)

logging.basicConfig(
    filename="logs/system/system.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

system_logger = logging.getLogger("system")
