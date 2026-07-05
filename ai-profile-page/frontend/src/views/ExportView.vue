<template>
  <main class="page-shell compact">
    <nav class="top-nav">
      <a class="brand" href="/">
        <span class="brand-mark">WT</span>
        <span>AI Profile</span>
      </a>
      <div class="nav-actions">
        <div class="nav-links">
          <a href="/">返回首页</a>
        </div>
        <div class="nav-tools">
          <a
            class="open-source-link"
            href="https://github.com/wuhuaha/resume-html/blob/main/ai-profile-page/docs/DEPLOYMENT.md"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="查看 GitHub 开源项目部署说明"
          >
            <Github :size="16" />
            <span>开源部署</span>
          </a>
          <ThemeSwitcher />
        </div>
      </div>
    </nav>

    <section class="export-layout">
      <div class="workspace-panel">
        <p class="eyebrow">JD 匹配导出</p>
        <h1>选择模板，生成匹配版简历</h1>
        <p class="muted-copy">先生成可编辑 Markdown 草稿，再人工或 AI 微调，最后刷新 HTML/PDF 预览。</p>

        <n-form class="export-form" label-placement="top">
          <n-form-item label="目标岗位方向">
            <n-input v-model:value="direction" size="large" placeholder="例如：语音 AI / 后端系统" />
          </n-form-item>

          <n-form-item label="粘贴岗位 JD">
            <n-input
              v-model:value="jd"
              type="textarea"
              :autosize="{ minRows: 8, maxRows: 14 }"
              placeholder="粘贴招聘 JD，系统会提取重点并生成匹配版简历。"
            />
          </n-form-item>

          <n-form-item label="样式模板">
            <div class="export-option-grid">
              <button
                v-for="item in templates"
                :key="item.key"
                type="button"
                :class="{ active: template === item.key }"
                @click="template = item.key"
              >
                {{ item.label }}
              </button>
            </div>
          </n-form-item>

          <n-form-item label="篇幅模式">
            <div class="export-option-grid">
              <button
                v-for="item in modeOptions"
                :key="item.value"
                type="button"
                :class="{ active: mode === item.value }"
                @click="mode = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </n-form-item>

          <n-button type="primary" size="large" block :loading="loading" @click="generate">
            <template #icon><Download :size="18" /></template>
            生成 Markdown 草稿
          </n-button>
        </n-form>
        <div v-if="activeModeConfig" class="export-policy-summary">
          <strong>{{ activeModeConfig.label }}</strong>
          <span>{{ activeModeConfig.targetPages ? `${activeModeConfig.targetPages} 页目标` : "不限页数" }}</span>
          <p>{{ activeModeConfig.description }}</p>
        </div>
        <p class="helper-text">{{ note }}</p>

        <div class="export-flow-status" :class="{ running: exportBusy, ready: draftMarkdown && !exportBusy }" aria-live="polite">
          <strong>{{ exportStatusTitle }}</strong>
          <span>{{ exportStatusMessage }}</span>
        </div>

        <section class="resume-draft-panel">
          <div class="resume-draft-head">
            <div>
              <p class="eyebrow">可编辑中间稿</p>
              <h2>Markdown 草稿</h2>
            </div>
            <n-button size="small" :disabled="!draftMarkdown" @click="downloadMarkdown">下载 MD</n-button>
          </div>
          <n-input
            v-model:value="draftMarkdown"
            class="resume-draft-editor"
            type="textarea"
            :disabled="!draftMarkdown"
            :autosize="{ minRows: 18, maxRows: 28 }"
            placeholder="点击“生成 Markdown 草稿”后，可在这里人工调整，再刷新右侧预览。"
          />
          <div class="draft-action-row">
            <n-button :disabled="!draftMarkdown" :loading="rendering" @click="refreshPreview">刷新预览</n-button>
            <n-button :disabled="!draftMarkdown" @click="resetDraft">恢复上次生成稿</n-button>
          </div>
          <div class="resume-ai-edit">
            <n-input
              v-model:value="aiInstruction"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 5 }"
              :disabled="!draftMarkdown"
              placeholder="例如：压缩到一页、强化语音 Agent 项目、减少早期经历篇幅。"
            />
            <n-button type="primary" :disabled="!draftMarkdown || !aiInstruction.trim()" :loading="aiEditing" @click="runAiEdit">
              AI 调整草稿
            </n-button>
          </div>
        </section>
      </div>

      <aside class="preview-panel">
        <div class="preview-toolbar">
          <h2>导出预览</h2>
          <div>
            <n-button size="small" :disabled="!draftMarkdown" @click="downloadMarkdown">下载 MD</n-button>
            <n-button size="small" :disabled="!resultHtml" @click="downloadHtml">下载 HTML</n-button>
            <n-button size="small" :disabled="!resultHtml" @click="printPdf">打印 PDF</n-button>
          </div>
        </div>
        <iframe v-if="resultHtml" title="简历预览" :srcdoc="resultHtml"></iframe>
        <div v-else class="empty-state">生成后可预览、下载 HTML，并通过浏览器打印为 PDF。</div>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { NButton, NForm, NFormItem, NInput } from "naive-ui";
