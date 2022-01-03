from dingus.processor import Processor

import logging
import os       
import argparse

def start():
    logger = logging.getLogger(__name__)
    os.remove("dingus.log")
    logging.basicConfig(filename = "dingus.log", level=logging.DEBUG) 

    parser = argparse.ArgumentParser(description='Dingus arguments.')
    parser.add_argument(
        "-network", type=str, nargs=1, default=["mainnet"],
        choices = ["mainnet", "testnet"],
        help="network connection: (choose from 'mainnet', 'testnet')"
    )

    args = parser.parse_args()
    os.environ["DINGUS_NETWORK"] = args.network[0]
    processor = Processor(logger)
