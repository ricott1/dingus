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



    import argparse

    parser = argparse.ArgumentParser(description='Dingus arguments.')
    parser.add_argument(
        "-network", type=str, nargs=1, default=["mainnet"],
        choices = ["mainnet", "testnet"],
        help="network connection: (choose from 'mainnet', 'testnet')"
    )

    args = parser.parse_args()
    os.environ["DINGUS_NETWORK"] = args.network[0]
    processor = Processor(logger)
