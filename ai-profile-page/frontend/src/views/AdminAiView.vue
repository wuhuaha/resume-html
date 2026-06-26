<template>
  <main class="page-shell compact admin-page admin-ai-page">
    <nav class="top-nav">
      <a class="brand" href="/">
        <span class="brand-mark">WT</span>
        <span>AI Profile</span>
      </a>
      <div class="nav-actions">
        <a href="/admin">手动编辑</a>
        <a href="/">返回首页</a>
        <ThemeSwitcher />
      </div>
    </nav>

    <section v-if="!authenticated" class="admin-gate">
      <div class="workspace-panel login-panel">
        <p class="eyebrow">AI 内容助手</p>
        <h1>输入修改密码</h1>
        <p class="muted-copy">进入后可分别维护资料 Markdown 和首页展示编排。</p>

        <form class="login-form" @submit.prevent="login">
          <n-input
            v-model:value="password"
            size="large"
            type="password"
            show-password-on="mousedown"
            placeholder="修改密码"
          />
          <n-button type="primary" size="large" attr-type="submit" :loading="loading">
            进入 AI 助手
          </n-button>
        </form>

        <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
          {{ status }}
        </n-alert>
      </div>
    </section>

    <template v-else>
      <header class="admin-page-head">
        <div>
          <p class="eyebrow">作者后台</p>
          <h1>AI 内容助手</h1>
          <p class="muted-copy">
            资料修改负责事实 Markdown；首页编排负责展示文案、排序和预设问题。两者独立保存。
          </p>
        </div>
        <div class="admin-head-actions">
          <span :class="['save-state', activeDirty ? 'is-dirty' : '']">{{ activeDirty ? "有未保存修改" : "已同步" }}</span>
          <n-button quaternary @click="logout">退出</n-button>
        </div>
      </header>

      <div class="admin-mode-tabs">
        <button type="button" :class="{ active: mode === 'markdown' }" @click="mode = 'markdown'">
          <FileText :size="17" />
          <span>资料修改</span>
        </button>
        <button type="button" :class="{ active: mode === 'home' }" @click="mode = 'home'">
          <LayoutTemplate :size="17" />
          <span>首页编排</span>
        </button>
      </div>

      <section v-if="mode === 'markdown'" class="ai-two-column">
        <aside class="workspace-panel ai-command-panel">
          <div class="admin-section-heading">
            <h2>修改 Markdown</h2>
            <p>这里改的是事实资料层，保存后会影响首页、问答和简历导出。</p>
          </div>

          <div class="ai-preset-list">
            <button v-for="item in markdownPresets" :key="item" type="button" @click="markdownInstruction = item">
              {{ item }}
            </button>
          </div>

          <n-input
            v-model:value="markdownInstruction"
            type="textarea"
            class="ai-instruction-input"
            placeholder="例如：精简项目描述，保留量化结果和关键技术证据。"
          />

          <div class="ai-command-row">
            <n-button type="primary" :loading="markdownAiLoading" :disabled="!markdownInstruction.trim()" @click="runMarkdownEdit">
              <template #icon><Bot :size="18" /></template>
              生成资料草稿
            </n-button>
            <n-button type="primary" secondary :loading="markdownSaving" @click="saveMarkdownDraft">
              <template #icon><Save :size="18" /></template>
              保存 Markdown
            </n-button>
          </div>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-main-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">Markdown 草稿</p>
              <h2>{{ displayPath }}</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ markdown.length }} 字符</span>
            </div>
          </div>
          <MarkdownLiteEditor
            v-model="markdown"
            default-mode="split"
            placeholder="当前 Markdown 会显示在这里。"
            @update:modelValue="markdownDirty = true"
          />
        </section>
      </section>

      <section v-else class="ai-two-column home-compose-layout">
        <aside class="workspace-panel ai-command-panel">
          <div class="admin-section-heading">
            <h2>调整首页</h2>
            <p>这里改的是展示编排层，不会修改 Markdown 事实资料。</p>
          </div>

          <div class="ai-preset-list">
            <button v-for="item in homePresets" :key="item" type="button" @click="homeInstruction = item">
              {{ item }}
            </button>
          </div>

          <n-input
            v-model:value="homeInstruction"
            type="textarea"
            class="ai-instruction-input"
            placeholder="例如：首页更突出语音 AI 和后端系统，语气专业克制。"
          />

          <div class="ai-command-row">
            <n-button type="primary" :loading="homeAiLoading" :disabled="!homeInstruction.trim()" @click="runHomeEdit">
              <template #icon><Bot :size="18" /></template>
              生成首页草稿
            </n-button>
            <n-button :loading="homeLoading" @click="loadHomeBriefing">
              <template #icon><RefreshCw :size="18" /></template>
              重新加载
            </n-button>
            <n-button type="primary" secondary :loading="homeSaving" @click="saveHomeDraft">
              <template #icon><Save :size="18" /></template>
              保存首页
            </n-button>
          </div>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-main-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">{{ homeSaved ? "已发布首页编排" : "首页编排草稿" }}</p>
              <h2>{{ previewTitle }}</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ homeBriefing?.generated ? "LLM 生成" : "本地解析" }}</span>
            </div>
          </div>
          <BriefingPreview :briefing="homeBriefing" variant="wide" />
        </section>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import { Bot, FileText, LayoutTemplate, RefreshCw, Save } from "lucide-vue-next";
