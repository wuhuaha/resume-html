<template>
  <div class="markdown-block">
    <template v-for="(line, index) in lines" :key="index">
      <p v-if="line.type === 'p'" v-html="line.html"></p>
      <p v-else-if="line.type === 'li'" class="inline-bullet" v-html="line.html"></p>
      <p v-else-if="line.type === 'ordered'" class="ordered-line">
        <span>{{ line.index }}.</span>
        <span v-html="line.html"></span>
      </p>
      <p v-else-if="line.type === 'meta'" class="meta-line" v-html="line.html"></p>
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
      const ordered = line.match(/^(\d+)[.)]\s+(.+)$/);
      if (ordered) return { type: "ordered", index: ordered[1], html: renderInlineMarkdown(ordered[2]) };
      if (line.startsWith("- ")) return { type: "li", html: renderInlineMarkdown(`• ${line.slice(2)}`) };
      if (line.includes("：") && line.length < 32) return { type: "meta", html: renderInlineMarkdown(line) };
      return { type: "p", html: renderInlineMarkdown(line) };
    }),
);

function renderInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
</script>
