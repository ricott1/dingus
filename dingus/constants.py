import enum

LSK = 10**8

DEFAULT_LISK32_ADDRESS_PREFIX = "lsk"
LISK32_CHARSET = "zxvcpmbn3465o978uyrtkqew2adsjhfg"
EVENT_TAGS = ["user_input", "service_subscription", "api_response"]

class SignatureTags(bytes, enum.Enum):
    TRANSACTION = "LSK_TX_".encode('ascii')

MAX_NUM_VALIDATORS = 199
NUMBER_ACTIVE_VALIDATORS_MAINCHAIN = 101

class Length(int, enum.Enum):
    PUB_KEY = 32
    ADDRESS = 20
    SEED = 32
    LISK32_ADDRESS = 41
    EDSA_SIGNATURE = 64
    EDSA_PUBLIC_KEY = 32
    CHAIN_ID = 4
    TOKEN_ID = 8
    BALANCE_TRANSFER_MAX_DATA = 64
    ID_STRING = 64
    BALANCE_TRANSFER = 150
    CHAIN_NAME_MAX = 20
    CHAIN_NAME_MIN = 1
    COMMAND_NAME_MIN = 1
    COMMAND_NAME_MAX = 32
    MODULE_NAME_MIN = 1
    MODULE_NAME_MAX = 32
    BLS_PUBLIC_KEY = 48
    BLS_SIGNATURE = 96
    DATA_MAX = 64