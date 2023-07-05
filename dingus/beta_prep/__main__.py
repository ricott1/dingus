import json
from scripts import *
import dingus.network.api as api
import cloak




def test_swap():
    # 54558739753796538000979871037007719415313302986541501570938489388164508227846#
    secret = 0x1787f38d854231dfec2b27a0f621414d10bfa95970b3e576aed29e1e8287e51e#int.from_bytes(os.urandom(32))
    Q  = cloak.commitment_from_secret(secret)
    
    # open_trs = cloak.openSwap(Q.x.to_bytes(32), Q.y.to_bytes(32))
    # send_and_wait(open_trs, sidechain_rpc_endpoint)

    # swapID = cloak.get_hashed_commitment(Q.x, Q.y)

    # close_trs = cloak.closeSwap(swapID, secret.to_bytes(32))
    # send_and_wait(close_trs, sidechain_rpc_endpoint)
    print("Q:", Q)
    print("SwapID:", cloak.get_hashed_commitment(Q.x, Q.y).hex())
    print("Secret:", secret.to_bytes(32).hex())

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


    