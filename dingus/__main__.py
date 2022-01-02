from dingus.processor import Processor
import dingus.utils as utils
from dingus.types.keys import PrivateKey

import logging
import os       

def start():
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG) 


    # sk = utils.passphrase_to_sk("ale ale ale")
    # # sk.to_json()
    # print(sk.to_public_key().to_address())
    # print(sk.to_public_key().to_address().to_avatar())
    processor = Processor(logger)
    
