export function normalizeBriefingForDisplay(briefing) {
  if (!briefing) return briefing;
  return {
    ...briefing,
    metrics: normalizeMetrics(briefing.metrics || []),
    fitSignals: normalizeFitSignals(briefing.fitSignals || []),
  };
}

function normalizeMetrics(metrics) {
  return metrics.map((item) => {
    const next = { ...item };
    const label = String(next.label || "");
    const note = String(next.note || "");
    if (label.includes("首token") || label.includes("首 token")) {
      next.value = next.value === "1s" ? "10s→1s" : next.value;
      next.label = "P95 端到端首帧语音延迟";
      if (!note || note.includes("首 token") || note.includes("首token")) {
        next.note = "上下文裁剪、模型路由、流式响应、缓存和并行链路优化";
      }
    }
    if (label === "成本降低" || label === "语义链路成本降低") {
      next.label = "Token 成本降低";
      if (!note || note.includes("架构重构") || note.includes("语义链路")) {
        next.note = "模型分层路由、上下文治理与缓存协同";
      }
    }
    if (label === "产品成本降低") {
      next.label = "ASR/TTS 成本降低";
    }
    return next;
  }).filter((item) => !String(item.label || "").includes("讯飞NLP"));
}

function normalizeFitSignals(items) {
  return items.map((item) => ({
    ...item,
    detail: String(item.detail || "")
      .replace(/首\s*token/g, "端到端首帧语音延迟")
      .replace(/首token/g, "端到端首帧语音延迟"),
  }));
}
