import json
import random
import time
from dingus import crypto
from dingus.crypto.utils import createAggSig, verifyWeightedAggSig, get_random_BLS_sk
from dingus.types.certificate import ActiveValidatorsUpdate, Certificate, Validator, get_active_validators_update
from dingus.types.transaction import Transaction
from dingus.types.block import Block
from dingus.types.keys import PrivateKey, PublicKey, Address, INVALID_BLS_KEY
from dingus.codec.json_format import MessageToDict, ParseDict  # to decode to hex
import dingus.utils as utils
import dingus.network.api as api


def register_mainchain() -> Transaction:
    bft_params = api.get_last_bft_params(mainchain_rpc_endpoint)["result"]
    mainchain_validators = sorted([
        {
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": v["bftWeight"],
        }
        for v in bft_params["validators"]
    ], key=lambda v: v["blsKey"])
    mainchain_validators = [v for v in mainchain_validators if v["blsKey"] != INVALID_BLS_KEY]
    mainchain_certificate_threshold = bft_params["certificateThreshold"]

    nonce = int(api.get_auth_account(user_key.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint)["result"]["nonce"])
    params = {
        "module": "interoperability",
        "command": "registerMainchain",
        "nonce": nonce,
        "fee": 7350000,
        "senderPublicKey": user_key.to_public_key(),
        "params": {
            "ownChainID": bytes.fromhex(SIDECHAIN_ID),
            "ownName": SIDECHAIN_NAME,
            "mainchainValidators": mainchain_validators,
            "mainchainCertificateThreshold": mainchain_certificate_threshold,
            "signature": b"",
            "aggregationBits": b"",
        },
        "signatures": [],
    }

    from dingus.application.interoperability.schemas import proto

    reg_message = proto["mainchainRegistrationMessage"]()

    reg_message_params = {
        "ownChainID": params["params"]["ownChainID"],
        "ownName": params["params"]["ownName"],
        "mainchainValidators": mainchain_validators,
        "mainchainCertificateThreshold": mainchain_certificate_threshold,
    }
    reg_message = ParseDict(reg_message_params, reg_message)

    from dingus.crypto import signBLS, createAggSig

    validators_data = json.loads(open("./interop_testing/inverno/dev-validators.json", "r").read())
    sidechain_validator_keys = [
        {
            "blsKey": bytes.fromhex(v["plain"]["blsKey"]),
            "blsPrivateKey": bytes.fromhex(v["plain"]["blsPrivateKey"]),
        }
        for v in validators_data["keys"]
    ]

    sidechain_bft_params = api.get_last_bft_params(sidechain_rpc_endpoint)["result"]
    sidechain_validators = sorted([
        { 
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": int(v["bftWeight"]),
            
        } for v in sidechain_bft_params["validators"]], key=lambda validator: validator["blsKey"])
    # sort validatorList lexicographically by blsKey property
    tag = "LSK_CHAIN_REGISTRATION_".encode("ascii")
    chainID = params["params"]["ownChainID"]
    message = reg_message.SerializeToString()
    keys_and_signatures = []
    for v in sidechain_validators:
        bls_key = v["blsKey"]
        validator = next(u for u in sidechain_validator_keys if u["blsKey"].hex() == bls_key.hex())
        bls_priv_key = validator["blsPrivateKey"]
        keys_and_signatures.append((bls_key, signBLS(bls_priv_key, tag, chainID, message)))

    keys_and_signatures = sorted(keys_and_signatures, key=lambda x: x[0])
    agg_bits, signature = createAggSig(
        [k for k, _ in keys_and_signatures],
        keys_and_signatures,
    )
    params["params"]["aggregationBits"] = bytes(agg_bits)
    params["params"]["signature"] = bytes(signature)

    trs = Transaction.from_dict(params)
    trs.sign(user_key, bytes.fromhex(SIDECHAIN_ID))
    return trs

