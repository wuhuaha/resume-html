<template>
  <main class="page-shell compact admin-page">
    <nav class="top-nav">
      <a class="brand" href="/">
        <span class="brand-mark">WT</span>
        <span>AI Profile</span>
      </a>
      <div class="nav-actions">
        <a href="/">返回首页</a>
        <ThemeSwitcher />
      </div>
    </nav>

    <section v-if="!authenticated" class="admin-gate">
      <div class="workspace-panel login-panel">
        <p class="eyebrow">作者后台</p>
        <h1>输入修改密码</h1>
        <p class="muted-copy">用于维护页面内容源 Markdown。部署时可通过后端环境变量修改密码，默认值为 admin。</p>

        <form class="login-form" @submit.prevent="login">
          <n-input
            v-model:value="password"
            size="large"
            type="password"
            show-password-on="mousedown"
            placeholder="修改密码"
          />
          <n-button type="primary" size="large" attr-type="submit" :loading="loading">
            进入后台
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
          <h1>内容维护</h1>
          <p class="muted-copy">
            编辑公开页面、AI 问答和简历导出共同使用的资料源。保存后会刷新资料索引。
          </p>
        </div>
        <div class="admin-head-actions">
          <span :class="['save-state', dirty ? 'is-dirty' : '']">{{ dirty ? "有未保存修改" : "已同步" }}</span>
          <n-button quaternary @click="logout">退出</n-button>
        </div>
      </header>

      <section class="admin-layout">
        <aside class="workspace-panel admin-side-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>写</h2>
              <p>保存当前 Markdown，或重新读取内容源。</p>
            </div>

            <div class="button-row">
              <n-button type="primary" size="large" :loading="saving" @click="save">
                <template #icon><Save :size="18" /></template>
                保存
              </n-button>
              <n-button size="large" :loading="loading" @click="loadDocument">
                <template #icon><RefreshCw :size="18" /></template>
                重新加载
              </n-button>
              <n-button size="large" @click="reindex">
                <template #icon><Settings :size="18" /></template>
                重建索引
              </n-button>
            </div>
          </section>

          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>导入</h2>
              <p>从 Word、PDF 或 Markdown 生成草稿，确认后再保存。</p>
            </div>

            <label class="upload-box compact-upload">
              <Upload :size="24" />
              <span>{{ selectedName || "选择文件" }}</span>
              <input type="file" accept=".docx,.pdf,.md,.txt" @change="selectFile" />
            </label>

            <n-button
              block
              secondary
              size="large"
              :disabled="!file"
              :loading="converting"
              @click="convert"
            >
              <template #icon><FileText :size="18" /></template>
              导入到编辑器
            </n-button>
          </section>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <aside class="preview-panel markdown-editor-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">当前文档</p>
              <h2>{{ displayPath }}</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ sectionCount }} 个章节</span>
              <span>{{ markdown.length }} 字符</span>
            </div>
          </div>
          <MarkdownLiteEditor
            v-model="markdown"
            placeholder="这里会显示 content/profile.md 的内容。"
            @update:modelValue="dirty = true"
          />
        </aside>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import { FileText, RefreshCw, Save, Settings, Upload } from "lucide-vue-next";
import MarkdownLiteEditor from "../components/MarkdownLiteEditor.vue";
import {
  adminLogin,
  getMarkdownDocument,
  importDocument,
  reindexContent,
  saveMarkdownDocument,
} from "../api";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const STORAGE_KEY = "ai-profile-admin-password";

const password = ref(sessionStorage.getItem(STORAGE_KEY) || "");
const authenticated = ref(false);
const loading = ref(false);
const saving = ref(false);
const converting = ref(false);
const status = ref("");
const statusType = ref("info");
const markdown = ref("");
const documentPath = ref("");
const sectionCount = ref(0);
const dirty = ref(false);
const file = ref(null);
const selectedName = ref("");

const adminPassword = computed(() => sessionStorage.getItem(STORAGE_KEY) || password.value);
const displayPath = computed(() => {
  if (!documentPath.value) return "content/profile.md";
  return documentPath.value.split(/[\\/]/).slice(-3).join("/");
});

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
    const result = await adminLogin(password.value);
    sessionStorage.setItem(STORAGE_KEY, password.value);
    authenticated.value = true;
    setStatus(result.message, "success");
    await loadDocument();
  } catch (error) {
    sessionStorage.removeItem(STORAGE_KEY);
    authenticated.value = false;
    setStatus(error.message, "error");
  } finally {
    loading.value = false;
  }
}

function logout() {
  sessionStorage.removeItem(STORAGE_KEY);
  password.value = "";
  authenticated.value = false;
  markdown.value = "";
  documentPath.value = "";
  sectionCount.value = 0;
  dirty.value = false;
  setStatus("");
}

async function loadDocument() {
  loading.value = true;
  try {
    const result = await getMarkdownDocument(adminPassword.value);
    markdown.value = result.markdown;
    documentPath.value = result.path;
    sectionCount.value = result.sections;
    dirty.value = false;
    setStatus("Markdown 已加载。", "success");
  } catch (error) {
    setStatus(`加载失败：${error.message}`, "error");
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    const result = await saveMarkdownDocument(adminPassword.value, markdown.value);
    sectionCount.value = result.sections;
    dirty.value = false;
    setStatus(result.message, "success");
  } catch (error) {
    setStatus(`保存失败：${error.message}`, "error");
  } finally {
    saving.value = false;
  }
}

function selectFile(event) {
  file.value = event.target.files?.[0] || null;
  selectedName.value = file.value?.name || "";
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  try {
    const result = await importDocument(adminPassword.value, file.value);
    markdown.value = result.markdown;
    dirty.value = true;
    setStatus(`已转换：${result.filename}。确认无误后点击保存写入内容源。`, "success");
  } catch (error) {
    setStatus(`转换失败：${error.message}`, "error");
  } finally {
    converting.value = false;
  }
}

async function reindex() {
  try {
    const result = await reindexContent(adminPassword.value);
    sectionCount.value = result.sections;
    setStatus(result.message, "success");
  } catch (error) {
    setStatus(`索引失败：${error.message}`, "error");
  }
}
</script>
