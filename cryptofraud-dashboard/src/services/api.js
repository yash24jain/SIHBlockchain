// API Client for SIH26183 Backend Gateway (member3-backend)

const API_BASE_URL = "http://localhost:8000";

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(username, password) {
  const params = new URLSearchParams();
  params.append("username", username);
  params.append("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });

  if (!response.ok) {
    throw new Error(`Login failed (${response.status})`);
  }

  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
  }
  return data;
}

export async function registerUser(username, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password, full_name: "Investigator" }),
  });
  if (!response.ok && response.status !== 400) {
    throw new Error(`Registration failed (${response.status})`);
  }
  return response.json();
}

export async function ensureAuthToken() {
  let token = localStorage.getItem("token");
  if (!token) {
    try {
      await login("test_investigator_e2e", "SecurePassword123!");
    } catch (e) {
      try {
        await registerUser("test_investigator_e2e", "investigator@example.com", "SecurePassword123!");
        await login("test_investigator_e2e", "SecurePassword123!");
      } catch (err) {
        console.error("Auto-authentication failed:", err);
      }
    }
  }
}

export async function calculateWalletRisk(walletAddress) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/risk/calculate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ wallet_address: walletAddress, chain: "ethereum" }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Risk evaluation failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function getWalletGraph(walletAddress) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/graph/${walletAddress}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Graph retrieval failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function getWalletTransactions(walletAddress) {
  await ensureAuthToken();
  const response = await fetch(
    `${API_BASE_URL}/transactions?wallet_address=${walletAddress}`,
    {
      headers: getAuthHeaders(),
    }
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Transactions retrieval failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function attributeVASP(walletAddress) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/vasp/attribute/${walletAddress}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`VASP attribution failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function generateReport(walletAddress) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ wallet_address: walletAddress, title: `Investigation Report for ${walletAddress}` }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Report generation failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function getReportStatus(reportId) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Report status failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function downloadReport(reportId) {
  await ensureAuthToken();
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Report download failed (${response.status}): ${errorText}`);
  }
  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition");
  let filename = `Crypto_Trace_Evidence_${reportId}.pdf`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }
  const pdfBlob = new Blob([blob], { type: "application/pdf" });
  const url = window.URL.createObjectURL(pdfBlob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}


