import { useState, useEffect } from "react";
import "./App.css";
import * as api from "./services/api";

function App() {
  const [page, setPage] = useState("dashboard");
  const [wallet, setWallet] = useState("");
  const [searchedWallet, setSearchedWallet] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [transactionSearch, setTransactionSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [reportGenerated, setReportGenerated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  
  // Real API state (initialized with clean 'No investigation yet' initial state)
  const [riskScore, setRiskScore] = useState(null);
  const [riskLevel, setRiskLevel] = useState("NOT ANALYZED");
  const [reasons, setReasons] = useState([]);
  const [vaspMatch, setVaspMatch] = useState({ name: "Unattributed", confidence: 0 });
  const [txList, setTxList] = useState([]);
  const [nodeList, setNodeList] = useState([]);

  const filteredTransactions = txList.filter((tx) => {
    const search = transactionSearch.toLowerCase();

    const matchesSearch =
      tx.hash.toLowerCase().includes(search) ||
      tx.from.toLowerCase().includes(search) ||
      tx.to.toLowerCase().includes(search);

    const matchesFilter =
      filter === "All" || tx.status === filter;

    return matchesSearch && matchesFilter;
  });

  async function analyzeWallet() {
    const targetWallet = wallet.trim() || "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae";
    setSearchedWallet(targetWallet);
    setLoading(true);
    setAnalysisError(null);

    // Immediately clear previous results before new analysis begins
    setRiskScore(0);
    setRiskLevel("ANALYZING");
    setReasons([]);
    setVaspMatch({ name: "Analyzing...", confidence: 0 });
    setTxList([]);
    setNodeList([]);

    try {
      // Ensure valid auth token exists
      await api.ensureAuthToken();

      // 1. Trigger live backend risk pipeline
      const riskRes = await api.calculateWalletRisk(targetWallet);
      if (riskRes) {
        const scoreVal = riskRes.score !== undefined ? riskRes.score : (riskRes.risk_score !== undefined ? riskRes.risk_score : 0);
        setRiskScore(Math.round(scoreVal));
        setRiskLevel(riskRes.risk_level || "UNKNOWN");
        setReasons(riskRes.reasons && riskRes.reasons.length > 0 ? riskRes.reasons : ["No specific suspicious signals surfaced."]);
      }

      // 2. Fetch live graph nodes & edges
      try {
        const graphRes = await api.getWalletGraph(targetWallet);
        if (graphRes && graphRes.nodes && graphRes.nodes.length > 0) {
          const apiNodes = graphRes.nodes.map((n, idx) => ({
            id: n.id,
            name: n.label || (n.id.length > 12 ? `${n.id.slice(0, 6)}...${n.id.slice(-4)}` : n.id),
            type: n.type ? n.type.toUpperCase() : "PEER",
            x: 10 + (idx % 4) * 25,
            y: 25 + Math.floor(idx / 4) * 40,
          }));
          setNodeList(apiNodes);
        } else {
          setNodeList([]);
        }
      } catch (e) {
        console.warn("Graph fetch detail:", e);
        setNodeList([]);
      }

      // 3. Fetch VASP attribution
      try {
        const vaspRes = await api.attributeVASP(targetWallet);
        if (vaspRes) {
          setVaspMatch({
            name: vaspRes.vasp_name_guess || "Unidentified Entity",
            confidence: Math.round((vaspRes.confidence_score !== undefined ? vaspRes.confidence_score : 0) * 100),
          });
        } else {
          setVaspMatch({ name: "None Detected", confidence: 0 });
        }
      } catch (e) {
        console.warn("VASP fetch detail:", e);
        setVaspMatch({ name: "Unattributed", confidence: 0 });
      }

      // 4. Fetch transactions list
      try {
        const txs = await api.getWalletTransactions(targetWallet);
        if (txs && txs.length > 0) {
          const formattedTxs = txs.map((tx) => ({
            hash: tx.tx_hash ? `${tx.tx_hash.slice(0, 6)}...${tx.tx_hash.slice(-4)}` : "0x...",
            from: tx.from_address ? `${tx.from_address.slice(0, 8)}...` : "Sender",
            to: tx.to_address ? `${tx.to_address.slice(0, 8)}...` : "Receiver",
            amount: `${tx.amount} ${tx.token_symbol || "ETH"}`,
            time: tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : "Recent",
            status: tx.amount > 1.0 ? "Suspicious" : "Normal",
          }));
          setTxList(formattedTxs);
        } else {
          setTxList([]);
        }
      } catch (e) {
        console.warn("Transactions fetch detail:", e);
        setTxList([]);
      }
    } catch (err) {
      console.error("Backend API Error during wallet analysis:", err);
      setAnalysisError(err.message || "Failed to connect to backend server.");
      // Requirement 10: DO NOT silently mask API failures with mock data!
      setRiskScore(0);
      setRiskLevel("FAILED");
      setReasons([]);
      setVaspMatch({ name: "Analysis Failed", confidence: 0 });
      setTxList([]);
      setNodeList([]);
    } finally {
      setLoading(false);
    }
  }

  async function generateReport() {
    if (!searchedWallet) {
      alert("Please enter and analyze a wallet before generating an investigation report.");
      return;
    }
    setReportGenerated(true);
    try {
      const rep = await api.generateReport(searchedWallet);
      if (rep && rep.id) {
        await api.downloadReport(rep.id);
      }
    } catch (e) {
      console.warn("Direct report download fallback:", e);
    }
  }

  function exportEvidence() {
    if (!searchedWallet) {
      alert("No investigation data available. Please analyze a wallet first.");
      return;
    }

    const txSummary = txList.length > 0
      ? txList.map((tx) => `  - ${tx.hash} | ${tx.from} -> ${tx.to} | ${tx.amount} | ${tx.status}`).join("\n")
      : "  - No transactions recorded for this wallet.";

    const reasonSummary = reasons.length > 0
      ? reasons.map((r) => `  - [!] ${r}`).join("\n")
      : "  - No suspicious signals surfaced.";

    const nodeSummary = nodeList.length > 0
      ? nodeList.map((n) => `  - ${n.name} (${n.id}) [${n.type}]`).join("\n")
      : "  - No graph nodes.";

    const content = `==========================================================================
                CRYPTO FORENSICS INVESTIGATION EVIDENCE EXPORT
                      SIH PROBLEM STATEMENT 26183
==========================================================================
Target Wallet       : ${searchedWallet}
Analysis Timestamp  : ${new Date().toISOString()}
Risk Score          : ${riskScore !== null ? `${riskScore}/100` : "N/A"}
Risk Level          : ${riskLevel}
VASP Attribution    : ${vaspMatch.name} (${vaspMatch.confidence}% Confidence)

SUSPICIOUS SIGNALS & REASONS:
${reasonSummary}

VASP MATCH ATTRIBUTION:
  - Identified Entity : ${vaspMatch.name}
  - Confidence Score  : ${vaspMatch.confidence}%

GRAPH TOPOLOGY (${nodeList.length} Nodes):
${nodeSummary}

ON-CHAIN TRANSACTIONS (${txList.length}):
${txSummary}

==========================================================================
                       END OF EVIDENCE EXPORT
==========================================================================
`;

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `CryptoTrace_Evidence_${searchedWallet.slice(0, 10)}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

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

          <button
            className={
              page === "dashboard"
                ? "navItem active"
                : "navItem"
            }
            onClick={() => setPage("dashboard")}
          >
            <span>▦</span>
            Dashboard
          </button>

          <button
            className={
              page === "investigation"
                ? "navItem active"
                : "navItem"
            }
            onClick={() => setPage("investigation")}
          >
            <span>⌕</span>
            Investigation
          </button>

          <button
            className={
              page === "cases"
                ? "navItem active"
                : "navItem"
            }
            onClick={() => setPage("cases")}
          >
            <span>◈</span>
            Cases
          </button>

          <button
            className={
              page === "vasps"
                ? "navItem active"
                : "navItem"
            }
            onClick={() => setPage("vasps")}
          >
            <span>◉</span>
            VASPs
          </button>

          <button
            className={
              page === "reports"
                ? "navItem active"
                : "navItem"
            }
            onClick={() => setPage("reports")}
          >
            <span>▤</span>
            Reports
          </button>

        </nav>

        <div className="sidebarBottom">
          <strong>SIH 26183</strong>
          <span>Crypto Fraud & VASP Identification</span>
        </div>

      </aside>


      {/* MAIN */}

      <main className="main">

        <header className="topbar">

          <div>
            <span className="breadcrumb">
              CRYPTO FORENSICS / SIH 26183
            </span>

            <h2>
              {page === "dashboard" && "Investigation Dashboard"}
              {page === "investigation" && "Wallet Investigation"}
              {page === "cases" && "Investigation Cases"}
              {page === "vasps" && "VASP Intelligence"}
              {page === "reports" && "Investigation Reports"}
            </h2>
          </div>

          <div className="systemStatus">
            <span className="statusDot"></span>
            SYSTEM ONLINE
          </div>

        </header>


        {/* ================= DASHBOARD ================= */}

        {page === "dashboard" && (

          <div className="content">

            <section className="hero">

              <div>

                <span className="sectionLabel">
                  REAL-TIME BLOCKCHAIN INTELLIGENCE
                </span>

                <h1>
                  Trace. Analyze. <span>Identify.</span>
                </h1>

                <p>
                  Automatically trace suspicious cryptocurrency
                  transactions and identify fraud-linked
                  Virtual Asset Service Providers.
                </p>

                <button
                  className="primaryButton"
                  onClick={() => setPage("investigation")}
                >
                  Start Investigation →
                </button>

              </div>

              <div className="heroGraphic">
                <div className="orbit"></div>
                <div className="heroCoin">₿</div>
              </div>

            </section>


            <section className="statsGrid">

              <div className="statCard">
                <span>ACTIVE CASES</span>
                <strong>12</strong>
                <small>+3 this week</small>
              </div>

              <div className="statCard">
                <span>WALLETS ANALYZED</span>
                <strong>1,284</strong>
                <small>+84 today</small>
              </div>

              <div className="statCard">
                <span>HIGH RISK</span>
                <strong className="redText">37</strong>
                <small>Requires attention</small>
              </div>

              <div className="statCard">
                <span>VASPs IDENTIFIED</span>
                <strong>19</strong>
                <small>Across 6 networks</small>
              </div>

            </section>


            <section className="panel">

              <div className="panelHeader">
                <div>
                  <h2>System Overview</h2>
                  <p>
                    Current blockchain investigation status
                  </p>
                </div>
              </div>

              <div className="overviewGrid">

                <div>
                  <span>NETWORK</span>
                  <strong>Ethereum Mainnet</strong>
                </div>

                <div>
                  <span>BLOCKCHAIN STATUS</span>
                  <strong className="greenText">
                    ● Operational
                  </strong>
                </div>

                <div>
                  <span>LAST SYNC</span>
                  <strong>2 minutes ago</strong>
                </div>

              </div>

            </section>

          </div>

        )}


        {/* ================= INVESTIGATION ================= */}

        {page === "investigation" && (

          <div className="content">

            {/* SEARCH */}

            <section className="panel">

              <div className="panelHeader">

                <div>
                  <h2>Wallet Investigation</h2>

                  <p>
                    Enter a suspect wallet address to
                    trace its cryptocurrency flow.
                  </p>
                </div>

                <span className="liveBadge">
                  ● LIVE
                </span>

              </div>

              <div className="searchBox">

                <input
                  value={wallet}
                  onChange={(e) =>
                    setWallet(e.target.value)
                  }
                  placeholder="Enter wallet address..."
                />

                <button
                  className="primaryButton"
                  onClick={analyzeWallet}
                  disabled={loading}
                >
                  {loading ? "Analyzing..." : "Analyze Wallet"}
                </button>

              </div>

              {analysisError && (
                <div className="searchedWallet" style={{ color: "#ff6b6b", borderLeft: "3px solid #ff6b6b" }}>
                  ⚠️ {analysisError}
                </div>
              )}

              {searchedWallet && !analysisError && (
                <div className="searchedWallet">
                  Analyzing: <strong>{searchedWallet}</strong>
                </div>
              )}

              {!searchedWallet && !analysisError && (
                <div className="searchedWallet" style={{ color: "#8b949e" }}>
                  No investigation conducted yet. Enter a wallet address above and click <strong>Analyze Wallet</strong>.
                </div>
              )}

            </section>


            {/* RISK CARDS */}

            <section className="statsGrid">

              <div className="statCard">
                <span>TRANSACTIONS</span>
                <strong>{txList.length}</strong>
                <small>Detected transactions</small>
              </div>

              <div className="statCard">
                <span>RISK SCORE</span>
                <strong className={riskScore === null ? "" : (riskScore >= 75 ? "redText" : "greenText")}>
                  {riskScore !== null ? `${riskScore}/100` : "--"}
                </strong>
                <small>Probability of fraud</small>
              </div>

              <div className="statCard">
                <span>RISK LEVEL</span>
                <strong className={riskLevel === "HIGH" ? "redText" : (riskLevel === "LOW" ? "greenText" : "")}>
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


            {/* GRAPH */}

            <section className="panel">

              <div className="panelHeader">

                <div>
                  <h2>Transaction Flow</h2>

                  <p>
                    Visual trace of the suspected
                    cryptocurrency money flow.
                  </p>
                </div>

                <span className="liveBadge">
                  LIVE ANALYSIS
                </span>

              </div>


              <div className="graphArea">

                {nodeList.length === 0 ? (
                  <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "#8b949e" }}>
                    {riskLevel === "ANALYZING" ? "Analyzing blockchain network flow..." : "No investigation graph loaded. Enter a wallet address above and click 'Analyze Wallet'."}
                  </div>
                ) : (
                  <>
                    {/* CONNECTIONS */}
                    <div className="flowLine flow1"></div>
                    <div className="flowLine flow2"></div>
                    <div className="flowLine flow3"></div>
                    <div className="flowLine flow4"></div>
                    <div className="flowLine flow5"></div>
                    <div className="flowLine flow6"></div>

                    {/* NODES */}
                    {nodeList.map((node) => (
                      <button
                        key={node.id}
                        className={
                          selectedNode === node.id
                            ? "graphNode selected"
                            : "graphNode"
                        }
                        style={{
                          left: `${node.x}%`,
                          top: `${node.y}%`,
                        }}
                        onClick={() =>
                          setSelectedNode(node.id)
                        }
                      >
                        <strong>
                          {node.name}
                        </strong>

                        <span>
                          {node.type}
                        </span>
                      </button>
                    ))}

                    {/* NODE DETAILS */}
                    {selectedNode && (
                      <div className="nodeDetails">
                        <button
                          className="closeButton"
                          onClick={() =>
                            setSelectedNode(null)
                          }
                        >
                          ×
                        </button>

                        <small>
                          SELECTED ENTITY
                        </small>

                        <h3>
                          {
                            nodeList.find(
                              (node) =>
                                node.id === selectedNode
                            )?.name || selectedNode
                          }
                        </h3>

                        <p>
                          Entity detected in the
                          cryptocurrency money-flow path.
                        </p>

                        <div className="detailRow">
                          <span>Network</span>
                          <strong>Ethereum</strong>
                        </div>

                        <div className="detailRow">
                          <span>Type</span>
                          <strong className="redText">
                            {nodeList.find((n) => n.id === selectedNode)?.type || "PEER"}
                          </strong>
                        </div>
                      </div>
                    )}
                  </>
                )}

              </div>

            </section>


            {/* FRAUD + VASP */}

            <div className="twoColumn">

              <section className="panel">

                <div className="panelHeader">
                  <div>
                    <h2>Fraud Indicators</h2>
                    <p>
                      Signals contributing to the risk score
                    </p>
                  </div>
                </div>

                {riskLevel === "NOT ANALYZED" ? (
                  <div className="indicator">
                    <span style={{ color: "#8b949e" }}>No wallet investigation conducted yet.</span>
                    <strong style={{ color: "#8b949e" }}>IDLE</strong>
                  </div>
                ) : reasons && reasons.length > 0 ? (
                  reasons.map((reason, idx) => (
                    <div key={idx} className="indicator">
                      <span>{reason}</span>
                      <strong className="redText">DETECTED</strong>
                    </div>
                  ))
                ) : (
                  <div className="indicator">
                    <span>No suspicious signals detected</span>
                    <strong className="greenText">CLEAN</strong>
                  </div>
                )}

              </section>


              <section className="panel">

                <div className="panelHeader">
                  <div>
                    <h2>VASP Attribution</h2>
                    <p>
                      Potential service connected to the flow
                    </p>
                  </div>
                </div>

                <div className="vaspCard">

                  <div className="vaspIcon">
                    ◉
                  </div>

                  <div>
                    <span>IDENTIFIED VASP</span>
                    <h3>{vaspMatch.name}</h3>
                    <p>
                      Destination wallet attribution result.
                    </p>
                  </div>

                </div>

                <div className="confidence">

                  <div>
                    <span>ATTRIBUTION CONFIDENCE</span>
                    <strong>{vaspMatch.confidence}%</strong>
                  </div>

                  <div className="progress">
                    <div
                      className="progressFill"
                      style={{ width: `${vaspMatch.confidence}%` }}
                    ></div>
                  </div>

                </div>

              </section>

            </div>


            {/* TIMELINE */}

            <section className="panel">

              <div className="panelHeader">

                <div>
                  <h2>Investigation Timeline</h2>
                  <p>
                    Sequence of detected money-flow events
                  </p>
                </div>

              </div>

              <div className="timeline">

                <div className="timelineItem">
                  <span className="timelineDot"></span>

                  <div>
                    <strong>
                      Suspect wallet reported
                    </strong>

                    <p>
                      Initial wallet entered for investigation.
                    </p>

                    <small>Recent</small>
                  </div>
                </div>

                <div className="timelineItem">
                  <span className="timelineDot"></span>

                  <div>
                    <strong>
                      Suspicious transactions detected
                    </strong>

                    <p>
                      Funds moved through intermediary wallets.
                    </p>

                    <small>Recent</small>
                  </div>
                </div>

                <div className="timelineItem">
                  <span className="timelineDot"></span>

                  <div>
                    <strong>
                      Consolidation wallet identified
                    </strong>

                    <p>
                      Multiple transaction paths converged.
                    </p>

                    <small>Recent</small>
                  </div>
                </div>

                <div className="timelineItem">
                  <span className="timelineDot"></span>

                  <div>
                    <strong>
                      Potential VASP connection found
                    </strong>

                    <p>
                      Destination address matched exchange
                      behaviour pattern.
                    </p>

                    <small>Recent</small>
                  </div>
                </div>

              </div>

            </section>


            {/* TRANSACTION TABLE */}

            <section className="panel">

              <div className="panelHeader">

                <div>
                  <h2>Recent Transactions</h2>
                  <p>
                    Transactions detected in the traced path
                  </p>
                </div>

                <div className="tableControls">

                  <input
                    value={transactionSearch}
                    onChange={(e) =>
                      setTransactionSearch(e.target.value)
                    }
                    placeholder="Search..."
                  />

                  <select
                    value={filter}
                    onChange={(e) =>
                      setFilter(e.target.value)}
                  >
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

                    {filteredTransactions.length > 0 ? (
                      filteredTransactions.map((tx) => (
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
                      ))
                    ) : (
                      <tr>
                        <td colSpan="6" style={{ textAlign: "center", padding: "20px", color: "#8b949e" }}>
                          {searchedWallet ? "No transactions found for this wallet." : "No investigation conducted yet. Enter a wallet above to fetch transactions."}
                        </td>
                      </tr>
                    )}

                  </tbody>

                </table>

              </div>

            </section>


            {/* INVESTIGATION SUMMARY */}

            <section className="panel">

              <div className="panelHeader">

                <div>
                  <h2>Investigation Summary</h2>

                  <p>
                    Automated analysis conclusion
                  </p>
                </div>

              </div>


              <div className="summaryBox">

                <div className="summaryScore">

                  <strong>{riskScore !== null ? riskScore : "--"}</strong>

                  <span>
                    RISK SCORE
                  </span>

                </div>


                <div className="summaryText">

                  <h3>
                    {riskLevel === "NOT ANALYZED" ? "No Investigation Conducted Yet" : `${riskLevel} Risk Flow Detected (${riskScore}/100)`}
                  </h3>

                  <p>
                    {riskLevel === "NOT ANALYZED"
                      ? "Enter a suspect wallet address above to trace transaction flows, compute risk score, and identify VASP attribution."
                      : `The investigated wallet demonstrates an overall risk level of ${riskLevel} with a calculated score of ${riskScore}/100. Attribution matching identified VASP target "${vaspMatch.name}" with ${vaspMatch.confidence}% confidence.`}
                  </p>

                </div>

              </div>


              <div className="actionButtons">

                <button
                  className="primaryButton"
                  onClick={generateReport}
                  disabled={!searchedWallet || loading}
                >
                  Generate Investigation Report
                </button>

                <button
                  className="secondaryButton"
                  onClick={exportEvidence}
                  disabled={!searchedWallet || loading}
                >
                  Export Evidence
                </button>

              </div>


              {reportGenerated && (

                <div className="successMessage">
                  ✓ Investigation report generated successfully.
                </div>

              )}

            </section>

          </div>

        )}


{/* CASES */}

{page === "cases" && (

  <div className="content">

    <section className="panel">

      <div className="panelHeader">

        <div>
          <h2>Investigation Cases</h2>

          <p>
            Active blockchain fraud investigations
          </p>
        </div>

      </div>


      <div className="caseGrid">

        <div className="caseCard">
          <span>CASE-26183</span>
          <h3>Crypto Investment Fraud</h3>
          <p>Ethereum • High Risk</p>
          <strong>OPEN</strong>
        </div>


        <div className="caseCard">
          <span>CASE-26171</span>
          <h3>Phishing Wallet</h3>
          <p>Ethereum • Medium Risk</p>
          <strong>UNDER REVIEW</strong>
        </div>


        <div className="caseCard">
          <span>CASE-26154</span>
          <h3>Suspicious VASP Flow</h3>
          <p>Ethereum • High Risk</p>
          <strong>OPEN</strong>
        </div>

      </div>

    </section>

  </div>

)}


{/* VASPS */}

{page === "vasps" && (

  <div className="content">

    <section className="panel">

      <div className="panelHeader">

        <div>
          <h2>VASP Intelligence</h2>

          <p>
            Potential cryptocurrency service providers
          </p>
        </div>

      </div>


      <div className="vaspList">

        <div className="vaspListItem">

          <div>
            <strong>Potential Exchange</strong>

            <span>
              Ethereum destination cluster
            </span>
          </div>

          <b>92%</b>

        </div>


        <div className="vaspListItem">

          <div>
            <strong>Exchange Cluster B</strong>

            <span>
              Historical transaction match
            </span>
          </div>

          <b>76%</b>

        </div>


        <div className="vaspListItem">

          <div>
            <strong>Exchange Cluster C</strong>

            <span>
              Behavioural similarity
            </span>
          </div>

          <b>64%</b>

        </div>

      </div>

    </section>

  </div>

)}


{/* REPORTS */}

{page === "reports" && (

  <div className="content">

    <section className="panel">

      <div className="panelHeader">

        <div>
          <h2>Investigation Reports</h2>

          <p>
            Generated investigation evidence
          </p>
        </div>

      </div>


      <div className="reportCard">

        <div>

          <span>
            REPORT-26183
          </span>

          <h3>
            Crypto Fraud Wallet Investigation
          </h3>

          <p>
            Risk Score: 87 • VASP Confidence: 92%
          </p>

        </div>


        <button
          className="secondaryButton"
          onClick={exportEvidence}
        >
          Export
        </button>

      </div>

    </section>

  </div>

)}

</main>

</div>
  );
}

export default App;