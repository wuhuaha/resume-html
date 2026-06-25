<template>
  <div class="theme-switcher" aria-label="主题色切换">
    <button
      v-for="theme in themes"
      :key="theme.key"
      type="button"
      :class="{ active: theme.key === activeKey }"
      :title="`切换到${theme.label}主题`"
      @click="setTheme(theme.key)"
    >
      <span :style="{ background: theme.accent }"></span>
    </button>
  </div>
</template>

<script setup>
import { useTheme } from "../theme";

const { activeKey, themes, setTheme } = useTheme();
</script>
