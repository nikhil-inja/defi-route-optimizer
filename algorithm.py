import networkx as nx
import math
import json
from web3 import Web3

def create_market_graph():
    """Builds a graph with real and hypothetical token pools."""
    G = nx.DiGraph()
    
    # --- Real Pool: WETH/USDC ---
    # We are hardcoding token addresses and symbols for this example.
    # In a real app, you would fetch symbols or have a mapping.
    WETH_ADDR = "0x4200000000000000000000000000000000000006"
    USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bda02913"
    
    G.add_node(WETH_ADDR, symbol="WETH")
    G.add_node(USDC_ADDR, symbol="USDC")
    
    # Hypothetical price for WETH/USDC: 1 WETH = 3000 USDC
    price_weth_for_usdc = 3000
    price_usdc_for_weth = 1 / price_weth_for_usdc
    
    G.add_edge(WETH_ADDR, USDC_ADDR, weight=-math.log(price_weth_for_usdc), price=price_weth_for_usdc)
    G.add_edge(USDC_ADDR, WETH_ADDR, weight=-math.log(price_usdc_for_weth), price=price_usdc_for_weth)

    # --- Hypothetical Pools for Multi-Hop Path ---
    TOKEN_A_ADDR = "0xAAAAAAAA"
    G.add_node(TOKEN_A_ADDR, symbol="TA")

    # WETH <-> TA Pool (hypothetical price: 1 WETH = 1000 TA)
    price_weth_for_ta = 1000
    G.add_edge(WETH_ADDR, TOKEN_A_ADDR, weight=-math.log(price_weth_for_ta), price=price_weth_for_ta)
    G.add_edge(TOKEN_A_ADDR, WETH_ADDR, weight=-math.log(1/price_weth_for_ta), price=1/price_weth_for_ta)

    # USDC <-> TA Pool (hypothetical price: 1 USDC = 0.5 TA)
    # This creates an inefficient path to show the algorithm choosing the better one.
    price_usdc_for_ta = 0.5
    G.add_edge(USDC_ADDR, TOKEN_A_ADDR, weight=-math.log(price_usdc_for_ta), price=price_usdc_for_ta)
    G.add_edge(TOKEN_A_ADDR, USDC_ADDR, weight=-math.log(1/price_usdc_for_ta), price=1/price_usdc_for_ta)
    
    print("Market graph created with 3 nodes and 6 edges.")
    return G

def find_negative_cycle_nodes(G, weight='weight'):
    # Initialize
    dist = {n: 0.0 for n in G}  # super-source trick
    pred = {n: None for n in G}
    nodes = list(G)

    # Relax |V|-1 times
    for _ in range(len(nodes) - 1):
        updated = False
        for u, v, data in G.edges(data=True):
            w = data.get(weight, 0.0)
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u
                updated = True
        if not updated:
            return None

    # One more pass to find an edge that can still relax -> cycle exists
    x = None
    for u, v, data in G.edges(data=True):
        w = data.get(weight, 0.0)
        if dist[u] + w < dist[v]:
            pred[v] = u
            x = v
            break
    if x is None:
        return None

    # Walk back |V| steps to ensure we are inside the cycle
    for _ in range(len(nodes)):
        x = pred[x]

    # Collect the cycle
    cycle = [x]
    cur = pred[x]
    while cur != x and cur is not None:
        cycle.append(cur)
        cur = pred[cur]
    cycle.reverse()
    return cycle

market_graph = create_market_graph()

# Define our start and end points for the trade
start_token_addr = "0x4200000000000000000000000000000000000006" # WETH
end_token_addr = "0x833589fCD6eDb6E08f4c7C32D4f71b54bda02913"   # USDC

start_symbol = market_graph.nodes[start_token_addr]['symbol']
end_symbol = market_graph.nodes[end_token_addr]['symbol']

print(f"\nFinding the best path from {start_symbol} to {end_symbol}")

try:
    optimal_path = nx.bellman_ford_path(
        market_graph, 
        source=start_token_addr, 
        target=end_token_addr,
        weight='weight'
    )
    print("\n--- Optimal Trading Route Found ---")
    overall_rate = 1.0

    for i in range(len(optimal_path) - 1):
        u = optimal_path[i]
        v = optimal_path[i+1]
        
        # Get the edge data
        edge_data = market_graph.get_edge_data(u, v)
        price = edge_data['price']
        
        u_symbol = market_graph.nodes[u]['symbol']
        v_symbol = market_graph.nodes[v]['symbol']
        
        print(f"Step {i+1}: Swap {u_symbol} -> {v_symbol} at a rate of {price:.6f}")
        
        # Multiply rates to get the final outcome
        overall_rate *= price

    print("\n--- Summary ---")
    print(f"Path: {' -> '.join([market_graph.nodes[node]['symbol'] for node in optimal_path])}")
    print(f"Final Exchange Rate: 1 {start_symbol} = {overall_rate:.6f} {end_symbol}")
    print("-----------------")

except nx.NetworkXNoPath:
    print(f"\nNo trading path found between {start_symbol} and {end_symbol}.")

except nx.NetworkXUnbounded:
    print("--- Arbitrage Opportunity Detected! ---")
    # 1) If you only need existence:
    # print("Negative cycle exists; not printing cycle nodes.")
    # return

    # 2) If you want the actual cycle nodes, compute them:
    cycle = find_negative_cycle_nodes(market_graph, weight='weight')
    if cycle:
        cycle_symbols = [market_graph.nodes[n].get('symbol', n) for n in cycle + [cycle[0]]]
        print("Arbitrage Path:")
        print(" -> ".join(cycle_symbols))
    else:
        print("Negative cycle detected, but failed to recover cycle nodes.")