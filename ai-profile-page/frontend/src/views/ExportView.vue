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
        <p class="muted-copy">把岗位 JD 放进来，系统会按事实资料重排重点，输出适合投递留档的 HTML/PDF 版本。</p>

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
            生成简历
          </n-button>
        </n-form>
        <div v-if="activeModeConfig" class="export-policy-summary">
          <strong>{{ activeModeConfig.label }}</strong>
          <span>{{ activeModeConfig.targetPages ? `${activeModeConfig.targetPages} 页目标` : "不限页数" }}</span>
          <p>{{ activeModeConfig.description }}</p>
        </div>
        <p class="helper-text">{{ note }}</p>
      </div>

      <aside class="preview-panel">
        <div class="preview-toolbar">
          <h2>导出预览</h2>
          <div>
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
import { exportResume, getResumeExportConfig } from "../api";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const jd = ref("");
const direction = ref("语音 AI / 后端系统");
const template = ref("ats");
const mode = ref("one-page");
const exportConfig = ref(null);
const resultHtml = ref("");
const filename = ref("wangtao-resume.html");
const note = ref("后端未配置 LLM Key 时，会使用本地资料生成保守版本。");
const loading = ref(false);

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
    filename.value = result.filename;
    note.value = result.note;
  } catch (error) {
    note.value = `生成失败：${error.message}`;
  } finally {
    loading.value = false;
  }
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
