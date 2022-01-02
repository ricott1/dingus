import dingus.processor as processor
import dingus.utils as utils
from dingus.types.keys import PrivateKey

import logging
import os


        

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG) 


    # sk = utils.passphrase_to_sk("ale ale ale")
    # # sk.to_json()
    # print(sk.to_public_key().to_address())
    # print(sk.to_public_key().to_address().to_avatar())
    processor = processor.Processor(logger)
    
