from enum import Enum


ENDPOINTS = {
    "mainnet": "https://service.lisk.com",
    "testnet": "https://testnet-service.lisk.com",
    "devnet": "http://localhost:5001",
}

SOCKET_ENDPOINTS = {
    "mainnet": "wss://service.lisk.com",
    "testnet": "wss://testnet-service.lisk.com",
    "devnet": "ws://host.docker.internal:8080",
}

RPC_ENDPOINTS = {
    "mainnet": "https://rpc.lisk.com",
    "testnet": "https://testnet-rpc.lisk.com",
    "devnet": "http://localhost:7887",
}


class RPC_REQUEST(str, Enum):
    POST_TRANSACTION = "txpool_postTransaction"
    DRY_RUN_TRANSACTION = "txpool_dryRunTransaction"
    GET_ALL_VALIDATORS = "pos_getAllValidators"
    GET_BALANCE = "token_getBalances"