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

          <n-form-item label="导出模板">
            <n-radio-group v-model:value="template" class="template-list">
              <n-radio-button v-for="item in templates" :key="item.value" :value="item.value">
                {{ item.label }}
              </n-radio-button>
            </n-radio-group>
          </n-form-item>

          <n-button type="primary" size="large" block :loading="loading" @click="generate">
            <template #icon><Download :size="18" /></template>
            生成简历
          </n-button>
        </n-form>
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
import { ref } from "vue";
import { NButton, NForm, NFormItem, NInput, NRadioButton, NRadioGroup } from "naive-ui";
import { exportResume } from "../api";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const jd = ref("");
const direction = ref("语音 AI / 后端系统");
const template = ref("ats");
const resultHtml = ref("");
const filename = ref("wangtao-resume.html");
const note = ref("后端未配置 DeepSeek Key 时，会使用本地资料生成保守版本。");
const loading = ref(false);

const templates = [
  { value: "ats", label: "ATS 一页纸" },
  { value: "voice-ai", label: "AI / 语音方向" },
  { value: "backend", label: "后端 / 系统方向" },
];

async function generate() {
  loading.value = true;
  try {
    const result = await exportResume({
      jd: jd.value,
      direction: direction.value,
      template: template.value,
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
