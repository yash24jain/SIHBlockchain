import json
import os
import networkx as nx

from blockc.explorer import explore_wallet
from graph.builder import build_transaction_graph
from graph.visualize import visualize_graph
from graph.focus import create_focused_graph
from analysis.investigation import investigate_wallet
from graph.path_focus import create_path_graph


def compute_volume_retention(transactions):
    if not transactions:
        return 0.0, 0.0, 0.0, "ETH"
    start_amount = float(transactions[0].get("amount", 0.0))
    end_amount = float(transactions[-1].get("amount", 0.0))
    token = transactions[0].get("token_symbol", transactions[0].get("token", "ETH"))
    retention_pct = (end_amount / start_amount * 100.0) if start_amount > 0 else 0.0
    return start_amount, end_amount, round(retention_pct, 2), token


# ============================================================
# 1. LIVE FETCH OR LOAD CACHED DATA
# ============================================================
DATA_FILE = "data/blockchain_data.json"
max_investigation_hops = 3

print("========================================")
print("BLOCKCHAIN FORENSIC PIPELINE")
print("========================================")

user_choice = input("Fetch fresh data from blockchain? (y/n) [default: n]: ").strip().lower()

if user_choice == "y":
    target_wallet = input("Enter suspect wallet address: ").strip().lower()
    print(f"\nCrawling on-chain money flow for {target_wallet} up to {max_investigation_hops} hops...")
    blockchain_data = explore_wallet(
        wallet=target_wallet,
        max_hops=max_investigation_hops,
        max_wallets=50,
        branches_per_wallet=2
    )
