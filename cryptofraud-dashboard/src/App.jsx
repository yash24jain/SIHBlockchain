import { useState } from "react";
import "./App.css";

const transactions = [
  {
    hash: "0x8a21...91fd",
    from: "Suspect Wallet",
    to: "Wallet A",
    amount: "1.42 ETH",
    time: "10:42 AM",
    status: "Suspicious",
  },
  {
    hash: "0x72bc...44ae",
    from: "Suspect Wallet",
    to: "Wallet B",
    amount: "0.82 ETH",
    time: "10:38 AM",
    status: "Suspicious",
  },
  {
    hash: "0x51de...8201",
    from: "Wallet A",
    to: "Consolidation",
    amount: "1.10 ETH",
    time: "10:31 AM",
    status: "Normal",
  },
  {
    hash: "0x44fa...71bc",
    from: "Wallet B",
    to: "Consolidation",
    amount: "0.76 ETH",
    time: "10:25 AM",
    status: "Suspicious",
  },
  {
    hash: "0x31ab...992e",
    from: "Consolidation",
    to: "Wallet C",
    amount: "0.54 ETH",
    time: "10:19 AM",
    status: "Normal",
  },
  {
    hash: "0x21cd...77af",
    from: "Consolidation",
    to: "VASP",
    amount: "1.32 ETH",
    time: "10:11 AM",
    status: "Suspicious",
  },
];

const nodes = [
  { id: "suspect", name: "Suspect Wallet", type: "HIGH RISK", x: 7, y: 45 },
  { id: "walletA", name: "Wallet A", type: "INTERMEDIATE", x: 27, y: 25 },
  { id: "walletB", name: "Wallet B", type: "HIGH RISK", x: 27, y: 68 },
  {
    id: "consolidation",
    name: "Consolidation",
    type: "SUSPICIOUS",
    x: 51,
    y: 45,
  },
  { id: "walletC", name: "Wallet C", type: "INTERMEDIATE", x: 75, y: 25 },
  { id: "vasp", name: "VASP", type: "EXCHANGE", x: 75, y: 68 },
];