import {
  clearStoredAdminPassword,
  getStoredAdminPassword,
  setStoredAdminPassword,
} from "../adminAuth";
import {
  adminLogin,
  aiEditHomeBriefing,
  aiEditMarkdown,
  getHomeBriefingDraft,
  getMarkdownDocument,
  saveHomeBriefing,
  saveMarkdownDocument,
} from "../api";
import BriefingPreview from "../components/BriefingPreview.vue";
import MarkdownLiteEditor from "../components/MarkdownLiteEditor.vue";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const markdownPresets = [
  "精简项目描述，保留量化结果和关键技术证据。",
  "把核心能力重新组织成招聘方更容易扫描的结构。",
  "检查内容是否有夸大表达，并改得更保守可信。",
];

const homePresets = [
  "首页首屏更突出语音 AI 和后端系统，语气专业克制。",
  "调整首页内容排序，让招聘方先看到岗位匹配证据。",
  "优化预设问题，让面试官更容易点击提问。",
  "把首页文案改得更简洁大方，不要营销腔。",
];

const mode = ref("markdown");
const password = ref(getStoredAdminPassword());
const authenticated = ref(false);
const loading = ref(false);
const status = ref("");
const statusType = ref("info");

const markdown = ref("");
const documentPath = ref("");
const markdownInstruction = ref("");
const markdownDirty = ref(false);
const markdownAiLoading = ref(false);
const markdownSaving = ref(false);

const homeBriefing = ref(null);
const homeInstruction = ref("");
const homeDirty = ref(false);
const homeSaved = ref(false);
const homeLoading = ref(false);
const homeAiLoading = ref(false);
const homeSaving = ref(false);

const adminPassword = computed(() => getStoredAdminPassword() || password.value);
const displayPath = computed(() => {
  if (!documentPath.value) return "content/profile.md";
  return documentPath.value.split(/[\\/]/).slice(-3).join("/");
});
const previewTitle = computed(() => homeBriefing.value?.hero?.statement || "等待生成首页编排");
const activeDirty = computed(() => (mode.value === "markdown" ? markdownDirty.value : homeDirty.value));

onMounted(async () => {
  if (password.value) {
    await login();
  }
});

function setStatus(message, type = "info") {
  status.value = message;
  statusType.value = type;
}

async function login() {
  if (!password.value.trim()) {
    setStatus("请输入修改密码。", "warning");
    return;
  }
  loading.value = true;
  try {
    await adminLogin(password.value);
    setStoredAdminPassword(password.value);
    authenticated.value = true;
    await Promise.all([loadMarkdown(), loadHomeBriefing()]);
    setStatus("AI 内容助手已就绪。", "success");
  } catch (error) {
    clearStoredAdminPassword();
    authenticated.value = false;
    setStatus(error.message, "error");
  } finally {
    loading.value = false;
  }
}

function logout() {
  clearStoredAdminPassword();
  password.value = "";
  authenticated.value = false;
  markdown.value = "";
  homeBriefing.value = null;
  setStatus("");
}

async function loadMarkdown() {
  const result = await getMarkdownDocument(adminPassword.value);
  markdown.value = result.markdown;
  documentPath.value = result.path;
  markdownDirty.value = false;
}

async function runMarkdownEdit() {
  const content = markdownInstruction.value.trim();
  if (!content) return;
  markdownAiLoading.value = true;
  try {
    const result = await aiEditMarkdown(adminPassword.value, markdown.value, content);
    markdown.value = result.markdown;
    markdownDirty.value = true;
    setStatus(result.note, result.configured ? "success" : "warning");
  } catch (error) {
    setStatus(`资料修改失败：${error.message}`, "error");
  } finally {
    markdownAiLoading.value = false;
  }
}

async function saveMarkdownDraft() {
  markdownSaving.value = true;
  try {
    const result = await saveMarkdownDocument(adminPassword.value, markdown.value);
    markdownDirty.value = false;
    await loadHomeBriefing();
    setStatus(result.message, "success");
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "error");
  } finally {
    markdownSaving.value = false;
  }
}

async function loadHomeBriefing() {
  homeLoading.value = true;
  try {
    const result = await getHomeBriefingDraft(adminPassword.value);
    homeBriefing.value = result.briefing;
    homeSaved.value = result.saved;
    homeDirty.value = false;
  } catch (error) {
    setStatus(`首页编排加载失败：${error.message}`, "error");
  } finally {
    homeLoading.value = false;
  }
}

async function runHomeEdit() {
  const content = homeInstruction.value.trim();
  if (!content || !homeBriefing.value) return;
  homeAiLoading.value = true;
  try {
    const result = await aiEditHomeBriefing(adminPassword.value, homeBriefing.value, content);
    homeBriefing.value = result.briefing;
    homeSaved.value = result.saved;
    homeDirty.value = true;
    setStatus(result.aiConfigured ? "已生成首页编排草稿。" : "后端未配置 DeepSeek API Key。", result.aiConfigured ? "success" : "warning");
  } catch (error) {
    setStatus(`首页编排失败：${error.message}`, "error");
  } finally {
    homeAiLoading.value = false;
  }
}

async function saveHomeDraft() {
  if (!homeBriefing.value) return;
  homeSaving.value = true;
  try {
    const result = await saveHomeBriefing(adminPassword.value, homeBriefing.value);
    homeBriefing.value = result.briefing;
    homeSaved.value = result.saved;
    homeDirty.value = false;
    setStatus("首页编排已保存，公开首页将使用该版本。", "success");
  } catch (error) {
    setStatus(`首页保存失败：${error.message}`, "error");
  } finally {
    homeSaving.value = false;
  }
}
</script>
