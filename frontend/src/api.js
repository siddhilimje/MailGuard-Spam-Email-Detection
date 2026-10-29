const API_BASE = "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check returned status ${res.status}`);
  }
  return await res.json();
}

export async function fetchModelInfo() {
  const res = await fetch(`${API_BASE}/model/info`);
  if (!res.ok) {
    throw new Error(`Model info returned status ${res.status}`);
  }
  return await res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) {
    throw new Error(`Metrics endpoint returned status ${res.status}`);
  }
  return await res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) {
    throw new Error(`Stats endpoint returned status ${res.status}`);
  }
  return await res.json();
}

export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) {
    throw new Error(`History endpoint returned status ${res.status}`);
  }
  const data = await res.json();
  return data.history;
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE}/api/samples`);
  if (!res.ok) {
    throw new Error(`Samples endpoint returned status ${res.status}`);
  }
  return await res.json();
}

export async function predictEmail(payload) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sender: payload.sender || "sender@example.com",
      subject: payload.subject || "",
      body: payload.body || ""
    })
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody.detail || errorBody.error || `Server responded with status ${res.status}`;
    throw new Error(message);
  }

  return await res.json();
}

export async function predictBatch(emails) {
  const res = await fetch(`${API_BASE}/predict/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      emails: emails.map(e => ({
        sender: e.sender || "sender@example.com",
        subject: e.subject || "",
        body: e.body || ""
      }))
    })
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody.detail || errorBody.error || `Server responded with status ${res.status}`;
    throw new Error(message);
  }

  return await res.json();
}

export async function submitFeedback(payload) {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Feedback submission returned status ${res.status}`);
  }
  return await res.json();
}

export async function fetchDriftMetrics() {
  const res = await fetch(`${API_BASE}/api/monitoring/drift`);
  if (!res.ok) {
    throw new Error(`Drift metrics returned status ${res.status}`);
  }
  return await res.json();
}

export async function runDriftCheck(stream = "logs") {
  const res = await fetch(`${API_BASE}/api/monitoring/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stream })
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Drift check failed with status ${res.status}`);
  }
  return await res.json();
}

export async function triggerModelRetrain(force = false) {
  const res = await fetch(`${API_BASE}/api/retrain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force })
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Retraining failed with status ${res.status}`);
  }
  return await res.json();
}
