from enum import Enum


SERVICE_ENDPOINTS = {
    "mainnet": "https://service.lisk.com/api/v2/",
    "testnet": "https://testnet-service.lisk.com/api/v2/",
    "devnet": "http://localhost:5001/api/v2/",
}

SOCKET_ENDPOINTS = {
    "mainnet": "service.lisk.com",
    "testnet": "testnet-service.lisk.com",
    "devnet": "host.docker.internal:8080",
}

RPC_ENDPOINTS = {
    "mainnet": "206.189.5.168:4002",
    "testnet": "206.189.5.168:4002",
    "devnet": "localhost:7887"
}


class RPC_REQUEST(str, Enum):
    POST_TRANSACTION = "txpool_postTransaction"
    DRY_RUN_TRANSACTION = "txpool_dryRunTransaction"
    GET_ALL_VALIDATORS = "pos_getAllValidators"
    GET_BALANCE = "token_getBalances"