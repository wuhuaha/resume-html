<template>
  <div class="briefing-preview">
    <section class="brief-preview-hero">
      <p class="eyebrow">{{ page.hero.eyebrow }}</p>
      <h2>{{ page.hero.headline }}</h2>
      <p class="brief-preview-statement">{{ page.hero.statement }}</p>
      <p class="brief-preview-muted">{{ page.hero.subtitle }}</p>
      <p>{{ page.hero.summary }}</p>
    </section>

    <section class="brief-preview-grid">
      <article v-for="item in page.metrics" :key="item.label">
        <strong>{{ item.value }}</strong>
        <span>{{ item.label }}</span>
      </article>
    </section>

    <section class="brief-preview-section">
      <p class="eyebrow">{{ page.page.sections.capabilities.eyebrow }}</p>
      <h3>{{ page.page.sections.capabilities.title }}</h3>
      <p>{{ page.page.sections.capabilities.intro }}</p>
      <ul>
        <li v-for="item in page.capabilities.slice(0, 4)" :key="item.title">
          <strong>{{ item.title }}</strong>
          <span>{{ item.body }}</span>
        </li>
      </ul>
    </section>

    <section class="brief-preview-section">
      <p class="eyebrow">{{ page.page.sections.timeline.title }}</p>
      <article v-for="item in page.timeline.slice(0, 3)" :key="item.title" class="brief-preview-item">
        <h4>{{ item.title }}</h4>
        <p>{{ item.focus }}</p>
      </article>
    </section>

    <section class="brief-preview-section">
      <p class="eyebrow">预设问题</p>
      <div class="brief-preview-questions">
        <span v-for="question in page.suggestedQuestions" :key="question">{{ question }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  briefing: {
    type: Object,
    default: null,
  },
});

const fallback = {
  page: {
    sections: {
      capabilities: { eyebrow: "Capability", title: "能力预览", intro: "生成预览后显示首页结构。" },
      timeline: { title: "经历时间线" },
    },
  },
  hero: {
    eyebrow: "Preview",
    headline: "首页预览",
    statement: "等待生成",
    subtitle: "",
    summary: "用当前 Markdown 草稿生成首页结构化预览。",
  },
  metrics: [],
  capabilities: [],
  timeline: [],
  suggestedQuestions: [],
};

const page = computed(() => props.briefing || fallback);
</script>