import { aiEditResume, exportResume, getResumeExportConfig, renderResume } from "../api";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const jd = ref("");
const direction = ref("语音 AI / 后端系统");
const template = ref("ats");
const mode = ref("one-page");
const exportConfig = ref(null);
const resultHtml = ref("");
const draftMarkdown = ref("");
const generatedMarkdown = ref("");
const filename = ref("wangtao-resume.html");
const note = ref("后端未配置 LLM Key 时，会使用本地资料生成保守版本。");
const loading = ref(false);
const rendering = ref(false);
const aiEditing = ref(false);
const aiInstruction = ref("");

const templates = computed(() => {
  const configured = exportConfig.value?.templates || {};
  return Object.entries(configured).map(([key, item]) => ({
    key,
    label: item.label,
    description: item.description,
  }));
});

const modeOptions = computed(() => {
  const modes = exportConfig.value?.modes || {};
  return Object.entries(modes).map(([value, item]) => ({
    value,
    label: item.label,
  }));
});

const activeModeConfig = computed(() => exportConfig.value?.modes?.[mode.value] || null);
const exportBusy = computed(() => loading.value || rendering.value || aiEditing.value);
const exportStatusTitle = computed(() => {
  if (loading.value) return "正在生成 Markdown 草稿";
  if (aiEditing.value) return "正在 AI 调整 Markdown";
  if (rendering.value) return "正在刷新 HTML/PDF 预览";
  if (draftMarkdown.value) return "Markdown 草稿可编辑";
  return "等待生成草稿";
});
const exportStatusMessage = computed(() => {
  if (loading.value) return "后端会先生成可人工编辑的 Markdown，再同步渲染右侧预览。";
  if (aiEditing.value) return "模型会只修改当前草稿，不会保存到首页或覆盖资料库。";
  if (rendering.value) return "当前只做 Markdown 到 HTML 的本地渲染，不调用模型。";
  if (draftMarkdown.value) return "可以直接手改草稿，或填写说明让 AI 调整，然后刷新预览并导出。";
  return "粘贴 JD 后点击生成，后续 PDF/HTML 都基于这份可编辑草稿导出。";
});

onMounted(async () => {
  try {
    exportConfig.value = await getResumeExportConfig();
    mode.value = exportConfig.value.activeMode || "one-page";
    template.value = exportConfig.value.activeTemplate || templates.value[0]?.key || "ats-classic";
  } catch (error) {
    note.value = `导出策略读取失败，使用默认一页纸策略：${error.message}`;
  }
});

async function generate() {
  loading.value = true;
  try {
    const result = await exportResume({
      jd: jd.value,
      direction: direction.value,
      template: template.value,
      mode: mode.value,
    });
    resultHtml.value = result.html;
    draftMarkdown.value = result.markdown;
    generatedMarkdown.value = result.markdown;
    filename.value = result.filename;
    note.value = result.note;
  } catch (error) {
    note.value = `生成失败：${error.message}`;
  } finally {
    loading.value = false;
  }
}

async function refreshPreview() {
  if (!draftMarkdown.value.trim()) return;
  rendering.value = true;
  try {
    const result = await renderResume({
      markdown: draftMarkdown.value,
      template: template.value,
      mode: mode.value,
    });
    resultHtml.value = result.html;
    draftMarkdown.value = result.markdown;
    filename.value = result.filename;
    note.value = result.note;
  } catch (error) {
    note.value = `预览刷新失败：${error.message}`;
  } finally {
    rendering.value = false;
  }
}

async function runAiEdit() {
  const instruction = aiInstruction.value.trim();
  if (!draftMarkdown.value.trim() || !instruction) return;
  aiEditing.value = true;
  try {
    const result = await aiEditResume({
      markdown: draftMarkdown.value,
      instruction,
      jd: jd.value,
      direction: direction.value,
      template: template.value,
      mode: mode.value,
    });
    draftMarkdown.value = result.markdown;
    note.value = result.note;
    await refreshPreview();
  } catch (error) {
    note.value = `AI 调整失败：${error.message}`;
  } finally {
    aiEditing.value = false;
  }
}

function resetDraft() {
  if (!generatedMarkdown.value) return;
  draftMarkdown.value = generatedMarkdown.value;
  note.value = "已恢复到上次生成的 Markdown 草稿，可刷新预览确认。";
}

function downloadMarkdown() {
  const blob = new Blob([draftMarkdown.value], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.value.replace(/\\.html?$/i, ".md") || "resume.md";
  link.click();
  URL.revokeObjectURL(url);
}

function downloadHtml() {
  const blob = new Blob([resultHtml.value], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.value;
  link.click();
  URL.revokeObjectURL(url);
}

function printPdf() {
  const printWindow = window.open("", "_blank");
  printWindow.document.write(resultHtml.value);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}
</script>
