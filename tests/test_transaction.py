from dingus.transaction import Transaction
import dingus.utils as utils
from dingus.constants import ADDRESS_LENGTH, LSK

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
print(params)
print(len(params["asset"]["recipientAddress"]), ADDRESS_LENGTH)
trs = Transaction.fromDict(params)
# trs.nonce=166

passphrase = "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
trs.sign(utils.passphrase_to_private_key(passphrase))
