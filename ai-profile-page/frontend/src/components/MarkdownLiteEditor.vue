<template>
  <div class="md-lite-editor">
    <div class="md-lite-toolbar">
      <div class="md-lite-tools" aria-label="Markdown 工具栏">
        <button type="button" title="二级标题" @click="prefixLine('## ')">
          <Heading2 :size="16" />
        </button>
        <button type="button" title="三级标题" @click="prefixLine('### ')">
          <Heading3 :size="16" />
        </button>
        <button type="button" title="加粗" @click="wrapSelection('**', '**', '重点内容')">
          <Bold :size="16" />
        </button>
        <button type="button" title="无序列表" @click="toggleList">
          <List :size="16" />
        </button>
        <button type="button" title="引用" @click="prefixLine('> ')">
          <Quote :size="16" />
        </button>
        <button type="button" title="链接" @click="wrapSelection('[', '](https://)', '链接文本')">
          <Link :size="16" />
        </button>
        <button type="button" title="代码块" @click="wrapSelection('```\n', '\n```', 'code')">
          <Code2 :size="16" />
        </button>
        <button type="button" title="分隔线" @click="insertAtCursor('\n---\n')">
          <Minus :size="16" />
        </button>
      </div>

      <div class="md-lite-modes" aria-label="编辑模式">
        <button type="button" :class="{ active: mode === 'edit' }" title="编辑" @click="mode = 'edit'">
          <Pencil :size="15" />
          <span>编辑</span>
        </button>
        <button type="button" :class="{ active: mode === 'split' }" title="分屏" @click="mode = 'split'">
          <Columns2 :size="15" />
          <span>分屏</span>
        </button>
        <button type="button" :class="{ active: mode === 'preview' }" title="预览" @click="mode = 'preview'">
          <Eye :size="15" />
          <span>预览</span>
        </button>
      </div>
    </div>

    <div :class="['md-lite-body', `mode-${mode}`]">
      <textarea
        v-if="mode !== 'preview'"
        ref="textareaRef"
        class="md-lite-textarea"
        :value="modelValue"
        :placeholder="placeholder"
        spellcheck="false"
        @input="updateValue"
        @keydown="handleKeydown"
      />

      <div v-if="mode !== 'edit'" class="md-lite-preview">
        <template v-if="blocks.length">
          <template v-for="(block, index) in blocks" :key="index">
            <h1 v-if="block.type === 'h1'" v-html="inlineHtml(block.text)" />
            <h2 v-else-if="block.type === 'h2'" v-html="inlineHtml(block.text)" />
            <h3 v-else-if="block.type === 'h3'" v-html="inlineHtml(block.text)" />
            <hr v-else-if="block.type === 'hr'" />
            <pre v-else-if="block.type === 'code'"><code>{{ block.text }}</code></pre>
            <blockquote v-else-if="block.type === 'quote'">
              <p v-for="(item, itemIndex) in block.items" :key="itemIndex" v-html="inlineHtml(item)" />
            </blockquote>
            <ul v-else-if="block.type === 'ul'">
              <li v-for="(item, itemIndex) in block.items" :key="itemIndex" v-html="inlineHtml(item)" />
            </ul>
            <ol v-else-if="block.type === 'ol'">
              <li v-for="(item, itemIndex) in block.items" :key="itemIndex" v-html="inlineHtml(item)" />
            </ol>
            <table v-else-if="block.type === 'table'">
              <thead>
                <tr>
                  <th v-for="(cell, cellIndex) in block.header" :key="cellIndex" v-html="inlineHtml(cell)" />
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in block.rows" :key="rowIndex">
                  <td v-for="(cell, cellIndex) in row" :key="cellIndex" v-html="inlineHtml(cell)" />
                </tr>
              </tbody>
            </table>
            <p v-else v-html="inlineHtml(block.text)" />
          </template>
        </template>
        <p v-else class="md-lite-empty">Markdown 预览会显示在这里。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from "vue";
import {
  Bold,
  Code2,
  Columns2,
  Eye,
  Heading2,
  Heading3,
  Link,
  List,
  Minus,
  Pencil,
  Quote,
} from "lucide-vue-next";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  placeholder: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:modelValue"]);

const mode = ref("split");
const textareaRef = ref(null);

const blocks = computed(() => parseMarkdown(props.modelValue));

function updateValue(event) {
  emit("update:modelValue", event.target.value);
}

async function ensureTextarea() {
  if (mode.value === "preview") {
    mode.value = "split";
    await nextTick();
  }
  await nextTick();
  textareaRef.value?.focus();
  return textareaRef.value;
}

async function insertAtCursor(text) {
  const textarea = await ensureTextarea();
  if (!textarea) return;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const nextValue = props.modelValue.slice(0, start) + text + props.modelValue.slice(end);
  emit("update:modelValue", nextValue);
  await nextTick();
  textarea.focus();
  textarea.setSelectionRange(start + text.length, start + text.length);
}

