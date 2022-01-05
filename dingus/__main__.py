from dingus.processor import Processor

import logging
import os       
import argparse
from pathlib import Path

def start():

    parser = argparse.ArgumentParser(description='Dingus arguments.')

    parser.add_argument(
        "-n", "--network", type=str, nargs=1, default=["testnet"],
        choices = ["mainnet", "testnet"],
        help = "network connection: (choose from 'mainnet', 'testnet')"
    )

    parser.add_argument(
        "-p", "--base-path", type=str, nargs=1, default=[str(Path.home()) + "/.dingus"],
        help = "path to store dingus data files"
    )

    parser.add_argument(
        "-l", "--log-path", type=str, nargs=1, default=[str(Path.home()) + "/.dingus/dingus.log"],
        help = "path to store log file"
    )

    args = parser.parse_args()

    Path(args.log_path[0]).unlink(missing_ok=True)
    logging.basicConfig(filename = args.log_path[0], level=logging.DEBUG) 

    os.environ["DINGUS_NETWORK"] = args.network[0]
    os.environ["DINGUS_BASE_PATH"] = args.base_path[0]
    Path(f"{os.environ['DINGUS_BASE_PATH']}/accounts").mkdir(parents=True, exist_ok=True)

    os.environ["DINGUS_NETWORK_ID"] = ""
    os.environ["DINGUS_BLOCK_TIME"] = "10"
    os.environ["DINGUS_MIN_FEE_PER_BYTE"] = "0"
    
    processor = Processor()
