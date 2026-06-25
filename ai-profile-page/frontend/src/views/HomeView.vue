<template>
  <main class="site-shell">
    <nav class="top-nav">
      <a class="brand" href="/">
        <span class="brand-mark">WT</span>
        <span>AI Profile</span>
      </a>
      <div class="nav-actions">
        <a href="#capabilities">{{ page.nav.capabilities }}</a>
        <a href="#timeline">{{ page.nav.timeline }}</a>
        <a href="#projects">{{ page.nav.projects }}</a>
        <a href="/resume/export">{{ page.nav.export }}</a>
        <a class="ghost-link" href="/admin">{{ page.nav.admin }}</a>
        <ThemeSwitcher />
      </div>
    </nav>

    <section class="hero-stage">
      <div class="hero-copy">
        <p class="eyebrow">{{ hero.eyebrow }}</p>
        <h1>{{ hero.headline }}</h1>
        <p class="hero-statement">{{ hero.statement }}</p>
        <p class="hero-title">{{ hero.subtitle }}</p>
        <p class="hero-summary">{{ hero.summary }}</p>

        <div class="metric-strip" aria-label="核心结果">
          <div v-for="item in metrics" :key="item.label">
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </div>
        </div>

        <div class="hero-actions">
          <n-button type="primary" size="large" tag="a" href="#chat">
            <template #icon><Bot :size="18" /></template>
            直接提问
          </n-button>
          <n-button size="large" tag="a" href="/resume/export">
            <template #icon><Download :size="18" /></template>
            {{ page.nav.export }}
          </n-button>
        </div>

        <div class="contact-row">
          <span v-if="meta.phone"><Phone :size="16" />{{ meta.phone }}</span>
          <span v-if="meta.email"><Mail :size="16" />{{ meta.email }}</span>
          <span v-if="meta.location"><MapPin :size="16" />{{ meta.location }}</span>
        </div>
      </div>

      <aside class="hero-side">
        <section id="chat" class="assistant-workbench" aria-label="AI 职业经历讲解员">
          <div class="workbench-topline">
            <div>
              <p class="eyebrow">{{ page.assistant.eyebrow }}</p>
              <h2>{{ page.assistant.title }}</h2>
            </div>
            <n-tag round :type="briefing?.aiConfigured ? 'success' : 'default'">
              {{ statusLabel }}
            </n-tag>
          </div>
          <p class="assistant-context">{{ page.assistant.context }}</p>

          <div class="assistant-quick">
            <button v-for="question in presets" :key="question" type="button" @click="ask(question)">
              {{ question }}
            </button>
          </div>

          <n-scrollbar class="chat-log compact-log">
            <article v-for="message in messages" :key="message.id" :class="['chat-message', message.role]">
              <p>{{ message.content }}</p>
            </article>
          </n-scrollbar>

          <form class="chat-input refined hero-query" @submit.prevent="ask(input)">
            <n-button circle secondary type="primary" :class="{ active: listening }" title="语音输入" @click="toggleVoice">
              <Mic v-if="!listening" :size="20" />
              <MicOff v-else :size="20" />
            </n-button>
            <n-input v-model:value="input" size="large" :placeholder="page.assistant.placeholder" />
            <n-button circle type="primary" :loading="loading" :disabled="!input.trim()" attr-type="submit" title="发送">
              <template #icon><Send :size="18" /></template>
            </n-button>
          </form>
          <p class="helper-text">{{ voiceHint }}</p>
        </section>
      </aside>
    </section>

    <section class="fit-panel" aria-label="岗位匹配信号">
      <div class="fit-panel-head">
        <p class="eyebrow">Fit signals</p>
        <span>{{ briefing?.generated ? "由 LLM 分析 Markdown 生成" : "本地资料解析" }}</span>
      </div>
      <div class="fit-grid">
        <article v-for="item in fitSignals" :key="item.label" class="fit-row">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.detail }}</p>
        </article>
      </div>
    </section>

    <section id="capabilities" class="capability-section">
      <div class="section-kicker">
        <div>
          <p class="eyebrow">{{ page.sections.capabilities.eyebrow }}</p>
          <h2>{{ page.sections.capabilities.title }}</h2>
        </div>
        <p>{{ page.sections.capabilities.intro }}</p>
      </div>
      <div class="capability-grid">
        <article v-for="(item, index) in capabilities" :key="item.title" class="capability-card">
          <span class="card-index">{{ String(index + 1).padStart(2, "0") }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.body }}</p>
          <small v-if="item.evidence">{{ item.evidence }}</small>
        </article>
      </div>
    </section>

    <section class="evidence-section">
      <div class="section-kicker">
        <div>
          <p class="eyebrow">{{ page.sections.evidence.eyebrow }}</p>
          <h2>{{ page.sections.evidence.title }}</h2>
        </div>
        <p>{{ page.sections.evidence.intro }}</p>
      </div>

      <div class="evidence-layout">
        <section id="timeline" class="timeline-panel">
          <div class="section-title compact-title">
            <h2>{{ page.sections.timeline.title }}</h2>
            <p>{{ page.sections.timeline.intro }}</p>
          </div>
          <div class="timeline">
            <article v-for="item in timeline" :key="item.title" class="timeline-item">
              <div class="timeline-dot"></div>
              <h3>{{ item.title }}</h3>
              <p v-if="item.focus" class="focus-line">{{ item.focus }}</p>
              <MarkdownBlock :text="item.body" />
            </article>
          </div>
        </section>

        <section id="projects" class="project-panel">
          <div class="section-title compact-title">
            <h2>{{ page.sections.projects.title }}</h2>
            <p>{{ page.sections.projects.intro }}</p>
          </div>
          <div class="project-list">
            <article v-for="item in projects" :key="item.title" class="project-card">
              <div class="project-card-top">
                <Github :size="18" />
                <h3>{{ item.title }}</h3>
              </div>
              <p v-if="item.focus" class="focus-line">{{ item.focus }}</p>
              <MarkdownBlock :text="item.body" />
            </article>
          </div>
        </section>
      </div>
    </section>

    <section class="export-cta">
      <div>
        <p class="eyebrow">{{ page.sections.export.eyebrow }}</p>
        <h2>{{ page.sections.export.title }}</h2>
        <p>{{ page.sections.export.intro }}</p>
      </div>
      <n-button type="primary" size="large" tag="a" href="/resume/export">
        <template #icon><Download :size="18" /></template>
        {{ page.sections.export.button }}
      </n-button>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NButton, NInput, NScrollbar, NTag } from "naive-ui";
