import { computed, ref, watch } from "vue";
import { getSiteStyle } from "./api";

const STORAGE_KEY = "ai-profile-style-preview";

export const fallbackPresets = [
  {
    key: "linear-pro",
    label: "Linear 专业风",
    source: "Linear / recruiting console",
    description: "克制、清晰、信息密度高，适合招聘方快速判断能力证据。",
    accent: "#126d64",
    accent2: "#1d4f91",
    accentSoft: "#e7f3f0",
    topGlow: "rgba(231, 243, 240, 0.68)",
    bg: "#f6f7f5",
    surface: "#ffffff",
    surfaceSoft: "#f1f4f2",
    ink: "#141716",
    muted: "#616966",
    subtle: "#8d9692",
    line: "#dce3df",
    lineStrong: "#c7d0cb",
    radius: "8px",
    shadow: "0 16px 44px rgba(31, 40, 36, 0.08)",
    shadowSoft: "0 10px 28px rgba(31, 40, 36, 0.05)",
    panelAlpha: "0.88",
    density: "compact",
    cardTone: "crisp",
  },
  {
    key: "mintlify-docs",
    label: "Mintlify 文档风",
    source: "Mintlify / technical docs",
    description: "技术文档感更强，强调结构、可读性和清爽的浅色界面。",
    accent: "#0f766e",
    accent2: "#2563eb",
    accentSoft: "#e6f6f3",
    topGlow: "rgba(230, 246, 243, 0.76)",
    bg: "#fbfcfc",
    surface: "#ffffff",
    surfaceSoft: "#f3f7f7",
    ink: "#101828",
    muted: "#5d6675",
    subtle: "#98a2b3",
    line: "#e4e7ec",
    lineStrong: "#cfd6df",
    radius: "8px",
    shadow: "0 18px 48px rgba(16, 24, 40, 0.07)",
    shadowSoft: "0 8px 24px rgba(16, 24, 40, 0.045)",
    panelAlpha: "0.9",
    density: "comfortable",
    cardTone: "document",
  },
  {
    key: "notion-editorial",
    label: "Notion 编辑风",
    source: "Notion / editorial profile",
    description: "阅读感更柔和，适合突出履历叙事、项目脉络和长期能力沉淀。",
    accent: "#7a4f2a",
    accent2: "#2f6f73",
    accentSoft: "#f4eee6",
    topGlow: "rgba(244, 238, 230, 0.72)",
    bg: "#faf8f4",
    surface: "#fffdf9",
    surfaceSoft: "#f3efe7",
    ink: "#1f1f1d",
    muted: "#67635d",
    subtle: "#9a948b",
    line: "#e5ded2",
    lineStrong: "#cec4b6",
    radius: "6px",
    shadow: "0 14px 38px rgba(63, 51, 38, 0.07)",
    shadowSoft: "0 8px 20px rgba(63, 51, 38, 0.045)",
    panelAlpha: "0.86",
    density: "comfortable",
    cardTone: "editorial",
  },
  {
    key: "ibm-enterprise",
    label: "IBM 企业风",
    source: "IBM Carbon / enterprise systems",
    description: "正式、理性、系统工程感强，适合后端、分布式和可靠性方向表达。",
    accent: "#0f62fe",
    accent2: "#198038",
    accentSoft: "#edf5ff",
    topGlow: "rgba(237, 245, 255, 0.76)",
    bg: "#f4f4f4",
    surface: "#ffffff",
    surfaceSoft: "#f2f4f8",
    ink: "#161616",
    muted: "#525252",
    subtle: "#8d8d8d",
    line: "#e0e0e0",
    lineStrong: "#c6c6c6",
    radius: "2px",
    shadow: "0 12px 34px rgba(22, 22, 22, 0.075)",
    shadowSoft: "0 6px 18px rgba(22, 22, 22, 0.045)",
    panelAlpha: "0.92",
    density: "compact",
    cardTone: "enterprise",
  },
];

const fallbackStyle = fallbackPresets[0];
const storedPreviewKey = localStorage.getItem(STORAGE_KEY);

export const stylePresets = ref([...fallbackPresets]);
export const publishedStyleKey = ref(fallbackStyle.key);
export const activeKey = ref(
  fallbackPresets.some((preset) => preset.key === storedPreviewKey) ? storedPreviewKey : fallbackStyle.key,
);

export const activeTheme = computed(
  () => stylePresets.value.find((preset) => preset.key === activeKey.value) || fallbackStyle,
);

export const themes = stylePresets;

export function setTheme(key, options = {}) {
  if (!stylePresets.value.some((preset) => preset.key === key)) return;
  activeKey.value = key;
  if (options.persistPreview !== false) {
    localStorage.setItem(STORAGE_KEY, key);
  }
}

export function clearThemePreview() {
  localStorage.removeItem(STORAGE_KEY);
  activeKey.value = publishedStyleKey.value;
}

export async function loadPublishedStyle() {
  const result = await getSiteStyle();
  applyStylePayload(result);
  const previewKey = localStorage.getItem(STORAGE_KEY);
  if (previewKey && stylePresets.value.some((preset) => preset.key === previewKey)) {
    activeKey.value = previewKey;
  } else {
    activeKey.value = result.activeKey;
  }
  return result;
}

export function applyStylePayload(payload) {
  if (Array.isArray(payload?.presets) && payload.presets.length) {
    stylePresets.value = payload.presets;
  }
  if (payload?.activeKey && stylePresets.value.some((preset) => preset.key === payload.activeKey)) {
    publishedStyleKey.value = payload.activeKey;
  }
}

export function markPublishedStyle(key) {
  if (!stylePresets.value.some((preset) => preset.key === key)) return;
  publishedStyleKey.value = key;
  activeKey.value = key;
  localStorage.removeItem(STORAGE_KEY);
}

export function useTheme() {
  return {
    activeKey,
    activeTheme,
    themes,
    publishedStyleKey,
    setTheme,
    clearThemePreview,
  };
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.dataset.theme = theme.key;
  root.dataset.density = theme.density || "compact";
  root.dataset.cardTone = theme.cardTone || "crisp";
  root.style.setProperty("--bg", theme.bg);
  root.style.setProperty("--surface", theme.surface || "#ffffff");
  root.style.setProperty("--surface-soft", theme.surfaceSoft);
  root.style.setProperty("--ink", theme.ink || "#141716");
  root.style.setProperty("--muted", theme.muted || "#616966");
  root.style.setProperty("--subtle", theme.subtle || "#8d9692");
  root.style.setProperty("--line", theme.line);
  root.style.setProperty("--line-strong", theme.lineStrong);
  root.style.setProperty("--accent", theme.accent);
  root.style.setProperty("--accent-2", theme.accent2);
  root.style.setProperty("--accent-soft", theme.accentSoft);
  root.style.setProperty("--top-glow", theme.topGlow);
  root.style.setProperty("--radius", theme.radius || "8px");
  root.style.setProperty("--shadow", theme.shadow);
  root.style.setProperty("--shadow-soft", theme.shadowSoft);
  root.style.setProperty("--panel-alpha", theme.panelAlpha || "0.88");
  root.style.setProperty("--panel-alpha-percent", `${Number(theme.panelAlpha || 0.88) * 100}%`);
}

watch(
  activeTheme,
  (theme) => {
    applyTheme(theme);
  },
  { immediate: true },
);
