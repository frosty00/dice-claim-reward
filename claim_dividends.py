import requests
from urllib.parse import urlencode

from ethereum import utils, transactions
import rlp

DIVIDENDS_ADDRESS = '0xa4463f9Ff0d87531232c8c4819B536c332DA6EAc'
CONTRACT_ADDRESS = '0x2e071D2966Aa7D8dECB1005885bA1977D6038A65'
PRIVATE_KEY = input('What is your private key?')
PRIVATE_KEY = PRIVATE_KEY[2:] if '0x' == PRIVATE_KEY[:2] else PRIVATE_KEY
ADDRESS = utils.encode_hex(utils.privtoaddr(bytes.fromhex(PRIVATE_KEY)))
ETHERSCAN = 'http://api.etherscan.io/api?'


def create_query(module, action):
    base = ETHERSCAN + 'module={}&action={}&'.format(module, action)

    def inner(**kwargs):
        url = base + urlencode(kwargs)
        response = requests.get(url).json()
        return response['result']
    return inner  # returns str

nonce = create_query('proxy', 'eth_getTransactionCount')
call = create_query('proxy', 'eth_call')
send = create_query('proxy', 'eth_sendRawTransaction')

def hex_to_bool(h):
    return bool(int(h, base=16))

def has_dice():
    dice_balance = call(data='70a08231' + ADDRESS.zfill(64), to=CONTRACT_ADDRESS)
    return hex_to_bool(dice_balance)

def is_paused():
    paused_status = call(data='301cf6e7', to=DIVIDENDS_ADDRESS)
    return hex_to_bool(paused_status)

def main():
    if is_paused():
        raise RuntimeError('payouts are currently paused')

    if not has_dice():
        raise ValueError('the address supplied does not have any dice')

    next_nonce = int(nonce(address=ADDRESS), base=16)
    tx = transactions.Transaction(nonce=next_nonce, gasprice=1*10**9, startgas=50000, # 1 gwei gasprice
                                  to=DIVIDENDS_ADDRESS, value=0, data=bytes.fromhex('cc9ae3f6')).sign(PRIVATE_KEY)

    txhash = send(hex=rlp.encode(tx).hex())
    print('Submitted the transaction successfully: {}'.format(txhash))

if __name__ == '__main__':
    main()
