import { useState, useEffect, useRef } from "react";
import "./App.css";
import { getWalletGraph } from "./services/api";

// -------------------------------------------------------------
// HELPER FUNCTIONS (From visualizer.py)
// -------------------------------------------------------------
function shortAddress(addr) {
  if (!addr) return "";
  const s = String(addr);
  return s.length > 12 ? `${s.slice(0, 6)}...${s.slice(-4)}` : s;
}

function isVASP(nodeData = {}) {
  const entityType = String(nodeData.entity_type || "").toUpperCase();
  const label = String(nodeData.label || "").toUpperCase();
  return (
    entityType.includes("EXCHANGE") ||
    entityType.includes("VASP") ||
    entityType.includes("DEPOSIT") ||
    label.includes("BINANCE") ||
    label.includes("COINBASE")
  );
}

// -------------------------------------------------------------
// SPRING-LAYOUT & CRITICAL PATH ENGINE (Port of visualizer.py)
// -------------------------------------------------------------
function computeForensicLayout(rawTransactions, suspectWallet, walletMetadata = []) {
  const sWallet = (suspectWallet || "").toLowerCase().trim();
  const nodeMap = new Map();
  const edgeList = [];
  const outgoingTokens = {};
  const incomingTokens = {};

  const metadataMap = new Map(
    (Array.isArray(walletMetadata) ? walletMetadata : []).map((item) => [
      String(item.address || item.wallet || item.id || "").toLowerCase(),
      item,
    ])
  );

  const addNode = (address, extra = {}) => {
    const id = String(address || "").trim();
    if (!id) return;

    const key = id.toLowerCase();
    const metadata = metadataMap.get(key) || {};

    if (!nodeMap.has(key)) {
      nodeMap.set(key, {
        id,
        hop:
          metadata.hop ??
          extra.hop ??
          (key === sWallet ? 0 : 1),
        entity_type:
          metadata.entity_type ||
          metadata.type ||
          extra.entity_type ||
          "EOA",
        label:
          metadata.label ||
          metadata.name ||
          extra.label ||
          "",
      });
    } else {
      const node = nodeMap.get(key);
      node.hop = metadata.hop ?? extra.hop ?? node.hop;
      node.entity_type =
        metadata.entity_type || metadata.type || extra.entity_type || node.entity_type;
      node.label = metadata.label || metadata.name || extra.label || node.label;
    }
  };

  (Array.isArray(walletMetadata) ? walletMetadata : []).forEach((item) => {
    addNode(item.address || item.wallet || item.id, item);
  });

  (Array.isArray(rawTransactions) ? rawTransactions : []).forEach((tx) => {
    const from = String(tx.from_address || tx.from || tx.sender || "").trim();
    const to = String(tx.to_address || tx.to || tx.receiver || "").trim();
    const rawAmount = tx.amount ?? tx.value ?? tx.value_eth ?? 0;
    const amt = Number.parseFloat(rawAmount);
    const token = tx.token_symbol || tx.token || tx.asset || tx.amount_unit || "ETH";

    if (!from || !to || !Number.isFinite(amt) || amt <= 0) return;
    if (from.toLowerCase() === to.toLowerCase()) return;

    addNode(from, {
      entity_type: tx.from_type || tx.sender_type,
      label: tx.from_label || tx.sender_label,
    });
    addNode(to, {
      entity_type: tx.to_type || tx.receiver_type,
      label: tx.to_label || tx.receiver_label,
    });

    if (from.toLowerCase() === sWallet) {
      outgoingTokens[token] = (outgoingTokens[token] || 0) + amt;
    }
    if (to.toLowerCase() === sWallet) {
      incomingTokens[token] = (incomingTokens[token] || 0) + amt;
    }

    edgeList.push({
      source: from,
      target: to,
      amount: amt,
      token,
      label: `${amt.toFixed(2)} ${token}`,
      tx_hash: tx.tx_hash || tx.hash || tx.transaction_hash || "",
      timestamp: tx.timestamp || tx.time || tx.block_timestamp || "",
      status: tx.status || "",
    });
  });

  // Deterministic fallback positions. The backend remains the source of truth
  // for paths; this function only prepares data for the existing SVG renderer.
  const width = 960;
  const height = 540;
  const nodes = Array.from(nodeMap.values()).map((node, i) => {
    const isSuspect = node.id.toLowerCase() === sWallet;
    const vaspFlag = isVASP(node);
    let color = "plum";
    let size = 20;

    if (isSuspect) {
      color = "red";
      size = 24;
    } else if (vaspFlag) {
      color = "gold";
      size = 22;
    } else if (node.hop === 1) {
      color = "skyblue";
      size = 21;
    }

    let x = width * 0.5;
    let y = height * 0.5;

    if (isSuspect) {
      x = width * 0.52;
      y = height * 0.52;
    } else if (node.hop === 1) {
      x = width * 0.30 + (i % 5) * 115;
      y = height * 0.82;
    } else {
      const column = (node.hop || 2) % 3;
      const row = Math.floor(i / 3) % 3;
      x = width * (0.18 + column * 0.32);
      y = height * (0.22 + row * 0.25);
    }

    return {
      ...node,
      color,
      r: size,
      x,
      y,
      shortLabel: shortAddress(node.id),
    };
  });

  function formatTokenMap(map) {
    const keys = Object.keys(map);
    if (keys.length === 0) return "0.00 ETH";
    return keys.map((k) => `${map[k].toFixed(2)} ${k}`).join(", ");
  }

  return {
    nodes,
    edges: edgeList,
    summary: {
      analyzed: nodes.length,
      txs: edgeList.length,
      outgoing: formatTokenMap(outgoingTokens),
      incoming: formatTokenMap(incomingTokens),
    },
  };
}

