const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export function getProfile() {
  return request("/api/profile");
}

export function getBriefing() {
  return request("/api/briefing");
}

export function askProfile(question, history = []) {
  return request("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
}

export function exportResume(payload) {
  return request("/api/resume/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function importDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/api/admin/import", {
    method: "POST",
    body: form,
  });
}

export function reindexContent() {
  return request("/api/admin/reindex", { method: "POST" });
}
