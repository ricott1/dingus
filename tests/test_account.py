import dingus.types.account as account
import dingus.utils as utils

def test_create_account():
    params = {
        "address": utils.random_address().to_lsk32(),
        "name": "test",
        "balance": 20,
        "public_key": utils.random_public_key(),
        "nonce": 3,
        "ciphertext":"",
        "salt": "",
        "iv": "",
        "iteration_count": 0,
        "bookmark": True
    }

    acc = account.Account.from_dict(params)
    assert acc.balance == 20
    assert len(acc.ciphertext) == 0

    passphrase = "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
    sk = utils.passphrase_to_private_key(passphrase)
    params = {**params, **sk.encrypt("pwd")} 
    acc = account.Account.from_dict(params)
    assert len(acc.ciphertext) == 96
