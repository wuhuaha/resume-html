const API_BASE = import.meta.env.VITE_API_BASE || "";

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

export function getSiteStyle() {
  return request("/api/site-style");
}

export function askProfile(question, history = []) {
  return request("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });
}

export function getVoiceConfig() {
  return request("/api/voice/config");
}

export function getVoiceHotwords() {
  return request("/api/voice/hotwords");
}

export function transcribeVoice(blob) {
  const form = new FormData();
  const extension = blob.type.includes("wav") ? "wav" : "webm";
  form.append("file", blob, `question.${extension}`);
  return request("/api/voice/asr", {
    method: "POST",
    body: form,
  });
}

export async function streamTranscribeVoice(blob, onText) {
  const form = new FormData();
  const extension = blob.type.includes("wav") ? "wav" : "webm";
  form.append("file", blob, `question.${extension}`);
  const response = await fetch(`${API_BASE}/api/voice/asr/stream`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const textBody = await response.text();
    let message = textBody;
    try {
      message = JSON.parse(textBody).detail || textBody;
    } catch {
      message = textBody;
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }

  if (!response.body) {
    const text = await response.text();
    onText(text);
    return text;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let collected = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    if (chunk) {
      collected += chunk;
      onText(collected);
    }
  }
  const tail = decoder.decode();
  if (tail) {
    collected += tail;
    onText(collected);
  }
  return collected;
}

export async function synthesizeVoice(text, referenceAudioDataUrl = "") {
  const response = await fetch(`${API_BASE}/api/voice/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, referenceAudioDataUrl }),
  });
  if (!response.ok) {
    const textBody = await response.text();
    let message = textBody;
    try {
      message = JSON.parse(textBody).detail || textBody;
    } catch {
      message = textBody;
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.blob();
}

export async function streamSynthesizeVoice(text, referenceAudioDataUrl = "") {
  const response = await fetch(`${API_BASE}/api/voice/tts/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, referenceAudioDataUrl }),
  });
  if (!response.ok) {
    const textBody = await response.text();
    let message = textBody;
    try {
      message = JSON.parse(textBody).detail || textBody;
    } catch {
      message = textBody;
    }
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.body;
}

export function exportResume(payload) {
  return request("/api/resume/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getResumeExportConfig() {
  return request("/api/resume/export-config");
}

export function adminLogin(password) {
  return request("/api/admin/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
}

export function getAdminMode() {
  return request("/api/admin/mode");
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

export function getAdminSiteStyle(password) {
  return request("/api/admin/site-style", {
    headers: adminHeaders(password),
  });
}

export function saveAdminSiteStyle(password, activeKey) {
  return request("/api/admin/site-style", {
    method: "PUT",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify({ activeKey }),
  });
}

export function getAdminResumeExportConfig(password) {
  return request("/api/admin/resume-export-config", {
    headers: adminHeaders(password),
  });
}

export function getResumeAvatar(password) {
  return request("/api/admin/resume-avatar", {
    headers: adminHeaders(password),
  });
}

export function saveResumeAvatar(password, blob, filename = "resume-avatar.png") {
  const form = new FormData();
  form.append("file", blob, filename);
  return request("/api/admin/resume-avatar", {
    method: "PUT",
    headers: adminHeaders(password),
    body: form,
  });
}

export function deleteResumeAvatar(password) {
  return request("/api/admin/resume-avatar", {
    method: "DELETE",
    headers: adminHeaders(password),
  });
}

export function getVoiceCloneReference(password) {
  return request("/api/admin/voice-clone/reference", {
    headers: adminHeaders(password),
  });
}

export function saveVoiceCloneReference(password, blob, filename = "voice-reference.wav") {
  const form = new FormData();
  form.append("file", blob, filename);
  return request("/api/admin/voice-clone/reference", {
    method: "PUT",
    headers: adminHeaders(password),
    body: form,
  });
}

export function deleteVoiceCloneReference(password) {
  return request("/api/admin/voice-clone/reference", {
    method: "DELETE",
    headers: adminHeaders(password),
  });
}

export function saveAdminResumeExportConfig(password, config) {
  return request("/api/admin/resume-export-config", {
    method: "PUT",
    headers: adminHeaders(password, { "Content-Type": "application/json" }),
    body: JSON.stringify(config),
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
