from dingus.transaction import Transaction
import dingus.utils as utils
from dingus.constants import LSK
import os

def test_send_transaction():
    params = {
        "moduleID": 2,
        "assetID": 0,
        "senderPublicKey": utils.random_public_key().encode(),
        "nonce": 0,
        "fee": int(0.5 * LSK),
        "asset": {
            "amount": int(3 * LSK),
            "recipientAddress": utils.random_address(),
            "data": ""
        }   
    }

    trs = Transaction.fromDict(params)

    passphrase = "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
    os.environ["NETWORK_ID"] = "15f0dacc1060e91818224a94286b13aa04279c640bd5d6f193182031d133df7c"
    trs.sign(utils.passphrase_to_private_key(passphrase))
    assert len(trs.signatures) == 1