def register_sidechain() -> Transaction:
    sidechain_bft_params = api.get_last_bft_params(sidechain_rpc_endpoint)["result"]
    sidechain_validators = sorted([
        { 
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": v["bftWeight"],
            
        } for v in sidechain_bft_params["validators"]], key=lambda v: v["blsKey"])
    sidechain_certificate_threshold = sidechain_bft_params["certificateThreshold"]

    nonce = int(api.get_auth_account(user_key.to_public_key().to_address().to_lsk32(), mainchain_rpc_endpoint)["result"]["nonce"])
    trs_dict = {
        "module": "interoperability",
        "command": "registerSidechain",
        "nonce": nonce,
        "fee": 1515000000,
        "senderPublicKey": user_key.to_public_key(),
        "params": {
            "chainID": bytes.fromhex(SIDECHAIN_ID),
            "name": SIDECHAIN_NAME,
            "sidechainValidators": sidechain_validators,
            "sidechainCertificateThreshold": sidechain_certificate_threshold,
        },
        "signatures": [],
    }

    trs = Transaction.from_dict(trs_dict)
    trs.sign(user_key, bytes.fromhex("03000000"))
    return trs

def token_transfer(chain: str = "mainchain") -> Transaction:
    if chain == "mainchain":
        priv_key = mainchain_key_val
        endpoint = mainchain_rpc_endpoint
        chainID = "03000000"
    else:
        priv_key = sidechain_key_val
        endpoint = sidechain_rpc_endpoint
        chainID = SIDECHAIN_ID

    pub_key = priv_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 26299416,
        "params": {
            "tokenID": bytes.fromhex(f"{chainID}00000000"),
            "amount": 500000000000,
            "recipientAddress": user_key.to_public_key().to_address(),
            "data": "Un dono per me.",
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    trs.sign(priv_key, bytes.fromhex(chainID))
    return trs


def register_validator(chain: str = "mainchain") -> Transaction:
    if chain == "mainchain":
        endpoint = mainchain_rpc_endpoint
        chainID = "03000000"
    else:
        endpoint = sidechain_rpc_endpoint
        chainID = SIDECHAIN_ID

    pub_key = user_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    sk, pop = get_random_BLS_sk()
    generator_key = PrivateKey.random()
    params = {
        "module": "pos",
        "command": "registerValidator",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 1126299416,
        "params": {
            "name": "gregoriomagno",
            "blsKey": bytes(sk.get_g1()),
            "proofOfPossession": bytes(pop),
            "generatorKey": generator_key.to_public_key().to_bytes()
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    trs.sign(user_key, bytes.fromhex(chainID))
    return trs

def stake(_from: PrivateKey, _to: Address, amount: int = 100000000000, chain: str = "mainchain") -> Transaction:
    if chain == "mainchain":
        endpoint = mainchain_rpc_endpoint
        chainID = "03000000"
    else:
        endpoint = sidechain_rpc_endpoint
        chainID = SIDECHAIN_ID

    # user_key = PrivateKey.from_passphrase(mainchain_passphrase, [44 + 0x80000000, 134 + 0x80000000, 0x80000002])
    pub_key = _from.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    
    params = {
        "module": "pos",
        "command": "stake",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 26299416,
        "params": {
            "stakes": [
                {
                    "validatorAddress": _to, 
                    "amount": amount# * random.randint(1, 32)
                }
            ]
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    trs.sign(_from, bytes.fromhex(chainID))
    return trs

def ccu(chain: str = "mainchain") -> Transaction:
    if chain == "mainchain":
        priv_key = mainchain_key_val
        endpoint = mainchain_rpc_endpoint
        sending_chain_id = bytes.fromhex(SIDECHAIN_ID)
        receiving_chain_id = bytes.fromhex("03000000")
        command = "submitMainchainCrossChainUpdate"
        certificate = api.get_last_valid_certificate(sidechain_rpc_endpoint, mainchain_rpc_endpoint)
        bft_params = api.get_bft_parameters_by_height(certificate.height, sidechain_rpc_endpoint)["result"]
    else:
        priv_key = sidechain_key_val
        endpoint = sidechain_rpc_endpoint
        sending_chain_id = bytes.fromhex("03000000")
        receiving_chain_id = bytes.fromhex(SIDECHAIN_ID)
        command = "submitSidechainCrossChainUpdate"
        certificate = api.get_last_valid_certificate(mainchain_rpc_endpoint, sidechain_rpc_endpoint)
        bft_params = api.get_bft_parameters_by_height(certificate.height, mainchain_rpc_endpoint)["result"]

    pub_key = priv_key.to_public_key()
    certificate_threshold = bft_params["certificateThreshold"]
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    last_certified_validators = api.get_chain_validators(sending_chain_id.hex(), endpoint)["result"]
    current_validators = sorted([
        { 
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": int(v["bftWeight"]),
            
        } for v in last_certified_validators["activeValidators"]], key=lambda validator: validator["blsKey"])
    new_validators = sorted([
        {
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": int(v["bftWeight"]),
        } for v in bft_params["validators"]], key=lambda validator: validator["blsKey"])
    validators_update = get_active_validators_update(current_validators, new_validators)
    print("Validators update: ", validators_update)
    # validators_update["blsKeysUpdate"] = [bytes.fromhex("02") * 48]
    
    trs_dict = {
        "module": "interoperability",
        "command": command,
        "nonce": nonce,
        "fee": 1000000,
        "senderPublicKey": pub_key,
        "params": {
            "sendingChainID": sending_chain_id,
            "certificate": certificate.bytes,
            "activeValidatorsUpdate": validators_update,
            "certificateThreshold": certificate_threshold,
            "inboxUpdate": {
                "crossChainMessages": [],
                "messageWitnessHashes": [],
                "outboxRootWitness": {
                    "bitmap": b"",
                    "siblingHashes": []
                }
            },
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(trs_dict)
    trs.sign(priv_key, receiving_chain_id)
    return trs

def ccu_test_suite() -> None:
    print("\n\n --- CCU SUITE --- \n")
    trs = ccu("mainchain")
    print("Mainchain ccu:", trs)
    # print("Certificate", Certificate.from_bytes(trs.params.certificate))
    print("\nID:", trs.id.hex())
    send_and_wait(trs, mainchain_rpc_endpoint)
    print(json.dumps(api.get_chain_account(trs.params.sendingChainID.hex(), mainchain_rpc_endpoint), indent=4))
    trs = ccu("sidechain")
    print("Sidechain ccu:", trs)
    # print("Certificate", Certificate.from_bytes(trs.params.certificate))
    print("\nID:", trs.id.hex())
    send_and_wait(trs, sidechain_rpc_endpoint)
    print(json.dumps(api.get_chain_account(trs.params.sendingChainID.hex(), sidechain_rpc_endpoint), indent=4))


def registration_test_suite():
    print("\n\n --- REGISTRATION SUITE --- \n")
    sidechain_reg_trs = register_sidechain()
    print("Sidechain registration transaction:", sidechain_reg_trs)
    send_and_wait(sidechain_reg_trs, mainchain_rpc_endpoint)
    print(json.dumps(api.get_chain_account(sidechain_reg_trs.params.chainID.hex(), mainchain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_channel(sidechain_reg_trs.params.chainID.hex(), mainchain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_chain_validators(sidechain_reg_trs.params.chainID.hex(), mainchain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_own_chain_account(mainchain_rpc_endpoint), indent=4))


    mainchain_reg_trs = register_mainchain()
    print("Mainchain registration transaction:", mainchain_reg_trs)

    send_and_wait(mainchain_reg_trs, sidechain_rpc_endpoint)
    print(json.dumps(api.get_chain_account("03000000", sidechain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_channel("03000000", sidechain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_chain_validators("03000000", sidechain_rpc_endpoint), indent=4))
    print(json.dumps(api.get_own_chain_account(sidechain_rpc_endpoint), indent=4))


def send_and_wait(trs: Transaction, endpoint: str, wait: bool = True):
    send_result = trs.send(endpoint)
    if "error" in send_result:
        print("Error while sending transaction:", send_result["error"])
        return

    print("Transaction sent:", send_result["result"]["transactionId"])
    if wait:
        wait_for_confirmation(trs, endpoint)


def wait_for_confirmation(trs: Transaction, endpoint: str):
    print("\nWaiting for transaction to be confirmed...")
    current_height = api.get_node_info(endpoint)["result"]["height"]
    last_height = current_height - 1
    i = 0
    while (h := api.get_node_info(endpoint)["result"]["height"]) < current_height + 101:
        block = api.get_block_by_height(h, endpoint)
        if block["result"]["transactions"] and any([t["id"] == trs.id.hex() for t in block["result"]["transactions"]]):
            print("\nTransaction included at height", h)
            events = api.get_events_by_height(h, endpoint)["result"]
            events = [e for e in events if e["topics"][0] == trs.id.hex() and e["module"] == trs.module]
            print("Events:")
            for e in events:
                print(json.dumps(e, indent=4))

            break

        if h != last_height:
            print("")
            last_height = h

        print(f"\rWaiting for block {h + 1} to be forged" + "." * (i % 4) + " " * (4 - i % 4), end="")
        time.sleep(1)
        i += 1

def stake_for_genesis(chain: str = "mainchain", N: int = 40, onlyInit: bool = True):
    if chain == "mainchain":
        passphrase = mainchain_passphrase
        endpoint = mainchain_rpc_endpoint
    elif chain == "sidechain":
        passphrase = sidechain_passphrase
        endpoint = sidechain_rpc_endpoint
    for n in range(N):
        _from = PrivateKey.from_passphrase(passphrase, [44 + 0x80000000, 134 + 0x80000000, 0x80000000 + n])
        _to = _from.to_public_key().to_address()
        if not onlyInit or _to.to_lsk32() in initValidators:
            send_and_wait(stake(_from, _to, amount= 120*100000000000, chain=chain), endpoint, wait=False)

user_key = PrivateKey(crypto.hash(bytes.fromhex("deadbeefc0feee")))

mainchain_passphrase = "attract squeeze option inflict dynamic end evoke love proof among random blanket table pumpkin general impose access toast undo extend fun employ agree dash"
mainchain_key_val = PrivateKey.from_passphrase(mainchain_passphrase)

mainchain_addr_val = mainchain_key_val.to_public_key().to_address().to_lsk32()
with open("interop_testing/inverno/passphrase.json", "r") as f:
    sidechain_passphrase = json.load(f)["passphrase"]
sidechain_key_val = PrivateKey.from_passphrase(sidechain_passphrase)

sidechain_rpc_endpoint = "localhost:7887"
mainchain_rpc_endpoint = "142.93.5.182:4002"

with open("interop_testing/inverno/genesis_assets.json", "r") as f:
    genesis_assets = json.load(f)["assets"]
    pos_assets = next(a for a in genesis_assets if a["module"] == "pos")
    initValidators = pos_assets["data"]["genesisData"]["initValidators"]
    initValidatorsData = pos_assets["data"]["validators"]

if __name__ == "__main__":
    # os.environ["REQUEST_METHOD"] = "socket"
    SIDECHAIN_ID = "030000ff"
    SIDECHAIN_NAME = "grandeinvernorosso"
    print(json.dumps(api.get_node_info(mainchain_rpc_endpoint), indent=4))

    # send_and_wait(token_transfer("mainchain"), mainchain_rpc_endpoint)
    # send_and_wait(token_transfer("sidechain"), sidechain_rpc_endpoint)
    # send_and_wait(register_validator("mainchain"), mainchain_rpc_endpoint)
    # print(json.dumps(api.get_all_pos_validator(sidechain_rpc_endpoint), indent=4))
    
    # stake_for_genesis(chain="sidechain", N=120)
        
    # registration_test_suite()
    # ccu_test_suite()

    # print(json.dumps(api.get_block_by_height(17815, mainchain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_events_by_height(17815, mainchain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_chain_account(SIDECHAIN_ID, mainchain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_all_pos_validator(sidechain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_last_bft_params(sidechain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_pos_validator("lskvvfdbroskc5akzenxv9n9tq33ttbevk59cjxx4", sidechain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_validator("lskg9x88ccc6b3q8zv8mxvzajozrctap4hprbm5uo", sidechain_rpc_endpoint), indent=4))
    
    # print(json.dumps(api.get_chain_account(SIDECHAIN_ID, mainchain_rpc_endpoint), indent=4))
    # print(api.get_last_certificate(sidechain_rpc_endpoint))
    # stake_for_genesis(chain="sidechain", N=120)


    # all_pos_validators = api.get_all_pos_validator(mainchain_rpc_endpoint)["result"]["validators"]
    

    # current_validators = api.get_last_bft_params(sidechain_rpc_endpoint)["result"]["validators"]
    # current_validators_address = [v["address"] for v in current_validators]
    # print(len(all_pos_validators), len(initValidators), len(current_validators_address))

    # certified_validators = api.get_chain_validators(SIDECHAIN_ID, mainchain_rpc_endpoint)["result"]["activeValidators"]
    # certified_validators_address = []
    # for key in [v["blsKey"] for v in certified_validators]:
    #     if u := next((u for u in initValidatorsData if u["blsKey"] == key), None):
    #         certified_validators_address.append(u["address"])

    # for i, v in enumerate(current_validators_address):
    #     if v not in initValidators:
    #         print(i, v)

    # print(len(certified_validators_address))
