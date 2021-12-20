import dingus.processor as processor

import logging
import os
import signal


        

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG)
    
    processor = processor.Processor(logger)
    signal.signal(signal.SIGINT, processor.close)
    
    



