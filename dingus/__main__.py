from dingus.processor import Processor

import logging
import os
import argparse
from pathlib import Path


def start():

    parser = argparse.ArgumentParser(description="Dingus arguments.")

    parser.add_argument(
        "-N",
        "--network",
        type=str,
        nargs=1,
        default=["testnet"],
        choices=["mainnet", "testnet"],
        help="network connection: (choose from 'mainnet', 'testnet')",
    )

    parser.add_argument(
        "-P",
        "--base-path",
        type=str,
        nargs=1,
        default=[str(Path.home()) + "/.dingus"],
        help="path to store dingus data files",
    )

    parser.add_argument(
        "-L",
        "--log-path",
        type=str,
        nargs=1,
        default=[str(Path.home()) + "/.dingus/dingus.log"],
        help="path to store log file",
    )

    args = parser.parse_args()

    os.environ["NETWORK"] = args.network[0]
    os.environ["BASE_PATH"] = args.base_path[0]
    Path(f"{os.environ['BASE_PATH']}/accounts").mkdir(parents=True, exist_ok=True)
    Path(f"{os.environ['BASE_PATH']}/database").mkdir(parents=True, exist_ok=True)

    os.environ["NETWORK_ID"] = ""
    os.environ["BLOCK_TIME"] = "10"
    os.environ["MIN_FEE_PER_BYTE"] = "0"

    Path(args.log_path[0]).unlink(missing_ok=True)
    logging.basicConfig(filename=args.log_path[0], level=logging.DEBUG)

    processor = Processor()