import { askProfile, getBriefing } from "../api";
import MarkdownBlock from "../components/MarkdownBlock.vue";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const briefing = ref(null);
const input = ref("");
const loading = ref(false);
const listening = ref(false);
const voiceHint = ref("语音输入为辅助入口；浏览器不支持时可直接使用文字。");
const messages = ref([]);

const fallbackPage = {
  nav: {
    capabilities: "能力地图",
    timeline: "经历证据",
    projects: "项目",
    export: "导出简历",
    admin: "作者后台",
  },
  assistant: {
    eyebrow: "AI Q&A",
    title: "问简历，不问套路",
    context: "页面由后端读取 Markdown 资料后生成；问答会约束在简历、项目详情和代码仓摘要内。",
    placeholder: "问一句：他为什么适合语音 AI / 后端系统岗位？",
    voiceHint: "语音输入为辅助入口；浏览器不支持时可直接使用文字。",
  },
  sections: {
    capabilities: {
      eyebrow: "Capability map",
      title: "招聘方最需要先判断的能力面",
      intro: "把技能栈重新组织为岗位评估维度：语音链路、AI 工程、系统能力和真实交付。",
    },
    evidence: {
      eyebrow: "Evidence trail",
      title: "经历与项目证据",
      intro: "用时间线和代表项目交叉验证职责、成果和工程可信度。",
    },
    timeline: {
      title: "经历时间线",
      intro: "按阶段展示职责边界、关键结果和技术深度。",
    },
    projects: {
      title: "代表项目",
      intro: "AI 问答会优先引用这些可核查资料，避免脱离事实包装。",
    },
    export: {
      eyebrow: "Resume export",
      title: "需要投递版简历时，再按 JD 生成",
      intro: "导出模块会基于同一份事实资料调整重点、排序和表达，但不会新增资料中没有的经历。",
      button: "选择模板导出",
    },
  },
};

const fallbackHero = {
  eyebrow: "AI career briefing for recruiters",
  headline: "王涛",
  statement: "把语音 AI、Agent 编排和后端系统落到真实产品里的工程师。",
  subtitle: "高级语音开发工程师",
  summary: "面向招聘方的个人能力介绍页。",
};

const page = computed(() => briefing.value?.page || fallbackPage);
const meta = computed(() => briefing.value?.meta || {});
const hero = computed(() => briefing.value?.hero || fallbackHero);
const fitSignals = computed(() => briefing.value?.fitSignals || []);
const metrics = computed(() => briefing.value?.metrics || []);
const capabilities = computed(() => briefing.value?.capabilities || []);
const timeline = computed(() => briefing.value?.timeline || []);
const projects = computed(() => briefing.value?.projects || []);
const presets = computed(() => briefing.value?.suggestedQuestions || []);
const statusLabel = computed(() => {
  if (briefing.value?.generated) return "LLM 已生成页面";
  if (briefing.value?.aiConfigured) return "DeepSeek 已连接";
  return "本地兜底模式";
});

onMounted(async () => {
  try {
    briefing.value = await getBriefing();
    voiceHint.value = page.value.assistant.voiceHint;
  } catch (error) {
    messages.value.push({
      id: Date.now(),
      role: "assistant",
      content: `暂时无法读取 briefing 接口：${error.message}`,
    });
  }

  messages.value.unshift({
    id: 1,
    role: "assistant",
    content: `你好，我已根据 ${meta.value.name || "候选人"} 的 Markdown 资料整理了这页内容。你可以问我岗位匹配、项目证据或技术深度。`,
  });
});

async function ask(question) {
  const content = question.trim();
  if (!content || loading.value) return;
  input.value = "";
  messages.value.push({ id: Date.now(), role: "user", content });
  loading.value = true;
  try {
    const result = await askProfile(content, messages.value);
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: result.answer });
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      role: "assistant",
      content: `暂时无法连接后端服务：${error.message}`,
    });
  } finally {
    loading.value = false;
  }
}

function toggleVoice() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceHint.value = "当前浏览器不支持语音识别，请使用文字输入。";
    return;
  }
  const recognition = new Recognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  listening.value = true;
  voiceHint.value = "正在听取语音问题...";
  recognition.onresult = (event) => {
    input.value = event.results[0][0].transcript;
    voiceHint.value = "已识别语音，可编辑后发送。";
  };
  recognition.onerror = () => {
    voiceHint.value = "语音识别未成功，请改用文字输入。";
  };
  recognition.onend = () => {
    listening.value = false;
  };
  recognition.start();
}
</script>