function App() {
  const [page, setPage] = useState("dashboard");
  const [wallet, setWallet] = useState("");
  const [searchedWallet, setSearchedWallet] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [transactionSearch, setTransactionSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [reportGenerated, setReportGenerated] = useState(false);

  const filteredTransactions = transactions.filter((tx) => {
    const search = transactionSearch.toLowerCase();

    const matchesSearch =
      tx.hash.toLowerCase().includes(search) ||
      tx.from.toLowerCase().includes(search) ||
      tx.to.toLowerCase().includes(search);

    const matchesFilter =
      filter === "All" || tx.status === filter;

    return matchesSearch && matchesFilter;
  });

  function analyzeWallet() {
    if (wallet.trim() === "") {
      setSearchedWallet("0x742d...f44e");
    } else {
      setSearchedWallet(wallet);
    }
  }

  function generateReport() {
    setReportGenerated(true);
  }

  function exportEvidence() {
    const content = `CryptoTrace Investigation Evidence

Wallet: ${searchedWallet || "0x742d...f44e"}
Risk Score: 87/100
Risk Level: HIGH
VASP Match: 92%

Transactions:
${transactions
  .map(
    (tx) =>
      `${tx.hash} | ${tx.from} -> ${tx.to} | ${tx.amount} | ${tx.status}`
  )
  .join("\n")}

VASP Attribution:
Potential VASP connection identified with 92% confidence.
`;

    const blob = new Blob([content], {
      type: "text/plain",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "cryptotrace-evidence.txt";
    link.click();

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
                >
                  Analyze Wallet
                </button>

              </div>

              {searchedWallet && (
                <div className="searchedWallet">
                  Analyzing: <strong>{searchedWallet}</strong>
                </div>
              )}

            </section>


            {/* RISK CARDS */}

            <section className="statsGrid">

              <div className="statCard">
                <span>TRANSACTIONS</span>
                <strong>24</strong>
                <small>Detected transactions</small>
              </div>

              <div className="statCard">
                <span>RISK SCORE</span>
                <strong className="redText">87/100</strong>
                <small>High probability of fraud</small>
              </div>

              <div className="statCard">
                <span>RISK LEVEL</span>
                <strong className="redText">HIGH</strong>
                <small>Immediate attention</small>
              </div>

              <div className="statCard">
                <span>VASP MATCH</span>
                <strong>92%</strong>
                <small>Attribution confidence</small>
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

                {/* CONNECTIONS */}

                <div className="flowLine flow1"></div>
                <div className="flowLine flow2"></div>
                <div className="flowLine flow3"></div>
                <div className="flowLine flow4"></div>
                <div className="flowLine flow5"></div>
                <div className="flowLine flow6"></div>


                {/* AMOUNTS */}

                <span className="flowAmount a1">
                  1.42 ETH
                </span>

                <span className="flowAmount a2">
                  0.82 ETH
                </span>

                <span className="flowAmount a3">
                  1.10 ETH
                </span>

                <span className="flowAmount a4">
                  0.76 ETH
                </span>

                <span className="flowAmount a5">
                  0.54 ETH
                </span>

                <span className="flowAmount a6">
                  1.32 ETH
                </span>


                {/* NODES */}

                {nodes.map((node) => (

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
                        nodes.find(
                          (node) =>
                            node.id === selectedNode
                        )?.name
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
                      <span>Risk</span>
                      <strong className="redText">
                        High
                      </strong>
                    </div>

                  </div>

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

                <div className="indicator">
                  <span>Rapid fund movement</span>
                  <strong>HIGH</strong>
                </div>

                <div className="indicator">
                  <span>Multiple intermediary wallets</span>
                  <strong>HIGH</strong>
                </div>

                <div className="indicator">
                  <span>Fund consolidation</span>
                  <strong>HIGH</strong>
                </div>

                <div className="indicator">
                  <span>Exchange interaction</span>
                  <strong>MEDIUM</strong>
                </div>

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
                    <h3>Potential Exchange</h3>
                    <p>
                      Destination wallet matches known
                      exchange behaviour.
                    </p>
                  </div>

                </div>

                <div className="confidence">

                  <div>
                    <span>ATTRIBUTION CONFIDENCE</span>
                    <strong>92%</strong>
                  </div>

                  <div className="progress">
                    <div
                      className="progressFill"
                      style={{ width: "92%" }}
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

                    <small>10:42 AM</small>
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

                    <small>10:38 AM</small>
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

                    <small>10:25 AM</small>
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
                      behaviour with 92% confidence.
                    </p>

                    <small>10:11 AM</small>
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

      {filteredTransactions.map((tx) => (
        <tr key={tx.hash}>

          <td className="hash">
            {tx.hash}
          </td>

          <td>
            {tx.from}
          </td>

          <td>
            {tx.to}
          </td>

          <td>
            {tx.amount}
          </td>

          <td>
            {tx.time}
          </td>

          <td>

            <span
              className={
                tx.status === "Suspicious"
                  ? "status suspicious"
                  : "status normal"
              }
            >
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

      <p>
        Automated analysis conclusion
      </p>
    </div>

  </div>


  <div className="summaryBox">

    <div className="summaryScore">

      <strong>87</strong>

      <span>
        RISK SCORE
      </span>

    </div>


    <div className="summaryText">

      <h3>
        High-risk cryptocurrency flow detected
      </h3>

      <p>
        The investigated wallet demonstrates multiple
        suspicious transaction patterns, including rapid
        fund movement, intermediary wallet usage and fund
        consolidation. The traced flow reaches a potential
        VASP with an estimated attribution confidence of 92%.
      </p>

    </div>

  </div>


  <div className="actionButtons">

    <button
      className="primaryButton"
      onClick={generateReport}
    >
      Generate Investigation Report
    </button>

    <button
      className="secondaryButton"
      onClick={exportEvidence}
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