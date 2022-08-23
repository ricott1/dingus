import dingus.codec
from dingus.codec.block_pb2 import Header
from dingus.transaction import Transaction
import utils


class Block(object):
    def __init__(self, header: Header, transactions: list[Transaction], assets = []) -> None:
        self.schema = dingus.codec.block.Block()
        
        for trs in transactions:
            self.schema.transactions.extend([trs.bytes])

        for asset in assets:
            self.schema.assets.extend([asset.bytes])
        self.unsigned_bytes = self.schema.SerializeToString()

        if "MIN_FEE_PER_BYTE" in os.environ:
            min_fee_per_byte = int(os.environ["MIN_FEE_PER_BYTE"])
        else:
            min_fee_per_byte = 0

        assert self.fee >= self.params.base_fee + min_fee_per_byte * (
            len(self.unsigned_bytes) + EDSA_SIGNATURE_LENGTH
        ), "Invalid 'fee'."

    @classmethod
    def validate_parameters(cls, params: dict) -> None:
        assert "moduleID" in params, "Missing 'moduleID' parameter."
        assert (
            f"{params['moduleID']}:{params['commandID']}" in module_params_to_schema
        ), "Invalid 'moduleID:commandID' combination."
        assert "commandID" in params, "Missing 'commandID' parameter."
        assert "senderPublicKey" in params, "Missing 'senderPublicKey' parameter."
        assert (
            len(params["senderPublicKey"]) == EDSA_PUBLIC_KEY_LENGTH
        ), "Invalid 'senderPublicKey' length."
        assert "nonce" in params, "Missing 'nonce' parameter."
        assert params["nonce"] >= 0, "Invalid 'nonce'."
        assert "fee" in params, "Missing 'fee' parameter."
        assert params["fee"] >= 0, "Invalid 'fee'."
        assert "asset" in params, "Missing 'asset' parameter."

    @classmethod
    def from_dict(cls, params: dict) -> Transaction:
        cls.validate_parameters(params)
        return Transaction(params)

    @property
    def moduleID(self) -> int:
        return self.schema.moduleID

    @property
    def commandID(self) -> int:
        return self.schema.commandID

    @property
    def senderPublicKey(self) -> bytes:
        return self.schema.senderPublicKey

    @property
    def nonce(self) -> int:
        return self.schema.nonce

    @property
    def fee(self) -> int:
        return self.schema.fee

    @property
    def signatures(self) -> list[bytes]:
        return self.schema.signatures

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()

    @property
    def to_dict(self) -> dict:
        base_tx = MessageToDict(self.schema)
        base_tx["asset"] = MessageToDict(self.schema)
        return base_tx

    @property
    def id(self) -> bytes:
        return utils.hash(self.bytes)

    @property
    def is_signed(self) -> bool:
        return len(self.schema.signatures) > 0

    def sign(self, sk: SigningKey) -> None:
        if len(self.signatures) != 0:
            logging.warn("Transaction already signed.")
            return

        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot sign transaction, network ID not set.")
            return

        net_id = bytes.fromhex(os.environ["CHAIN_ID"])
        signature = utils.sign(net_id + self.unsigned_bytes, sk)
        self.schema.signatures.extend([signature])

    def send(self) -> dict:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex())

    def __str__(self) -> str:
        return json.dumps(self.to_dict)
