from dingus.processor import Processor

import logging
import os       
import argparse
from pathlib import Path

def start():
    try:
        os.remove("./dingus.log")
    except:
        pass
    logging.basicConfig(filename = "./dingus.log", level=logging.DEBUG) 

    parser = argparse.ArgumentParser(description='Dingus arguments.')

    parser.add_argument(
        "-n", "--network", type=str, nargs=1, default=["mainnet"],
        choices = ["mainnet", "testnet"],
        help = "network connection: (choose from 'mainnet', 'testnet')"
    )

    parser.add_argument(
        "-p", "--base-path", type=str, nargs=1, default=[str(Path.home()) + "/.dingus"],
        help = "path to store dingus data files"
    )

    args = parser.parse_args()
    os.environ["DINGUS_NETWORK"] = args.network[0]
    os.environ["DINGUS_BASE_PATH"] = args.base_path[0]
    Path(f"{os.environ['DINGUS_BASE_PATH']}/accounts").mkdir(parents=True, exist_ok=True)

    os.environ["DINGUS_NETWORK_ID"] = ""
    os.environ["DINGUS_BLOCK_TIME"] = "10"
    os.environ["DINGUS_MIN_FEE_PER_BYTE"] = "0"
    processor = Processor()
