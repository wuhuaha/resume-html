const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    let message = text;
    try {
      message = JSON.parse(text).detail || text;
    } catch {
      message = text;
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json();
}

function adminHeaders(password, extra = {}) {
  return {
    ...extra,
    "X-Admin-Password": password,
  };
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

export function adminLogin(password) {
  return request("/api/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
}

export function getMarkdownDocument(password) {
  return request("/api/admin/markdown", {
    headers: adminHeaders(password),
  });
}

export function saveMarkdownDocument(password, markdown) {
  return request("/api/admin/markdown", {
    method: "PUT",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ markdown }),
  });
}

export function aiEditMarkdown(password, markdown, instruction) {
  return request("/api/admin/ai/edit", {
    method: "POST",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ markdown, instruction }),
  });
}

export function previewMarkdownBriefing(password, markdown) {
  return request("/api/admin/preview", {
    method: "POST",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ markdown }),
  });
}

export function getHomeBriefingDraft(password) {
  return request("/api/admin/home-briefing", {
    headers: adminHeaders(password),
  });
}

export function aiEditHomeBriefing(password, briefing, instruction) {
  return request("/api/admin/home-briefing/ai", {
    method: "POST",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ briefing, instruction }),
  });
}

export function saveHomeBriefing(password, briefing) {
  return request("/api/admin/home-briefing", {
    method: "PUT",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ briefing }),
  });
}

export function importDocument(password, file) {
  const form = new FormData();
  form.append("file", file);
  return request("/api/admin/import", {
    method: "POST",
    headers: adminHeaders(password),
    body: form,
  });
}

export function reindexContent(password) {
  return request("/api/admin/reindex", {
    method: "POST",
    headers: adminHeaders(password),
  });
}
