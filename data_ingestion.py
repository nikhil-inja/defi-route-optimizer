import json
import math
from web3 import Web3

BASE_RPC_URL = "https://mainnet.base.org"

w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

if not w3.is_connected():
    raise ConnectionError("Failed to connect to the Base Network")

# Valid Uniswap V3 WETH/USDC pool on Base network (0.05% fee tier)
# Found using Uniswap V3 Factory
POOL_ADDRESS = '0xd0b53D9277642d899DF5C87A3966A349A798F224'

# Uniswap V3 Pool ABI
POOL_ABI = json.loads('''
[
  {"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"_liquidity","type":"uint128"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]
''')

pool_contract = w3.eth.contract(address=POOL_ADDRESS, abi=POOL_ABI)

print(f"\nQuerying Uniswap V3 Pool at address: {POOL_ADDRESS}")

def get_pool_data(contract):

    token0 = contract.functions.token0().call()
    token1 = contract.functions.token1().call()

    liquidity = contract.functions.liquidity().call()

    slot0 = contract.functions.slot0().call()
    sqrt_price_x96 = slot0[0]

    return {
        'token0': token0,
        'token1': token1,
        'liquidity': liquidity,
        'sqrtPriceX96': sqrt_price_x96,
    }

def calculate_price(sqrt_price_x96, decimals0=18, decimals1=6):
    """
    Calculates the human-readable price from the sqrtPriceX96 value.
    WETH (token0) has 18 decimals, USDC (token1) has 6 decimals.
    """
    price_ratio = (sqrt_price_x96 / 2**96) ** 2
    readable_price = price_ratio * (10 ** (decimals0 - decimals1))
    return readable_price


pool_data = get_pool_data(pool_contract)
price_t1_t0 = calculate_price(pool_data['sqrtPriceX96'])

print("\n--- Live Pool Data ---")
print(f"Token 0 Address (WETH): {pool_data['token0']}")
print(f"Token 1 Address (USDC): {pool_data['token1']}")
print(f"Current Liquidity: {pool_data['liquidity']:,}")
print(f"Price of Token 0 in terms of Token 1 (WETH/USDC): ${price_t1_t0:,.2f}")
print(f"Price of Token 1 in terms of Token 0 (USDC/WETH): {1/price_t1_t0:,.6f}")
print("------------------------")
