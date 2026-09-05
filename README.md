# SIHBlockchain
SIH 


GUYS LOOK INTO THIS


Chirag (Graph) — his module's output needs to match the shape in app/services/graph_client.py's mock (nodes, edges, patterns)
Ansh (Blockchain data) — he can push data straight into POST /transactions/bulk
Member 4 (Risk/ML) — same pattern, via risk_client.py
Member 5 (Frontend) — give them http://localhost:8000 as the API base URL, and the /auth/login form-data change I just made (important, so their login request isn't silently broken)
Member 6 (VASP + Reports) — vasp_client.py + the report generator stub in reports.py