async function wrapSelection(before, after, fallback) {
  const textarea = await ensureTextarea();
  if (!textarea) return;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = props.modelValue.slice(start, end) || fallback;
  const nextValue = props.modelValue.slice(0, start) + before + selected + after + props.modelValue.slice(end);
  emit("update:modelValue", nextValue);
  await nextTick();
  textarea.focus();
  textarea.setSelectionRange(start + before.length, start + before.length + selected.length);
}

async function prefixLine(prefix) {
  const textarea = await ensureTextarea();
  if (!textarea) return;
  const start = textarea.selectionStart;
  const lineStart = props.modelValue.lastIndexOf("\n", Math.max(start - 1, 0)) + 1;
  const nextValue = props.modelValue.slice(0, lineStart) + prefix + props.modelValue.slice(lineStart);
  emit("update:modelValue", nextValue);
  await nextTick();
  textarea.focus();
  textarea.setSelectionRange(start + prefix.length, start + prefix.length);
}

async function toggleList() {
  const textarea = await ensureTextarea();
  if (!textarea) return;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = props.modelValue.slice(start, end);

  if (!selected.includes("\n")) {
    await prefixLine("- ");
    return;
  }

  const nextSelected = selected
    .split("\n")
    .map((line) => (line.trim() ? `- ${line.replace(/^[-*+]\s+/, "")}` : line))
    .join("\n");
  const nextValue = props.modelValue.slice(0, start) + nextSelected + props.modelValue.slice(end);
  emit("update:modelValue", nextValue);
  await nextTick();
  textarea.focus();
  textarea.setSelectionRange(start, start + nextSelected.length);
}

function handleKeydown(event) {
  if (event.key === "Tab") {
    event.preventDefault();
    insertAtCursor("  ");
  }

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
    event.preventDefault();
    wrapSelection("**", "**", "重点内容");
  }
}

function parseMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const parsed = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trimEnd();
    const clean = line.trim();

    if (!clean) {
      index += 1;
      continue;
    }

    if (clean.startsWith("```")) {
      const codeLines = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }
      parsed.push({ type: "code", text: codeLines.join("\n") || " " });
      index += 1;
      continue;
    }

    const heading = clean.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      parsed.push({ type: `h${heading[1].length}`, text: heading[2] });
      index += 1;
      continue;
    }

    if (/^(-{3,}|\*{3,})$/.test(clean)) {
      parsed.push({ type: "hr" });
      index += 1;
      continue;
    }

    if (isTableStart(lines, index)) {
      const table = parseTable(lines, index);
      parsed.push(table.block);
      index = table.nextIndex;
      continue;
    }

    if (/^>\s?/.test(clean)) {
      const items = [];
      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^>\s?/, ""));
        index += 1;
      }
      parsed.push({ type: "quote", items });
      continue;
    }

    if (/^[-*+]\s+/.test(clean)) {
      const items = [];
      while (index < lines.length && /^[-*+]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*+]\s+/, ""));
        index += 1;
      }
      parsed.push({ type: "ul", items });
      continue;
    }

    if (/^\d+\.\s+/.test(clean)) {
      const items = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s+/, ""));
        index += 1;
      }
      parsed.push({ type: "ol", items });
      continue;
    }

    const paragraph = [clean];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines, index)) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    parsed.push({ type: "p", text: paragraph.join(" ") });
  }

  return parsed;
}

function isBlockStart(lines, index) {
  const clean = lines[index].trim();
  return (
    clean.startsWith("```") ||
    /^(#{1,3})\s+/.test(clean) ||
    /^(-{3,}|\*{3,})$/.test(clean) ||
    /^>\s?/.test(clean) ||
    /^[-*+]\s+/.test(clean) ||
    /^\d+\.\s+/.test(clean) ||
    isTableStart(lines, index)
  );
}

function isTableStart(lines, index) {
  return lines[index]?.includes("|") && /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[index + 1] || "");
}

function parseTable(lines, startIndex) {
  const header = splitTableRow(lines[startIndex]);
  const rows = [];
  let index = startIndex + 2;
  while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
    rows.push(splitTableRow(lines[index]));
    index += 1;
  }
  return { block: { type: "table", header, rows }, nextIndex: index };
}

function splitTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function inlineHtml(text = "") {
  let html = escapeHtml(text);
  html = html.replace(
    /\[([^\]]+)]\((https?:\/\/[^)\s]+|mailto:[^)\s]+|tel:[^)\s]+|#[^)\s]+)\)/g,
    (_match, label, url) => `<a href="${escapeAttribute(url)}" target="_blank" rel="noreferrer">${label}</a>`,
  );
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return html;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}
</script>
