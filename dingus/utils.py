from hashlib import sha256 
from nacl.signing import SigningKey, VerifyKey
import os

import dingus.types.keys as keys
from dingus.constants import ADDRESS_LENGTH, PUB_KEY_LENGTH


def passphrase_to_sk(passphrase: str) -> keys.PrivateKey:
    seed = sha256(passphrase.encode()).digest()
    return keys.PrivateKey(seed)

def public_key_to_address(pk: bytes) -> bytes:
    return sha256(pk).digest()[:20].hex()

def hash(msg: bytes) -> bytes:
    return sha256(msg).digest()

def sign(msg: bytes, sk: SigningKey) -> bytes:
    return sk.sign(msg).signature

def random_address() -> keys.Address:
    return keys.Address(os.urandom(ADDRESS_LENGTH))

def random_public_key() -> keys.PublicKey:
    return keys.PublicKey(os.urandom(PUB_KEY_LENGTH))

def mock_block() -> dict:
    return{
        'id': '856ab6c964aae1b9ff42a3866defd871a8adf4169bd883d01abd205ee0e59ec2', 
        'height': 17281669, 
        'version': 2, 
        'timestamp': 1639824850, 
        'generatorAddress': 'lskbfur9zgv52sov3g44zgaepc9rkscgwtz69y3t2', 
        'generatorPublicKey': 'd76962002b6f39155251f759ec91e93c8dddba7d9df1a909937f265af606143b', 
        'generatorUsername': 'benevale', 
        'transactionRoot': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 
        'signature': 'f12ef06edc5c3237427b83b68a93cee7083c57a0c8c82a2b3ef0cb00129b3ce2a1e0cb4c5348efbd96d01804ac2cb29fe4cad68a51677ac7f531b008fddb6903', 
        'previousBlockId': '1be9ed7bea70de312490e87f0ac780632836f6e024dbff3ddeb0efb777ff9cca', 
        'numberOfTransactions': 0, 
        'totalForged': '100000000', 
        'totalBurnt': '0', 
        'totalFee': '0', 
        'reward': '100000000', 
        'isFinal': False, 
        'maxHeightPreviouslyForged': 17281623, 
        'maxHeightPrevoted': 17281586, 
        'seedReveal': '015d705212c99e897ce00d5a77eacef5'
        }
    

 