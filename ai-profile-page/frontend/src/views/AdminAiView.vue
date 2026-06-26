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
        <p class="muted-copy">进入后可通过 DeepSeek 对话修改 Markdown 草稿，并预览首页生成效果。</p>

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
            用对话修改 Markdown 草稿，并用同一套首页生成逻辑预览效果。确认后再保存到正式内容源。
          </p>
        </div>
        <div class="admin-head-actions">
          <span :class="['save-state', dirty ? 'is-dirty' : '']">{{ dirty ? "草稿未保存" : "已同步" }}</span>
          <n-button quaternary @click="logout">退出</n-button>
        </div>
      </header>

      <section class="ai-admin-layout">
        <aside class="workspace-panel ai-chat-panel">
          <div class="admin-section-heading">
            <h2>对话修改</h2>
            <p>AI 只允许基于当前 Markdown 改写、重排和精简，不应新增事实。</p>
          </div>

          <div class="ai-preset-list">
            <button v-for="item in presets" :key="item" type="button" @click="instruction = item">
              {{ item }}
            </button>
          </div>

          <n-input
            v-model:value="instruction"
            type="textarea"
            class="ai-instruction-input"
            placeholder="例如：把核心能力改得更适合语音 AI 岗位，保留事实和量化结果。"
          />

          <div class="ai-command-row">
            <n-button type="primary" :loading="aiLoading" :disabled="!instruction.trim()" @click="runAiEdit">
              <template #icon><Bot :size="18" /></template>
              生成草稿
            </n-button>
            <n-button :loading="previewLoading" @click="previewDraft">
              <template #icon><Eye :size="18" /></template>
              预览首页
            </n-button>
            <n-button type="primary" secondary :loading="saving" @click="saveDraft">
              <template #icon><Save :size="18" /></template>
              保存
            </n-button>
          </div>

          <div class="ai-message-log">
            <article v-for="message in messages" :key="message.id" :class="['ai-message', message.role]">
              {{ message.content }}
            </article>
          </div>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-draft-panel">
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
            default-mode="edit"
            placeholder="当前 Markdown 会显示在这里。"
            @update:modelValue="dirty = true"
          />
        </section>

        <aside class="preview-panel ai-briefing-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">首页预览</p>
              <h2>{{ previewTitle }}</h2>
            </div>
            <n-button size="small" :loading="previewLoading" @click="previewDraft">刷新预览</n-button>
          </div>
          <BriefingPreview :briefing="briefing" />
        </aside>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import { Bot, Eye, Save } from "lucide-vue-next";
import {
  clearStoredAdminPassword,
  getStoredAdminPassword,
  setStoredAdminPassword,
} from "../adminAuth";
import {
  adminLogin,
  aiEditMarkdown,
  getMarkdownDocument,
  previewMarkdownBriefing,
  saveMarkdownDocument,
} from "../api";
import BriefingPreview from "../components/BriefingPreview.vue";
import MarkdownLiteEditor from "../components/MarkdownLiteEditor.vue";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const presets = [
  "把首页首屏表达改得更适合语音 AI 岗位，但不要增加经历。",
  "精简项目描述，保留量化结果和关键技术证据。",
  "把核心能力重新组织成招聘方更容易扫描的结构。",
  "检查内容是否有夸大表达，并改得更保守可信。",
];

const password = ref(getStoredAdminPassword());
const authenticated = ref(false);
const loading = ref(false);
const aiLoading = ref(false);
const previewLoading = ref(false);
const saving = ref(false);
const dirty = ref(false);
const status = ref("");
const statusType = ref("info");
const markdown = ref("");
const documentPath = ref("");
const instruction = ref("");
const briefing = ref(null);
const messages = ref([
  {
    id: 1,
    role: "assistant",
    content: "先选择一个预设，或直接输入你希望如何修改内容。生成结果会进入草稿，不会自动保存。",
  },
]);

const adminPassword = computed(() => getStoredAdminPassword() || password.value);
const displayPath = computed(() => {
  if (!documentPath.value) return "content/profile.md";
  return documentPath.value.split(/[\\/]/).slice(-3).join("/");
});
const previewTitle = computed(() => briefing.value?.hero?.statement || "等待生成预览");

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
    await loadDocument();
    await previewDraft();
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
  briefing.value = null;
  setStatus("");
}

async function loadDocument() {
  const result = await getMarkdownDocument(adminPassword.value);
  markdown.value = result.markdown;
  documentPath.value = result.path;
  dirty.value = false;
}

async function runAiEdit() {
  const content = instruction.value.trim();
  if (!content) return;
  aiLoading.value = true;
  messages.value.push({ id: Date.now(), role: "user", content });
  try {
    const result = await aiEditMarkdown(adminPassword.value, markdown.value, content);
    markdown.value = result.markdown;
    dirty.value = true;
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: result.note });
    setStatus(result.note, result.configured ? "success" : "warning");
    await previewDraft();
  } catch (error) {
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: `修改失败：${error.message}` });
    setStatus(`修改失败：${error.message}`, "error");
  } finally {
    aiLoading.value = false;
  }
}

async function previewDraft() {
  if (!markdown.value.trim()) return;
  previewLoading.value = true;
  try {
    briefing.value = await previewMarkdownBriefing(adminPassword.value, markdown.value);
  } catch (error) {
    setStatus(`预览失败：${error.message}`, "error");
  } finally {
    previewLoading.value = false;
  }
}

async function saveDraft() {
  saving.value = true;
  try {
    const result = await saveMarkdownDocument(adminPassword.value, markdown.value);
    dirty.value = false;
    setStatus(result.message, "success");
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "error");
  } finally {
    saving.value = false;
  }
}
</script>
