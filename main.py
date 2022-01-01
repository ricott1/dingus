import dingus.processor as processor
import dingus.utils as utils
from dingus.types.keys import PrivateKey

import logging
import os


        

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG) 
    processor = processor.Processor(logger)
    
