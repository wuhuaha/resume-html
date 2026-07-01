<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <component :is="currentView" />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { NConfigProvider, NMessageProvider } from "naive-ui";
import AdminAiView from "./views/AdminAiView.vue";
import AdminView from "./views/AdminView.vue";
import ExportView from "./views/ExportView.vue";
import HomeView from "./views/HomeView.vue";
import { activeTheme, loadPublishedStyle } from "./theme";

const routes = {
  "/": HomeView,
  "/resume/export": ExportView,
  "/admin": AdminView,
  "/admin/ai": AdminAiView,
};

const currentView = computed(() => routes[window.location.pathname] || HomeView);

const themeOverrides = computed(() => ({
  common: {
    primaryColor: activeTheme.value.accent,
    primaryColorHover: activeTheme.value.accent2,
    primaryColorPressed: "#141716",
    borderRadius: activeTheme.value.radius,
    fontFamily: 'Inter, "Microsoft YaHei", "PingFang SC", "Noto Sans SC", Arial, sans-serif',
  },
  Button: {
    fontWeight: "800",
    borderRadiusMedium: activeTheme.value.radius,
  },
  Input: {
    borderRadius: activeTheme.value.radius,
  },
  Card: {
    borderRadius: activeTheme.value.radius,
  },
}));

onMounted(async () => {
  try {
    await loadPublishedStyle();
  } catch {
    // The local fallback style is enough when the API is temporarily unavailable.
  }
});
</script>
