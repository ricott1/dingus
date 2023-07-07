import json
from scripts import *
import dingus.network.api as api
import atmen




def test_swap():
    # secret = bytes.fromhex("ac9647afcb88196f1b7c20db07013832799a3028c1ed39af16e32aad7dfcb6cd")
    secret = os.urandom(32)
    swapID  = atmen.commitment_from_secret(secret)
    print("SwapID:", swapID.hex())
    print("Secret:", secret.hex())
    
    open_trs = atmen.openSwap(swapID)
    print("sender balance", json.dumps(api.get_balance(PublicKey(open_trs.senderPublicKey).to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))
    print("recipient balance", json.dumps(api.get_balance(user_key2.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))
    send_and_wait(open_trs, sidechain_rpc_endpoint)
    print("sender balance", json.dumps(api.get_balance(PublicKey(open_trs.senderPublicKey).to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))
    print("recipient balance", json.dumps(api.get_balance(user_key2.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))
    close_trs = atmen.closeSwap(swapID, secret)
    send_and_wait(close_trs, sidechain_rpc_endpoint)
    print("sender balance", json.dumps(api.get_balance(sidechain_key_val.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))
    print("recipient balance", json.dumps(api.get_balance(user_key2.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint)["result"], indent=4))

if __name__ == "__main__":
    # print(api.get_balance(user_key.to_public_key().to_address().to_lsk32(), sidechain_rpc_endpoint))  
    test_swap()
    # send_and_wait(trs, sidechain_rpc_endpoint)

    # print(json.dumps(api.get_events_by_height(336, sidechain_rpc_endpoint), indent=4))



    # print(api.get_last_certificate(sidechain_rpc_endpoint))
    # print(json.dumps(api.get_node_info(sidechain_rpc_endpoint), indent=4))


    # print(json.dumps(api.get_last_bft_params(mainchain_rpc_endpoint), indent=4))

    # preparation stuff
    # stake_for_genesis("sidechain")
    # stake_for_genesis("mainchain")
    # send_and_wait(token_transfer("mainchain"), mainchain_rpc_endpoint)
    # send_and_wait(token_transfer("sidechain"), sidechain_rpc_endpoint)

    # registration_test_suite()
    # sidechain_reg_trs = register_sidechain()
    # print("Sidechain registration transaction:", sidechain_reg_trs)
    # send_and_wait(sidechain_reg_trs, mainchain_rpc_endpoint)
    
    
    # ccu_test_suite()
    # print(json.dumps(api.get_chain_account(SIDECHAIN_ID, mainchain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_chain_account("02000000", sidechain_rpc_endpoint), indent=4))
    # trs = ccu("mainchain", True)
    # print(trs)
    # print(trs.bytes.hex())
    # send_and_wait(trs, mainchain_rpc_endpoint)
    # print(json.dumps(api.get_channel("03000000", sidechain_rpc_endpoint), indent=4))
    # print(json.dumps(api.get_generator_keys(mainchain_rpc_endpoint), indent=4))
    # print(api.get_balance("lsknopnjqsh9rpbmsycsv39zg84rhwq3tw3rpf4rn", sidechain_rpc_endpoint))  


    