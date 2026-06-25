import { computed, ref, watch } from "vue";

const STORAGE_KEY = "ai-profile-theme";

export const themes = [
  {
    key: "jade",
    label: "墨绿",
    accent: "#126d64",
    accent2: "#1d4f91",
    accentSoft: "#e7f3f0",
    topGlow: "rgba(231, 243, 240, 0.68)",
    bg: "#f6f7f5",
    surfaceSoft: "#f1f4f2",
    line: "#dce3df",
    lineStrong: "#c7d0cb",
  },
  {
    key: "indigo",
    label: "靛蓝",
    accent: "#315fbc",
    accent2: "#0f766e",
    accentSoft: "#e9effb",
    topGlow: "rgba(232, 239, 253, 0.78)",
    bg: "#f7f8fb",
    surfaceSoft: "#f0f3fa",
    line: "#dbe2ef",
    lineStrong: "#c4cedd",
  },
  {
    key: "graphite",
    label: "石墨",
    accent: "#4f5b56",
    accent2: "#255e73",
    accentSoft: "#ecefed",
    topGlow: "rgba(236, 239, 237, 0.78)",
    bg: "#f7f7f4",
    surfaceSoft: "#efefeb",
    line: "#deded8",
    lineStrong: "#c9cac3",
  },
  {
    key: "claret",
    label: "勃艮第",
    accent: "#8a3345",
    accent2: "#315f78",
    accentSoft: "#f5eaed",
    topGlow: "rgba(247, 232, 236, 0.72)",
    bg: "#f8f6f4",
    surfaceSoft: "#f3eeec",
    line: "#e4d9d8",
    lineStrong: "#cfbfbd",
  },
];

const fallbackTheme = themes[0];
const initialKey = localStorage.getItem(STORAGE_KEY);
const activeKey = ref(themes.some((theme) => theme.key === initialKey) ? initialKey : fallbackTheme.key);

export const activeTheme = computed(() => themes.find((theme) => theme.key === activeKey.value) || fallbackTheme);

export function setTheme(key) {
  if (themes.some((theme) => theme.key === key)) {
    activeKey.value = key;
  }
}

export function useTheme() {
  return {
    activeKey,
    activeTheme,
    themes,
    setTheme,
  };
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.dataset.theme = theme.key;
  root.style.setProperty("--bg", theme.bg);
  root.style.setProperty("--surface-soft", theme.surfaceSoft);
  root.style.setProperty("--line", theme.line);
  root.style.setProperty("--line-strong", theme.lineStrong);
  root.style.setProperty("--accent", theme.accent);
  root.style.setProperty("--accent-2", theme.accent2);
  root.style.setProperty("--accent-soft", theme.accentSoft);
  root.style.setProperty("--top-glow", theme.topGlow);
}

watch(
  activeTheme,
  (theme) => {
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme.key);
  },
  { immediate: true },
);