else:
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Please run with 'y' to fetch data first.")
        exit(1)
    print(f"Loading local forensic data from {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        blockchain_data = json.load(f)

wallet = blockchain_data["wallet"].lower().strip()
raw_metadata = blockchain_data.get("wallets_metadata", {})
wallets_metadata = {str(k).lower().strip(): v for k, v in raw_metadata.items()}

print(f"\nTarget Suspect: {wallet}")
print("Starting blockchain investigation...\n")

# Filter out zero-value transactions
transactions = [
    tx for tx in blockchain_data.get("transactions", [])
    if float(tx.get("amount", 0.0) or 0.0) > 0.0
]

# ============================================================
# 2. GRAPH CONSTRUCTION & METADATA ENRICHMENT
# ============================================================
graph = build_transaction_graph(transactions)

for node in graph.nodes:
    norm_node = str(node).lower().strip()
    meta = wallets_metadata.get(norm_node, {})
    graph.nodes[node]["entity_type"] = meta.get("entity_type", "EOA")
    graph.nodes[node]["label"] = meta.get("label", "Unlabeled")

wallet_depths = {wallet: 0}

if wallet in graph:
    lengths = nx.single_source_shortest_path_length(
        graph, 
        wallet, 
        cutoff=max_investigation_hops
    )
    wallet_depths.update(lengths)

for wallet_address, depth in wallet_depths.items():
    if wallet_address in graph:
        graph.nodes[wallet_address]["hop"] = depth

focused_graph = create_focused_graph(
    graph,
    wallet_depths,
    wallet
)

for node in focused_graph.nodes:
    norm_node = str(node).lower().strip()
    meta = wallets_metadata.get(norm_node, {})
    focused_graph.nodes[node]["entity_type"] = meta.get("entity_type", "EOA")
    focused_graph.nodes[node]["label"] = meta.get("label", "Unlabeled")

# ============================================================
# 3. FORENSIC ANALYSIS & CRITICAL PATH SELECTION
# ============================================================
investigation = investigate_wallet(
    focused_graph,
    wallet,
    max_hops=max_investigation_hops
)

print("\n========== CRITICAL PATHS ==========")

for path_data in investigation["critical_paths"]:
    path_txs = path_data.get("transactions", [])
    start_amt, end_amt, retention_pct, token = compute_volume_retention(path_txs)
    path_data["retention_pct"] = retention_pct

    start_addr = str(path_data["summary"]["start_wallet"]).lower().strip()
    end_addr = str(path_data["summary"]["end_wallet"]).lower().strip()
    
    start_type = focused_graph.nodes.get(start_addr, {}).get("entity_type", "EOA")
    end_type = focused_graph.nodes.get(end_addr, {}).get("entity_type", "EOA")
    end_label = focused_graph.nodes.get(end_addr, {}).get("label", "Unlabeled")

    print(f"\nRank {path_data['rank']} | {path_data['path_id']} | Score: {path_data['score']}")
    print(f"  Hops: {path_data['hops']} | Volume Retention: {retention_pct}% ({start_amt} -> {end_amt} {token})")
    print(f"  Start: [{start_type}] {start_addr}")
    print(f"  End:   [{end_type}] {end_addr} ({end_label})")
    print(f"  Indicators: {', '.join(path_data['indicators'])}")

selected_path_id = input("\nEnter PATH-ID to investigate (or press Enter for Rank 1): ").strip()

if not selected_path_id and investigation["critical_paths"]:
    selected_path_id = investigation["critical_paths"][0]["path_id"]

selected_path = None
for path_data in investigation["critical_paths"]:
    if path_data["path_id"] == selected_path_id:
        selected_path = path_data
        break

if selected_path is None:
    print("\nInvalid PATH-ID.")
    exit(1)

selected_txs = selected_path.get("transactions", [])
start_amt, end_amt, retention_pct, token = compute_volume_retention(selected_txs)

print("\n========== SELECTED PATH ==========")
print(f"Path ID: {selected_path['path_id']}")
print(f"Rank: {selected_path['rank']}")
print(f"Score: {selected_path['score']}")
print(f"Hops: {selected_path['hops']}")
print(f"Volume Retention: {retention_pct}% ({start_amt} {token} -> {end_amt} {token})")
print(f"Indicators: {', '.join(selected_path['indicators'])}")

print("\nMoney Flow Breakdown:")
for i, addr in enumerate(selected_path["path"]):
    norm_addr = str(addr).lower().strip()
    node_data = focused_graph.nodes.get(norm_addr, {})
    entity_type = node_data.get("entity_type", "EOA")
    label = node_data.get("label", "Unlabeled")
    print(f"  Hop {i}: [{entity_type:<17}] {norm_addr} ({label})")

selected_path_graph = create_path_graph(focused_graph, selected_path)

print("\n========== PATH TRANSACTIONS ==========")
for index, transaction in enumerate(selected_txs, start=1):
    sender = str(transaction.get("from", "")).lower().strip()
    receiver = str(transaction.get("to", "")).lower().strip()
    tx_token = transaction.get("token_symbol", transaction.get("token", "ETH"))
    s_type = focused_graph.nodes.get(sender, {}).get("entity_type", "EOA")
    r_type = focused_graph.nodes.get(receiver, {}).get("entity_type", "EOA")

    print(f"\nTransaction {index}")
    print(f"  From:      [{s_type}] {sender}")
    print(f"  To:        [{r_type}] {receiver}")
    print(f"  Amount:    {transaction.get('amount')} {tx_token}")
    print(f"  Timestamp: {transaction.get('timestamp')}")
    print(f"  TX Hash:   {transaction.get('tx_hash')}")

print("\n========== INVESTIGATION SUMMARY ==========")
print(f"Wallets:          {len(investigation['wallets'])}")
print(f"Transactions:     {len(investigation['transactions'])}")
print(f"Paths:            {len(investigation['paths'])}")
print(f"Critical Paths:   {len(investigation['critical_paths'])}")
print(f"Rapid movements:  {len(investigation['forensics']['rapid_movements'])}")

with open("data/investigation.json", "w", encoding="utf-8") as file:
    json.dump(investigation, file, indent=4)

print("\nInvestigation JSON saved to data/investigation.json")

# ============================================================
# 4. VISUALIZATION
# ============================================================
print("\nOpening Selected Path View (close window to open Full Graph)...")
visualize_graph(selected_path_graph, wallet)

print("Opening Full Money Flow Graph...")
visualize_graph(graph, wallet)