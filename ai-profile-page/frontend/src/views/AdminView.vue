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

    <section class="admin-layout">
      <div class="workspace-panel">
        <p class="eyebrow">隐藏作者后台</p>
        <h1>内容导入与索引管理</h1>
        <p class="muted-copy">把 Word/PDF 转成 Markdown 草稿，再人工整理进内容源，避免 AI 基于未确认资料回答。</p>

        <label class="upload-box">
          <Upload :size="28" />
          <span>{{ selectedName || "选择 Word / PDF / Markdown 文件" }}</span>
          <input type="file" accept=".docx,.pdf,.md,.txt" @change="selectFile" />
        </label>

        <div class="button-row">
          <n-button type="primary" size="large" :disabled="!file" :loading="loading" @click="convert">
            <template #icon><FileText :size="18" /></template>
            转换为 Markdown
          </n-button>
          <n-button size="large" @click="reindex">
            <template #icon><Settings :size="18" /></template>
            重建索引
          </n-button>
        </div>
        <n-alert class="admin-alert" type="info" :bordered="false">{{ status }}</n-alert>
      </div>

      <aside class="preview-panel">
        <div class="preview-toolbar">
          <h2>Markdown 草稿</h2>
        </div>
        <n-input
          v-model:value="markdown"
          class="markdown-draft"
          type="textarea"
          placeholder="转换结果会显示在这里。"
        />
      </aside>
    </section>
  </main>
</template>

<script setup>
import { ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import { importDocument, reindexContent } from "../api";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const file = ref(null);
const selectedName = ref("");
const loading = ref(false);
const status = ref("作者后台当前为轻量隐藏入口，后续可增加访问控制。");
const markdown = ref("");

function selectFile(event) {
  file.value = event.target.files?.[0] || null;
  selectedName.value = file.value?.name || "";
}

async function convert() {
  if (!file.value) return;
  loading.value = true;
  try {
    const result = await importDocument(file.value);
    markdown.value = result.markdown;
    status.value = `已转换：${result.filename}`;
  } catch (error) {
    status.value = `转换失败：${error.message}`;
  } finally {
    loading.value = false;
  }
}

async function reindex() {
  try {
    const result = await reindexContent();
    status.value = result.message;
  } catch (error) {
    status.value = `索引失败：${error.message}`;
  }
}
</script>
