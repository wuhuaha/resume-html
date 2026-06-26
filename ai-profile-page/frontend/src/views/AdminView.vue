<template>
  <main class="page-shell compact">
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

    <section v-else class="admin-layout">
      <div class="workspace-panel">
        <div class="admin-heading-row">
          <div>
            <p class="eyebrow">内容源编辑</p>
            <h1>维护 Markdown</h1>
          </div>
          <n-button quaternary @click="logout">退出</n-button>
        </div>
        <p class="muted-copy">
          当前编辑的是公开页面、AI 问答和导出简历共同使用的资料源。保存后会刷新资料索引。
        </p>

        <div class="admin-meta">
          <span>{{ documentPath || "content/profile.md" }}</span>
          <span>{{ sectionCount }} 个章节</span>
          <span>{{ markdown.length }} 字符</span>
        </div>

        <div class="button-row">
          <n-button type="primary" size="large" :loading="saving" @click="save">
            <template #icon><Save :size="18" /></template>
            保存 Markdown
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

        <label class="upload-box">
          <Upload :size="28" />
          <span>{{ selectedName || "选择 Word / PDF / Markdown 文件生成草稿" }}</span>
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
          转换草稿并放入编辑器
        </n-button>

        <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
          {{ status }}
        </n-alert>
      </div>

      <aside class="preview-panel markdown-editor-panel">
        <div class="preview-toolbar">
          <div>
            <p class="eyebrow">Profile Markdown</p>
            <h2>正式内容</h2>
          </div>
          <span :class="['save-state', dirty ? 'is-dirty' : '']">{{ dirty ? "有未保存修改" : "已同步" }}</span>
        </div>
        <n-input
          v-model:value="markdown"
          class="markdown-draft"
          type="textarea"
          placeholder="这里会显示 content/profile.md 的内容。"
          @update:value="dirty = true"
        />
      </aside>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import { FileText, RefreshCw, Save, Settings, Upload } from "lucide-vue-next";
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
