import json
import os
import networkx as nx

from graph.builder import build_transaction_graph
from graph.focus import create_focused_graph
from analysis.investigation import investigate_wallet


def compute_volume_retention(transactions):
    if not transactions:
        return 0.0, 0.0, 0.0, "ETH"
    start_amount = float(transactions[0].get("amount", 0.0))
    end_amount = float(transactions[-1].get("amount", 0.0))
    token = transactions[0].get("token_symbol", transactions[0].get("token", "ETH"))
    retention_pct = (end_amount / start_amount * 100.0) if start_amount > 0 else 0.0
    return start_amount, end_amount, round(retention_pct, 2), token


def generate_wallet_graph_payload(wallet_address: str, max_hops: int = 4) -> dict:
    wallet_address = str(wallet_address).lower().strip()
    data_file = "data/blockchain_data.json"

    if not os.path.exists(data_file):
        return {
            "wallet_address": wallet_address,
            "nodes": [],
            "edges": [],
            "patterns": [],
            "error": "Forensic data file not found"
        }

    with open(data_file, "r", encoding="utf-8") as f:
        blockchain_data = json.load(f)

    # 1. Ingest non-zero value transactions
    transactions = [
        tx for tx in blockchain_data.get("transactions", [])
        if float(tx.get("amount", 0.0) or 0.0) > 0.0
    ]

    graph = build_transaction_graph(transactions)
    raw_metadata = blockchain_data.get("wallets_metadata", {})
    wallets_metadata = {str(k).lower().strip(): v for k, v in raw_metadata.items()}

    for node in graph.nodes:
        norm_node = str(node).lower().strip()
        meta = wallets_metadata.get(norm_node, {})
        graph.nodes[node]["entity_type"] = meta.get("entity_type", "EOA")
        graph.nodes[node]["label"] = meta.get("label", "Unlabeled")

    wallet_depths = {wallet_address: 0}
    if wallet_address in graph:
        lengths = nx.single_source_shortest_path_length(graph, wallet_address, cutoff=max_hops)
        wallet_depths.update(lengths)

    for w_addr, depth in wallet_depths.items():
        if w_addr in graph:
            graph.nodes[w_addr]["hop"] = depth

    focused_graph = create_focused_graph(graph, wallet_depths, wallet_address)
    investigation = investigate_wallet(focused_graph, wallet_address, max_hops=max_hops)

    # ============================================================
    # 2. NODES: Preserves standard types + adds deep entity metadata
    # ============================================================
    nodes = []
    for node, data in focused_graph.nodes(data=True):
        clean_node = str(node).lower().strip()
        raw_entity = data.get("entity_type", "EOA").upper()

        # Backward-compatible mock type
        if clean_node == wallet_address:
            node_type = "target"
        elif "EXCHANGE" in raw_entity or "VASP" in raw_entity:
            node_type = "exchange"
        elif "CONTRACT" in raw_entity or "ROUTER" in raw_entity:
            node_type = "contract"
        else:
            node_type = "peer"

        nodes.append({
            # Mock required fields:
            "id": clean_node,
            "type": node_type,
            "label": data.get("label", "Unlabeled"),
            
            # Forensic additions:
            "hop": int(data.get("hop", 0)),
            "raw_entity_type": raw_entity,
            "is_suspect": clean_node == wallet_address,
            "is_vasp": node_type == "exchange"
        })

    # ============================================================
    # 3. EDGES: Preserves mock fields + adds on-chain provenance
    # ============================================================
    edges = []
    for u, v, data in focused_graph.edges(data=True):
        sender = str(u).lower().strip()
        receiver = str(v).lower().strip()
        hop_val = focused_graph.nodes.get(receiver, {}).get("hop", 1)

        edges.append({
            # Mock required fields:
            "from": sender,
            "to": receiver,
            "amount": float(data.get("amount", 0.0) or 0.0),
            "hop": int(hop_val),

            # Forensic additions:
            "token": data.get("token_symbol", data.get("token", "ETH")),
            "tx_hash": data.get("tx_hash", ""),
            "timestamp": data.get("timestamp", ""),
            "block_number": data.get("block_number", None)
        })

    # ============================================================
    # 4. PATTERNS: Preserves severity badges + adds numerical metrics
    # ============================================================
    patterns = []
    
    # Process Critical Peeling / Money-Flow Paths
    for cp in investigation.get("critical_paths", []):
        cp_txs = cp.get("transactions", [])
        start_amt, end_amt, retention_pct, token = compute_volume_retention(cp_txs)
        indicators = cp.get("indicators", [])
        score = float(cp.get("score", 0.0))
        severity = "HIGH" if score >= 30 else ("MEDIUM" if score >= 15 else "LOW")

        p_type = "PEELING_CHAIN" if any("peel" in str(ind).lower() for ind in indicators) else "MONEY_FLOW"
        desc = (
            f"Path {cp.get('path_id')} ({cp.get('hops')} hops): "
            f"Retained {retention_pct}% ({start_amt} -> {end_amt} {token}). "
            f"Indicators: {', '.join(indicators) if indicators else 'Direct Transfer'}"
        )

        patterns.append({
            # Mock required fields:
            "pattern_type": p_type,
            "description": desc,
            "related_addresses": [str(a).lower().strip() for a in cp.get("path", [])],
            "severity": severity,

            # Forensic additions:
            "path_id": cp.get("path_id"),
            "rank": cp.get("rank"),
            "risk_score": score,
            "volume_retention_pct": retention_pct,
            "indicators": indicators,
            "initial_amount": start_amt,
            "terminal_amount": end_amt,
            "token": token
        })

    # Process Rapid Transit / Mixing Velocity
    for rm in investigation.get("forensics", {}).get("rapid_movements", []):
        patterns.append({
            "pattern_type": "RAPID_MOVEMENT",
            "description": f"Rapid hop within {rm.get('time_delta_minutes', 0)} mins: {rm.get('from')[:10]}... -> {rm.get('to')[:10]}...",
            "related_addresses": [str(rm.get("from")).lower().strip(), str(rm.get("to")).lower().strip()],
            "severity": "HIGH",
            "time_delta_minutes": rm.get("time_delta_minutes", 0),
            "amount": rm.get("amount", 0.0),
            "token": rm.get("token", "ETH")
        })

    # Package top-level payload with high-level metrics
    return {
        "wallet_address": wallet_address,
        "nodes": nodes,
        "edges": edges,
        "patterns": patterns,
        "investigation_summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "critical_paths_detected": len(investigation.get("critical_paths", [])),
            "rapid_transfers_count": len(investigation.get("forensics", {}).get("rapid_movements", []))
        }
    }