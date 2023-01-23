from dingus.types.ccm import CCM
import dingus.codec as codec
import dingus.utils as utils

def test_send_transaction():
    params = {
        "module": "interoperability",
        "crossChainCommand": "registration",
        "nonce": 0,
        "fee": 0,
        "sendingChainID": bytes.fromhex("00000123"),
        "receivingChainID": bytes.fromhex("00000000"),
        "params": {
            "name": "lisk_mainchain",
            "chainID": bytes.fromhex("00000000"),
            "messageFeeTokenID": bytes.fromhex("0000000000000000")
        },
        "status": 0
    }
    

    ccm = CCM.from_dict(params)

    
    print("ccm:", ccm)
    print("ccm bytes:", ccm.bytes.hex())
    print("ccm id:", ccm.id.hex())

    # validators = [
    # ]
    # certificateThreshold = 30000000

    # schema = codec.validators.Validators()
    # for v in validators:
    #     val_schema = codec.validators.Validator()
    #     val_schema.blsKey = bytes.fromhex(v["blsKey"])
    #     val_schema.bftWeight = v["bftWeight"]
    #     schema.validators.extend([val_schema])

    # schema.certificateThreshold = certificateThreshold

    # # print("validators:", schema)
    # # print("validators bytes:", schema.SerializeToString().hex())
    # print("validators hash", crypto.hash(schema.SerializeToString()).hex())


if __name__ == "__main__":
    test_send_transaction()