import networkx as nx
import math
import json
from web3 import Web3

BASE_RPC_URL = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
if not w3.is_connected():
    raise ConnectionError("Failed to connect to the Base Network")

POOL_ADDRESS = '0xd0b53D9277642d899DF5C87A3966A349A798F224'
POOL_ABI = json.loads('''[
  {"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]
''')

def get_pool_price_and_tokens(pool_address):
    """Fetches token addresses and the current price from a Uniswap V3 pool."""
    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)

    token0 = pool_contract.functions.token0().call()
    token1 = pool_contract.functions.token1().call()

    slot0 = pool_contract.functions.slot0().call()
    sqrt_price_x96 = slot0[0]

    price_ratio = (sqrt_price_x96 / 2**96) ** 2
    price_t1_for_t0 = price_ratio * (10 ** (6 - 18))

    return {
        "token0": token0,
        "token1": token1,
        "price_t1_for_t0": price_t1_for_t0
    }


G = nx.DiGraph()
print("Graph initialized")
print(f"Fetching data for pool: {POOL_ADDRESS}")

pool_data = get_pool_price_and_tokens(POOL_ADDRESS)
token0 = pool_data["token0"]
token1 = pool_data["token1"]
price_t1_for_t0 = pool_data["price_t1_for_t0"]
price_t0_for_t1 = 1 / price_t1_for_t0

G.add_node(token0, symbol="WETH")
G.add_node(token1, symbol="USDC")
print(f"Added nodes for WETH({token0}) and USDC({token1})")

weight0_to_1 = -math.log(price_t0_for_t1)
weight1_to_0 = -math.log(price_t1_for_t0)
print("Edges added for both trading directions.")

print("\n--- Graph Information ---")
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")

print("\nNodes")
for node, data in G.nodes(data=True):
    print(f"- {data['symbol']}: {node}")

print("\nEdges (with weights):")
for u, v, data in G.edges(data=True):
    u_symbol = G.nodes[u]['symbol']
    v_symbol = G.nodes[v]['symbol']
    print(f"- From {u_symbol} to {v_symbol}: Weight = {data['weight']:.6f} (Price: {data['price']:.6f})")
print("------------------------")


TOKEN_A_ADDRESS = '0xAAAAAAAA'
G.add_node(TOKEN_A_ADDRESS, symbol="TA")

G.add_edge(token0, TOKEN_A_ADDRESS, weight=weight0_to_1, price=-math.log(1000))
G.add_edge(TOKEN_A_ADDRESS, token0, weight=weight0_to_1, price=-math.log(1/1000))

G.add_edge(token1, TOKEN_A_ADDRESS, weight=weight1_to_0, price=-math.log(1))
G.add_edge(TOKEN_A_ADDRESS, token1, weight=weight1_to_0, price=-math.log(1/1))

print("\n--- Graph after adding hypothetical 'Token A' ---")
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")
print("-------------------------------------------------")