function normalizeCriticalPaths(data) {
  const candidates =
    data?.critical_paths ||
    data?.criticalPaths ||
    data?.investigation?.critical_paths ||
    data?.result?.critical_paths ||
    [];

  if (!Array.isArray(candidates)) return [];

  return candidates
    .map((item, index) => {
      if (Array.isArray(item)) {
        return {
          path_id: `PATH-${index + 1}`,
          path: item,
          hops: Math.max(item.length - 1, 0),
          score: null,
          classification: "CRITICAL_PATH",
          reasons: [],
          transactions: [],
        };
      }

      const path = item.path || item.wallet_path || item.nodes || [];
      return {
        ...item,
        path_id: item.path_id || item.pathId || `PATH-${index + 1}`,
        path: Array.isArray(path) ? path : [],
        hops: item.hops ?? Math.max((Array.isArray(path) ? path.length : 1) - 1, 0),
        score: item.score ?? item.risk_score ?? null,
        classification: item.classification || "CRITICAL_PATH",
        reasons: Array.isArray(item.reasons) ? item.reasons : [],
        transactions: Array.isArray(item.transactions) ? item.transactions : [],
      };
    })
    .filter((item) => item.path.length >= 2);
}

// -------------------------------------------------------------
// MAIN COMPONENT
// -------------------------------------------------------------
function App() {
  const [page, setPage] = useState("investigation");
  const [wallet, setWallet] = useState("");
  const [searchedWallet, setSearchedWallet] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [transactionSearch, setTransactionSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [reportGenerated, setReportGenerated] = useState(false);
  const [loading, setLoading] = useState(false);

  // Graph state
  const [graphView, setGraphView] = useState("main"); // main graph first; critical path is selected from backend results
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [criticalPaths, setCriticalPaths] = useState([]);
  const [selectedCriticalPathId, setSelectedCriticalPathId] = useState(null);
  const [graphSummary, setGraphSummary] = useState({
    analyzed: 0,
    txs: 0,
    outgoing: "0.00 ETH",
    incoming: "0.00 ETH",
  });

  // Inspection text box state (like visualizer.py current_info_text)
  const [infoBoxText, setInfoBoxText] = useState("Click a wallet to inspect it");

  // Metrics state
  const [riskScore, setRiskScore] = useState(null);
  const [riskLevel, setRiskLevel] = useState("NOT ANALYZED");
  const [reasons, setReasons] = useState([]);
  const [vaspMatch, setVaspMatch] = useState({ name: "Unattributed", confidence: 0 });
  const [txList, setTxList] = useState([]);

  // Drag state for interactive SVG nodes
  const draggingNodeRef = useRef(null);

  async function analyzeWallet() {
    const target = wallet.trim();
    if (!target) return;

    setSearchedWallet(target);
    setLoading(true);
    setReportGenerated(false);
    setSelectedNode(null);
    setSelectedCriticalPathId(null);
    setInfoBoxText("Click a wallet to inspect it");

    try {
      const response = await getWalletGraph(target);
      const investigation = response?.result || response?.investigation || response;

      const rawTransactions =
        investigation?.transactions ||
        investigation?.transaction_list ||
        response?.transactions ||
        response?.edges ||
        [];

      const walletMetadata =
        investigation?.wallets ||
        investigation?.nodes ||
        response?.wallets ||
        response?.nodes ||
        [];

      const computed = computeForensicLayout(
        rawTransactions,
        target,
        walletMetadata
      );

      // Some graph APIs return already-normalized nodes/edges instead of a
      // transactions array. Preserve those if there is no transaction data.
      if (
        computed.edges.length === 0 &&
        Array.isArray(response?.edges) &&
        response.edges.length > 0
      ) {
        const edgeTransactions = response.edges.map((edge) => ({
          from: edge.source || edge.from || edge.from_address,
          to: edge.target || edge.to || edge.to_address,
          amount: edge.amount ?? edge.value ?? 0,
          token_symbol: edge.token || edge.token_symbol || "ETH",
          tx_hash: edge.tx_hash || edge.hash,
          timestamp: edge.timestamp,
        }));
        const fallback = computeForensicLayout(
          edgeTransactions,
          target,
          walletMetadata
        );
        setGraphNodes(fallback.nodes);
        setGraphEdges(fallback.edges);
        setGraphSummary(fallback.summary);
      } else {
        setGraphNodes(computed.nodes);
        setGraphEdges(computed.edges);
        setGraphSummary(computed.summary);
      }

      const paths = normalizeCriticalPaths(response);
      setCriticalPaths(paths);
      setGraphView(paths.length > 0 ? "critical" : "main");
      if (paths.length > 0) {
        setSelectedCriticalPathId(paths[0].path_id);
      }

      // Consume backend-provided analysis when available. Never invent values.
      const risk =
        investigation?.risk_score ??
        investigation?.riskScore ??
        response?.risk_score ??
        response?.riskScore ??
        null;
      const level =
        investigation?.risk_level ||
        investigation?.riskLevel ||
        response?.risk_level ||
        response?.riskLevel ||
        "NOT ANALYZED";
      const backendReasons =
        investigation?.reasons ||
        investigation?.risk_reasons ||
        response?.reasons ||
        response?.risk_reasons ||
        [];
      const vasp =
        investigation?.vasp ||
        investigation?.vasp_match ||
        investigation?.vasp_attribution ||
        response?.vasp ||
        response?.vasp_match ||
        response?.vasp_attribution ||
        null;

      setRiskScore(risk);
      setRiskLevel(level);
      setReasons(Array.isArray(backendReasons) ? backendReasons : []);
      setVaspMatch({
        name:
          vasp?.name ||
          vasp?.label ||
          vasp?.entity ||
          investigation?.vasp_name ||
          "Unattributed",
        confidence:
          Number(
            vasp?.confidence ??
            vasp?.confidence_score ??
            investigation?.vasp_confidence ??
            0
          ) || 0,
      });

      const transactionsForTable = rawTransactions.map((tx, index) => ({
        hash: String(
          tx.tx_hash || tx.hash || tx.transaction_hash || `TX-${index + 1}`
        ),
        from: shortAddress(tx.from_address || tx.from || tx.sender || ""),
        to: shortAddress(tx.to_address || tx.to || tx.receiver || ""),
        amount: `${tx.amount ?? tx.value ?? "0"} ${tx.token_symbol || tx.token || tx.asset || "ETH"}`,
        time: tx.timestamp || tx.time || tx.block_timestamp || "—",
        status: tx.status || "Detected",
      }));
      setTxList(transactionsForTable);
    } catch (error) {
      console.error("Wallet graph investigation failed:", error);
      setGraphNodes([]);
      setGraphEdges([]);
      setCriticalPaths([]);
      setSelectedCriticalPathId(null);
      setGraphSummary({
        analyzed: 0,
        txs: 0,
        outgoing: "0.00 ETH",
        incoming: "0.00 ETH",
      });
      setRiskScore(null);
      setRiskLevel("NOT ANALYZED");
      setReasons([]);
      setVaspMatch({ name: "Unattributed", confidence: 0 });
      setTxList([]);
      setInfoBoxText(error?.message || "Unable to retrieve wallet graph");
    } finally {
      setLoading(false);
    }
  }

  function selectCriticalPath(pathId) {
    setSelectedCriticalPathId(pathId);
    setGraphView("critical");
    setSelectedNode(null);
    setInfoBoxText("Click a wallet to inspect it");
  }

  // Main graph contains every transaction returned by the API.
  // Critical view contains only the backend-selected critical path.
  const selectedCriticalPath =
    criticalPaths.find((path) => path.path_id === selectedCriticalPathId) ||
    criticalPaths[0] ||
    null;

  const pathWallets = selectedCriticalPath?.path || [];
  const pathPairs = new Set();
  for (let i = 0; i < pathWallets.length - 1; i += 1) {
    pathPairs.add(
      `${String(pathWallets[i]).toLowerCase()}->${String(pathWallets[i + 1]).toLowerCase()}`
    );
  }

  let activeEdges = graphEdges;
  if (graphView === "critical" && selectedCriticalPath) {
    activeEdges = graphEdges.filter((edge) =>
      pathPairs.has(
        `${edge.source.toLowerCase()}->${edge.target.toLowerCase()}`
      )
    );

    // If the backend supplied transactions inside the selected path, use them
    // when the main graph does not contain matching edge objects.
    if (activeEdges.length === 0 && selectedCriticalPath.transactions.length > 0) {
      activeEdges = selectedCriticalPath.transactions.map((tx) => ({
        source: tx.from_address || tx.from || tx.sender,
        target: tx.to_address || tx.to || tx.receiver,
        amount: Number.parseFloat(tx.amount ?? tx.value ?? 0) || 0,
        token: tx.token_symbol || tx.token || tx.asset || "ETH",
        label: `${Number.parseFloat(tx.amount ?? tx.value ?? 0) || 0} ${tx.token_symbol || tx.token || tx.asset || "ETH"}`,
      }));
    }
  }

  const activeNodes =
    graphView === "critical" && selectedCriticalPath
      ? graphNodes.filter((n) =>
          pathWallets.some(
            (walletAddress) =>
              String(walletAddress).toLowerCase() === n.id.toLowerCase()
          )
        )
      : graphNodes;

  // Dragging logic for nodes
  function handleMouseDown(e, nodeId) {
    draggingNodeRef.current = nodeId;
  }

  function handleMouseMove(e) {
    if (!draggingNodeRef.current) return;
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 960;
    const y = ((e.clientY - rect.top) / rect.height) * 540;

    setGraphNodes((prev) =>
      prev.map((n) => (n.id === draggingNodeRef.current ? { ...n, x, y } : n))
    );
  }

  function handleMouseUp() {
    draggingNodeRef.current = null;
  }

  function handleNodeClick(node) {
  setSelectedNode(node.id);

  const inDeg = activeEdges.filter(
    (e) => e.target.toLowerCase() === node.id.toLowerCase()
  ).length;

  const outDeg = activeEdges.filter(
    (e) => e.source.toLowerCase() === node.id.toLowerCase()
  ).length;

  const isSuspect =
    node.id.toLowerCase() ===
    (searchedWallet || wallet).toLowerCase();

  const role = isSuspect
    ? "Suspect Wallet"
    : node.entity_type || "EOA";

  setInfoBoxText(
    `Type: ${role}\n` +
    `Address: ${node.id}\n` +
    `Label: ${node.label || "Unknown"}\n` +
    `Hop: ${node.hop}\n` +
    `In: ${inDeg} | Out: ${outDeg}`
    );
  }

  const filteredTransactions = txList.filter((tx) => {
    const search = transactionSearch.toLowerCase();
    const matchesSearch =
      tx.hash.toLowerCase().includes(search) ||
      tx.from.toLowerCase().includes(search) ||
      tx.to.toLowerCase().includes(search);
    const matchesFilter = filter === "All" || tx.status === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="logo">
          <div className="logoIcon">₿</div>
          <div>
            <h1>CryptoTrace</h1>
            <span>BLOCKCHAIN FORENSICS</span>
          </div>
        </div>
        <nav>
          <button className={page === "dashboard" ? "navItem active" : "navItem"} onClick={() => setPage("dashboard")}>
            <span>▦</span> Dashboard
          </button>
          <button className={page === "investigation" ? "navItem active" : "navItem"} onClick={() => setPage("investigation")}>
            <span>⌕</span> Investigation
          </button>
          <button className={page === "cases" ? "navItem active" : "navItem"} onClick={() => setPage("cases")}>
            <span>◈</span> Cases
          </button>
          <button className={page === "vasps" ? "navItem active" : "navItem"} onClick={() => setPage("vasps")}>
            <span>◉</span> VASPs
          </button>
          <button className={page === "reports" ? "navItem active" : "navItem"} onClick={() => setPage("reports")}>
            <span>▤</span> Reports
          </button>
        </nav>
        <div className="sidebarBottom">
          <strong>SIH 26183</strong>
          <span>Crypto Fraud & VASP Identification</span>
        </div>
      </aside>

      {/* MAIN CONTAINER */}
      <main className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">CRYPTO FORENSICS / SIH 26183</span>
            <h2>
              {page === "dashboard" && "Investigation Dashboard"}
              {page === "investigation" && "Wallet Investigation"}
              {page === "cases" && "Investigation Cases"}
              {page === "vasps" && "VASP Intelligence"}
              {page === "reports" && "Investigation Reports"}
            </h2>
          </div>
          <div className="systemStatus">
            <span className="statusDot"></span> SYSTEM ONLINE
          </div>
        </header>

        {/* DASHBOARD PAGE */}
        {page === "dashboard" && (
          <div className="content">
            <section className="hero">
              <div>
                <span className="sectionLabel">REAL-TIME BLOCKCHAIN INTELLIGENCE</span>
                <h1>Trace. Analyze. <span>Identify.</span></h1>
                <p>Automatically trace suspicious cryptocurrency transactions and identify fraud-linked Virtual Asset Service Providers.</p>
                <button className="primaryButton" onClick={() => setPage("investigation")}>Start Investigation →</button>
              </div>
              <div className="heroGraphic">
                <div className="orbit"></div>
                <div className="heroCoin">₿</div>
              </div>
            </section>
            <section className="statsGrid">
              <div className="statCard"><span>ACTIVE CASES</span><strong>12</strong><small>+3 this week</small></div>
              <div className="statCard"><span>WALLETS ANALYZED</span><strong>1,284</strong><small>+84 today</small></div>
              <div className="statCard"><span>HIGH RISK</span><strong className="redText">37</strong><small>Requires attention</small></div>
              <div className="statCard"><span>VASPs IDENTIFIED</span><strong>19</strong><small>Across 6 networks</small></div>
            </section>
          </div>
        )}

        {/* INVESTIGATION PAGE */}
        {page === "investigation" && (
          <div className="content">
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Wallet Investigation</h2>
                  <p>Enter a suspect wallet address to trace its cryptocurrency flow.</p>
                </div>
                <span className="liveBadge">● API DATA</span>
              </div>
              <div className="searchBox">
                <input
                  value={wallet}
                  onChange={(e) => setWallet(e.target.value)}
                  placeholder="Enter suspect wallet address (e.g. 0x742d35Cc66...)"
                />
                <button className="primaryButton" onClick={analyzeWallet} disabled={loading}>
                  {loading ? "Analyzing..." : "Analyze Wallet"}
                </button>
              </div>
              {searchedWallet && (
                <div className="searchedWallet">
                  Analyzing: <strong>{searchedWallet}</strong>
                </div>
              )}
            </section>

            <section className="statsGrid">
              <div className="statCard">
                <span>TRANSACTIONS</span>
                <strong>{txList.length}</strong>
                <small>Detected transactions</small>
              </div>
              <div className="statCard">
                <span>RISK SCORE</span>
                <strong className={riskScore === null ? "" : riskScore >= 75 ? "redText" : "greenText"}>
                  {riskScore !== null ? `${riskScore}/100` : "--"}
                </strong>
                <small>Probability of fraud</small>
              </div>
              <div className="statCard">
                <span>RISK LEVEL</span>
                <strong className={riskLevel === "HIGH" ? "redText" : riskLevel === "LOW" ? "greenText" : ""}>
                  {riskLevel}
                </strong>
                <small>Immediate attention</small>
              </div>
              <div className="statCard">
                <span>VASP MATCH</span>
                <strong>{vaspMatch.confidence}%</strong>
                <small>{vaspMatch.name}</small>
              </div>
            </section>

            {/* FORENSIC MONEY FLOW INVESTIGATION GRAPH (PORT OF VISUALIZER.PY) */}
            <section className="panel" style={{ padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div>
                  <h2 style={{ fontSize: "20px", fontWeight: "bold", margin: 0 }}>Blockchain Money Flow Investigation</h2>
                  <p style={{ margin: "4px 0 0 0", color: "#8b949e", fontSize: "13px" }}>
                    {graphView === "critical"
                      ? selectedCriticalPath
                        ? `Selected critical path • ${selectedCriticalPath.hops} hops${selectedCriticalPath.score !== null ? ` • score ${selectedCriticalPath.score}` : ""}`
                        : "No critical path returned by the backend"
                      : "Full multi-hop transaction network returned by the API"}
                  </p>
                </div>

                {/* GRAPH VIEW SWITCHER */}
                <div style={{ display: "flex", gap: "8px", background: "#161b22", padding: "4px", borderRadius: "8px" }}>
                  <button
                    onClick={() => criticalPaths.length > 0 && setGraphView("critical")}
                    disabled={criticalPaths.length === 0}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      cursor: criticalPaths.length > 0 ? "pointer" : "not-allowed",
                      fontWeight: 700,
                      fontSize: "13px",
                      background: graphView === "critical" ? "#ef4444" : "transparent",
                      color: "white",
                      opacity: criticalPaths.length > 0 ? 1 : 0.45,
                    }}
                  >
                    ⚡ Critical Path{criticalPaths.length > 0 ? ` (${criticalPaths.length})` : ""}
                  </button>
                  <button
                    onClick={() => setGraphView("main")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      cursor: "pointer",
                      fontWeight: 700,
                      fontSize: "13px",
                      background: graphView === "main" ? "#38bdf8" : "transparent",
                      color: "white",
                    }}
                  >
                    🌐 Main Graph
                  </button>
                </div>
              </div>

              {/* ALL CRITICAL PATHS RETURNED BY GRAPH FORENSICS */}
              <div
                style={{
                  marginBottom: "12px",
                  background: "#f6f8fa",
                  border: "1px solid #d0d7de",
                  borderRadius: "10px",
                  padding: "10px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <strong style={{ color: "#111827", fontSize: "14px" }}>
                    Critical Paths ({criticalPaths.length})
                  </strong>
                  <span style={{ color: "#6b7280", fontSize: "12px" }}>
                    Select a path to focus the graph
                  </span>
                </div>

                {criticalPaths.length === 0 ? (
                  <div style={{ color: "#6b7280", fontSize: "12px", padding: "6px 2px" }}>
                    No critical paths were returned by the current API response.
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: "8px", overflowX: "auto", paddingBottom: "2px" }}>
                    {criticalPaths.map((path, index) => {
                      const selected = path.path_id === selectedCriticalPathId;
                      return (
                        <button
                          key={path.path_id}
                          onClick={() => selectCriticalPath(path.path_id)}
                          style={{
                            minWidth: "250px",
                            maxWidth: "330px",
                            textAlign: "left",
                            padding: "9px 10px",
                            borderRadius: "8px",
                            border: selected ? "2px solid #ef4444" : "1px solid #c9d1d9",
                            background: selected ? "#fff1f2" : "white",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                            <strong style={{ color: "#111827", fontSize: "12px" }}>
                              ⚡ #{index + 1} {path.path_id}
                            </strong>
                            <span style={{ color: "#b91c1c", fontSize: "11px", fontWeight: 800 }}>
                              {path.score !== null ? `Score ${path.score}` : path.classification}
                            </span>
                          </div>
                          <div style={{ marginTop: "5px", color: "#374151", fontSize: "11px", lineHeight: 1.5, wordBreak: "break-all" }}>
                            {path.path.join(" → ")}
                          </div>
                          <div style={{ marginTop: "5px", color: "#6b7280", fontSize: "11px" }}>
                            {path.hops} hops{path.reasons.length > 0 ? ` • ${path.reasons[0]}` : ""}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* MATPLOTLIB-STYLE CANVAS CONTAINER */}
              <div
                style={{
                  position: "relative",
                  width: "100%",
                  height: "560px",
                  background: "#ffffff",
                  borderRadius: "10px",
                  border: "1px solid #d0d7de",
                  overflow: "hidden",
                }}
              >
                {/* TITLE OVERLAY */}
                <div
                  style={{
                    position: "absolute",
                    top: 14,
                    width: "100%",
                    textAlign: "center",
                    fontSize: "22px",
                    fontWeight: 900,
                    color: "#000000",
                    pointerEvents: "none",
                  }}
                >
                  Blockchain Money Flow Investigation
                </div>

                {/* TOP-LEFT MOVABLE INFO BOX */}
                <div
                  style={{
                    position: "absolute",
                    top: 20,
                    left: 20,
                    zIndex: 10,
                    background: "white",
                    padding: "8px 14px",
                    borderRadius: "8px",
                    border: "1.5px solid #000000",
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "#000000",
                    whiteSpace: "pre-line",
                    wordBreak: "break-all",
                    maxWidth: "420px",
                    boxShadow: "0 2px 5px rgba(0,0,0,0.08)",
                  }}
                >
                  {infoBoxText}
                </div>

                {/* TOP-RIGHT LEGEND */}
                <div
                  style={{
                    position: "absolute",
                    top: 20,
                    right: 20,
                    zIndex: 10,
                    background: "white",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    border: "1px solid #d0d7de",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.06)",
                    fontSize: "12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ width: 14, height: 14, borderRadius: "50%", background: "red", border: "1.5px solid black" }}></span>
                    <span style={{ color: "#000000", fontWeight: 600 }}>Suspect Wallet</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ width: 14, height: 14, borderRadius: "50%", background: "skyblue", border: "1.5px solid black" }}></span>
                    <span style={{ color: "#000000", fontWeight: 600 }}>Hop 1 Wallet</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ width: 14, height: 14, borderRadius: "50%", background: "plum", border: "1.5px solid black" }}></span>
                    <span style={{ color: "#000000", fontWeight: 600 }}>Hop 2+ Wallet</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ width: 14, height: 14, borderRadius: "50%", background: "gold", border: "1.5px solid black" }}></span>
                    <span style={{ color: "#000000", fontWeight: 600 }}>VASP / Exchange Deposit</span>
                  </div>
                </div>

                {/* BOTTOM-LEFT SUMMARY BOX */}
                <div
                  style={{
                    position: "absolute",
                    bottom: 20,
                    left: 20,
                    zIndex: 10,
                    background: "white",
                    padding: "10px 16px",
                    borderRadius: "8px",
                    border: "1.5px solid #000000",
                    fontSize: "12px",
                    color: "#000000",
                    lineHeight: 1.6,
                    boxShadow: "0 2px 5px rgba(0,0,0,0.08)",
                  }}
                >
                  <div><strong>Wallets analyzed:</strong> {graphSummary.analyzed}</div>
                  <div><strong>Transactions shown:</strong> {activeEdges.length}</div>
                  <div><strong>Outgoing from suspect:</strong> {graphSummary.outgoing}</div>
                  <div><strong>Incoming to suspect:</strong> {graphSummary.incoming}</div>
                </div>

                {/* SVG CANVAS FOR EDGES AND CIRCULAR NODES */}
                <svg
                  viewBox="0 0 960 540"
                  style={{ width: "100%", height: "100%", cursor: draggingNodeRef.current ? "grabbing" : "default" }}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                >
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" orient="auto">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000" />
                    </marker>
                  </defs>

                  {/* DIRECTED ARROWS & AMOUNT LABELS */}
                  {activeEdges.map((edge, idx) => {
                    const src = graphNodes.find((n) => n.id.toLowerCase() === edge.source.toLowerCase());
                    const tgt = graphNodes.find((n) => n.id.toLowerCase() === edge.target.toLowerCase());
                    if (!src || !tgt) return null;

                    const dx = tgt.x - src.x;
                    const dy = tgt.y - src.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;

                    // Trim arrows to node boundary
                    const srcX = src.x + (dx / dist) * src.r;
                    const srcY = src.y + (dy / dist) * src.r;
                    const tgtX = tgt.x - (dx / dist) * (tgt.r + 5);
                    const tgtY = tgt.y - (dy / dist) * (tgt.r + 5);

                    // Curvature matching visualizer.py arc3,rad=0.08
                    const normalX = -dy / dist;
                    const normalY = dx / dist;
                    const curveOffset = dist * 0.08;
                    const midX = (srcX + tgtX) / 2 + normalX * curveOffset;
                    const midY = (srcY + tgtY) / 2 + normalY * curveOffset;

                    const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
                    const labelAngle = angle > 90 || angle < -90 ? angle + 180 : angle;

                    return (
                      <g key={idx}>
                        <path
                          d={`M ${srcX} ${srcY} Q ${midX} ${midY} ${tgtX} ${tgtY}`}
                          stroke="#000000"
                          strokeWidth="1.6"
                          fill="none"
                          markerEnd="url(#arrow)"
                        />
                        <rect
                          x={midX - 35}
                          y={midY - 10}
                          width="70"
                          height="16"
                          fill="white"
                          opacity="0.85"
                          rx="3"
                          transform={`rotate(${labelAngle}, ${midX}, ${midY})`}
                        />
                        <text
                          x={midX}
                          y={midY + 2}
                          transform={`rotate(${labelAngle}, ${midX}, ${midY})`}
                          fill="#000000"
                          fontSize="10"
                          fontWeight="700"
                          textAnchor="middle"
                        >
                          {edge.label}
                        </text>
                      </g>
                    );
                  })}

                  {/* CIRCULAR NODES WITH BLACK EDGES */}
                  {activeNodes.map((node) => (
                    <g
                      key={node.id}
                      style={{ cursor: "pointer" }}
                      onMouseDown={(e) => handleMouseDown(e, node.id)}
                      onClick={() => handleNodeClick(node)}
                    >
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={node.r}
                        fill={node.color}
                        stroke="#000000"
                        strokeWidth="1.8"
                      />
                      <text
                        x={node.x}
                        y={node.y + 24}
                        fill="#000000"
                        fontSize="11"
                        fontWeight="800"
                        textAnchor="middle"
                      >
                        {node.shortLabel}
                      </text>
                    </g>
                  ))}
                </svg>
              </div>
            </section>

            {/* FRAUD INDICATORS & VASP ATTRIBUTION */}
            <div className="twoColumn">
              <section className="panel">
                <div className="panelHeader">
                  <div>
                    <h2>Fraud Indicators</h2>
                    <p>Signals contributing to the risk score</p>
                  </div>
                </div>
                {reasons.length > 0 ? (
                  reasons.map((reason, idx) => (
                    <div key={idx} className="indicator">
                      <span>{reason}</span>
                      <strong className="redText">DETECTED</strong>
                    </div>
                  ))
                ) : (
                  <div className="indicator">
                    <span style={{ color: "#8b949e" }}>No wallet investigation conducted yet.</span>
                    <strong style={{ color: "#8b949e" }}>IDLE</strong>
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panelHeader">
                  <div>
                    <h2>VASP Attribution</h2>
                    <p>Potential service connected to the flow</p>
                  </div>
                </div>
                <div className="vaspCard">
                  <div className="vaspIcon">◉</div>
                  <div>
                    <span>IDENTIFIED VASP</span>
                    <h3>{vaspMatch.name}</h3>
                    <p>Destination wallet attribution result.</p>
                  </div>
                </div>
                <div className="confidence">
                  <div>
                    <span>ATTRIBUTION CONFIDENCE</span>
                    <strong>{vaspMatch.confidence}%</strong>
                  </div>
                  <div className="progress">
                    <div className="progressFill" style={{ width: `${vaspMatch.confidence}%` }}></div>
                  </div>
                </div>
              </section>
            </div>

            {/* TIMELINE */}
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Investigation Timeline</h2>
                  <p>Sequence of detected money-flow events returned by the API</p>
                </div>
              </div>
              <div className="timeline">
                {txList.length === 0 ? (
                  <div className="timelineItem">
                    <span className="timelineDot"></span>
                    <div>
                      <strong>No transaction timeline available</strong>
                      <p>Run an investigation to load blockchain events.</p>
                    </div>
                  </div>
                ) : (
                  txList.slice(0, 8).map((tx, index) => (
                    <div className="timelineItem" key={`${tx.hash}-${index}`}>
                      <span className="timelineDot"></span>
                      <div>
                        <strong>{index === 0 ? "Initial transaction detected" : `Money-flow event ${index + 1}`}</strong>
                        <p>{tx.from} → {tx.to} • {tx.amount}</p>
                        <small>{tx.time}</small>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>

            {/* TRANSACTION TABLE */}
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Recent Transactions</h2>
                  <p>Transactions detected in the traced path</p>
                </div>
                <div className="tableControls">
                  <input
                    value={transactionSearch}
                    onChange={(e) => setTransactionSearch(e.target.value)}
                    placeholder="Search hash or address..."
                  />
                  <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                    <option value="All">All</option>
                    <option value="Suspicious">Suspicious</option>
                    <option value="Normal">Normal</option>
                  </select>
                </div>
              </div>

              <div className="tableWrapper">
                <table>
                  <thead>
                    <tr>
                      <th>TRANSACTION</th>
                      <th>FROM</th>
                      <th>TO</th>
                      <th>AMOUNT</th>
                      <th>TIME</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTransactions.map((tx) => (
                      <tr key={tx.hash}>
                        <td className="hash">{tx.hash}</td>
                        <td>{tx.from}</td>
                        <td>{tx.to}</td>
                        <td>{tx.amount}</td>
                        <td>{tx.time}</td>
                        <td>
                          <span className={tx.status === "Suspicious" ? "status suspicious" : "status normal"}>
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* INVESTIGATION SUMMARY */}
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Investigation Summary</h2>
                  <p>Automated analysis conclusion</p>
                </div>
              </div>
              <div className="summaryBox">
                <div className="summaryScore">
                  <strong>{riskScore !== null ? riskScore : "--"}</strong>
                  <span>RISK SCORE</span>
                </div>
                <div className="summaryText">
                  <h3>{riskLevel === "NOT ANALYZED" ? "No Investigation Conducted Yet" : `${riskLevel} Risk Flow Detected (${riskScore}/100)`}</h3>
                  <p>
                    {riskLevel === "NOT ANALYZED"
                      ? "Enter a suspect wallet address above to trace transaction flows, compute risk score, and identify VASP attribution."
                      : `The API returned a ${riskLevel} risk assessment with a score of ${riskScore}/100. VASP attribution: ${vaspMatch.name} (${vaspMatch.confidence}% confidence).`}
                  </p>
                </div>
              </div>
              <div className="actionButtons">
                <button className="primaryButton" onClick={() => setReportGenerated(true)} disabled={!searchedWallet}>
                  Generate Investigation Report
                </button>
              </div>
              {reportGenerated && (
                <div className="successMessage">
                  ✓ Investigation report generated successfully. Ready for export.
                </div>
              )}
            </section>
          </div>
        )}

        {/* CASES PAGE */}
        {page === "cases" && (
          <div className="content">
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Investigation Cases</h2>
                  <p>Active blockchain fraud investigations</p>
                </div>
              </div>
              <div className="caseGrid">
                <div className="caseCard"><span>CASE-26183</span><h3>Crypto Investment Fraud</h3><p>Ethereum • High Risk</p><strong>OPEN</strong></div>
                <div className="caseCard"><span>CASE-26171</span><h3>Phishing Wallet</h3><p>Ethereum • Medium Risk</p><strong>UNDER REVIEW</strong></div>
                <div className="caseCard"><span>CASE-26154</span><h3>Suspicious VASP Flow</h3><p>Ethereum • High Risk</p><strong>OPEN</strong></div>
              </div>
            </section>
          </div>
        )}

        {/* VASPS PAGE */}
        {page === "vasps" && (
          <div className="content">
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>VASP Intelligence</h2>
                  <p>Potential cryptocurrency service providers</p>
                </div>
              </div>
              <div className="vaspList">
                <div className="vaspListItem"><div><strong>Binance Deposit Hot Wallet</strong><span>Ethereum destination cluster</span></div><b>94%</b></div>
                <div className="vaspListItem"><div><strong>Coinbase Prime Custody</strong><span>Historical transaction match</span></div><b>76%</b></div>
                <div className="vaspListItem"><div><strong>OKX Intermediary Pool</strong><span>Behavioural similarity</span></div><b>64%</b></div>
              </div>
            </section>
          </div>
        )}

        {/* REPORTS PAGE */}
        {page === "reports" && (
          <div className="content">
            <section className="panel">
              <div className="panelHeader">
                <div>
                  <h2>Investigation Reports</h2>
                  <p>Generated investigation evidence</p>
                </div>
              </div>
              <div className="reportCard">
                <div><span>REPORT-26183</span><h3>Crypto Fraud Wallet Investigation</h3><p>Risk Score: 88 • VASP Confidence: 94%</p></div>
                <button className="secondaryButton">Export</button>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;