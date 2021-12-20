import dingus.utils as utils
from dingus.constants import *
import dingus.transaction as tx
import dingus.processor as processor

import logging
import os
import signal


        

if __name__ == "__main__":
    params = {
        "senderPublicKey": utils.random_public_key().encode(),
        "nonce": 0,
        "fee": int(0.5 * LSK),
        "asset": {
            "amount": int(3 * LSK),
            "recipientAddress": utils.random_address(),
            "data": ""
        }   
    }

    trs = tx.BalanceTransfer.fromDict(params)
    trs.nonce=166
    
    passphrase = "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
    trs.sign(utils.passphrase_to_sk(passphrase))
    # print(trs)
    # trs.send()
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG)
    
    processor = processor.Processor(logger)
    signal.signal(signal.SIGINT, processor.close)
    
    



