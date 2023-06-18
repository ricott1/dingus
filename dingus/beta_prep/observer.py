import json
import time
from dingus import crypto, tree
from scripts import mainchain_rpc_endpoint, sidechain_rpc_endpoint, SIDECHAIN_ID
import dingus.network.api as api

BLOCK_TIME = 5

def track_ccms(target: str):
    if target == "mainchain":
        tracking_topics = [
            "03000000"
        ]
        endpoint = mainchain_rpc_endpoint
        filename = "mainchain/observer.json"
        query_key = "83ed0d25" + "0000" + crypto.hash(bytes.fromhex(SIDECHAIN_ID)).hex()
    else:
        tracking_topics = [
            SIDECHAIN_ID
        ]
        endpoint = sidechain_rpc_endpoint
        filename = "sidechain/observer.json"
        query_key = "83ed0d25" + "0000" + crypto.hash(bytes.fromhex("03000000")).hex()

    track_all_topics = False
    DEBUG = True
    
    print(json.dumps(api.get_node_info(endpoint), indent=4))
    final_height = api.get_node_info(endpoint)["result"]["finalizedHeight"]
    
    with open(filename, "r") as f:
        observer = json.load(f)
    height = observer["lastHeight"]
    events = observer["ccms"]
    inclusion_proofs = observer["inclusionProofs"]
    while True:
        block_events = api.get_events_by_height(height, endpoint)["result"]
        if block_events:
            if DEBUG:
                print(json.dumps(events, indent=4))
            events += [e for e in block_events if e["module"] == "interoperability"]
            observer["ccms"] = events
            with open(filename, "w") as f:
                f.write(json.dumps(observer, indent=4))
        
        height += 1
        if height > final_height:
            print("Finalized height: ", final_height)
            observer["lastHeight"] = final_height
            inclusion_proof = api.get_inclusion_proof([query_key], endpoint)["result"]["proof"]
            observer["inclusionProofs"] += [{
                "height": height,
                "proof": inclusion_proof
            }] 
            with open(filename, "w") as f:
                f.write(json.dumps(observer, indent=4))
            time.sleep(BLOCK_TIME)
            final_height = api.get_node_info(endpoint)["result"]["finalizedHeight"]

if __name__ == "__main__":
    import sys
    track_ccms(sys.argv[1])

