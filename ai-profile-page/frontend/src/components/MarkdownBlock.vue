<template>
  <div class="markdown-block">
    <template v-for="(line, index) in lines" :key="index">
      <p v-if="line.type === 'p'">{{ line.text }}</p>
      <p v-else-if="line.type === 'li'" class="inline-bullet">• {{ line.text }}</p>
      <p v-else-if="line.type === 'meta'" class="meta-line">{{ line.text }}</p>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  text: {
    type: String,
    default: "",
  },
});

const lines = computed(() =>
  props.text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      if (line.startsWith("- ")) return { type: "li", text: line.slice(2) };
      if (line.includes("：") && line.length < 32) return { type: "meta", text: line };
      return { type: "p", text: line };
    }),
);
</script>

