import logging
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = str(os.getenv("CONFIG_PATH"))

logger = logging.basicConfig(filename=f'{CONFIG_PATH}/logs', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')