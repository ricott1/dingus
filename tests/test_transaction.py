from dingus.transaction import Transaction
from dingus.types.keys import PrivateKey
import dingus.utils as utils
from dingus.constants import LSK, SIGNATURE_TAG_TRANSACTION
import os


def test_send_transaction():
    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": bytes.fromhex("6689d38d0d89e072b5339d24b4bff1bd6ef99eb26d8e02697819aecc8851fd55"),
        "nonce": 5,
        "fee": 1216299416,
        "params": {
            "tokenID": bytes.fromhex("0000000000000000"),
            "amount": 123986407700,
            "recipientAddress": bytes.fromhex("2ca4b4e9924547c48c04300b320be84e8cd81e4a"),
            "data": "Odi et amo. Quare id faciam, fortasse requiris.",
            "accountInitializationFee": 0
        },
    }

    trs = Transaction.from_dict(params)

    passphrase = (
        "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
    )
    os.environ[
        "CHAIN_ID"
    ] = "00000000"

    sk1 = PrivateKey(bytes.fromhex("42d93fa53d631181540ad630b9ad913835db79e7d2510be915513836bc175edc"))
    sk2 = PrivateKey(bytes.fromhex("3751d0dee5ee214809118514303fa50a1daaf7151ec8d30c98b12e0caa4bb7de"))

    print("unsigned trs:", trs.bytes.hex())
    assert trs.bytes == trs.unsigned_bytes
    trs.sign(sk1)
    trs.sign(sk2)
    assert len(trs.signatures) == 2
    print("signed trs:",trs)
    print("bytes:",trs.bytes.hex())
    print(trs.id.hex())

    print("privatekey1: ", sk1._signing_key.hex())
    print("privatekey2: ", sk2._signing_key.hex())

#### **First key pair:**

# ```
# private key = 42d93fa53d631181540ad630b9ad913835db79e7d2510be915513836bc175edc
# public key = 6689d38d0d89e072b5339d24b4bff1bd6ef99eb26d8e02697819aecc8851fd55
# ```

# #### **Second key pair:**

# ```
# private key = 3751d0dee5ee214809118514303fa50a1daaf7151ec8d30c98b12e0caa4bb7de
# public key = aa3f553d66b58d6167d14fe9e91b1bd04d7cf5eef27fed0bec8aaac6c73c90b3
# ```



    assert 0
