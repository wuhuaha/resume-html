<template>
  <main class="site-shell">
    <nav class="top-nav">
      <a class="brand" href="/">
        <span class="brand-mark">WT</span>
        <span>AI Profile</span>
      </a>
      <div class="nav-actions">
        <div class="nav-links">
          <a href="#capabilities">{{ page.nav.capabilities }}</a>
          <a href="#timeline">{{ page.nav.timeline }}</a>
          <a href="#projects">{{ page.nav.projects }}</a>
          <a href="/resume/export">{{ page.nav.export }}</a>
        </div>
        <div class="nav-tools">
          <a class="ghost-link" href="/admin">{{ page.nav.admin }}</a>
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
              <MarkdownBlock v-if="message.role === 'assistant'" :text="message.content" />
              <p v-else>{{ message.content }}</p>
            </article>
          </n-scrollbar>

          <form class="chat-input refined hero-query" @submit.prevent="ask(input)">
            <n-button
              circle
              secondary
              type="primary"
              :class="{ active: listening }"
              :loading="voiceLoading && !listening"
              :disabled="!voiceConfigured || !canRecord"
              attr-type="button"
              title="按住说话，松开识别"
              @pointerdown.prevent="pressVoiceStart"
              @pointerup.prevent="pressVoiceEnd"
              @pointercancel.prevent="pressVoiceEnd"
              @keydown.space.prevent="pressVoiceStart"
              @keyup.space.prevent="pressVoiceEnd"
              @keydown.enter.prevent="pressVoiceStart"
              @keyup.enter.prevent="pressVoiceEnd"
            >
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
              <div class="timeline-meta">
                <span>{{ timelinePeriod(item.title) }}</span>
                <strong>{{ timelineCompany(item.title) }}</strong>
                <small>{{ timelineRole(item.title) }}</small>
              </div>
              <div class="timeline-body">
                <h3>{{ timelineRole(item.title) }}</h3>
                <p v-if="item.focus" class="focus-line">{{ item.focus }}</p>
                <MarkdownBlock :text="item.body" />
              </div>
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
              <MarkdownBlock :text="compactMarkdown(item.body, 3)" />
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
import {
  askProfile,
  getBriefing,
  getVoiceConfig,
  getVoiceHotwords,
  streamSynthesizeVoice,
  streamTranscribeVoice,
  synthesizeVoice,
  transcribeVoice,
} from "../api";
import MarkdownBlock from "../components/MarkdownBlock.vue";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";

const briefing = ref(null);
const input = ref("");
const loading = ref(false);
const listening = ref(false);
const voiceLoading = ref(false);
const voiceConfigured = ref(false);
const canRecord = Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const voicePressing = ref(false);
const voicePointerTarget = ref(null);
const voicePointerId = ref(null);
const currentAudioUrl = ref("");
const audioContext = ref(null);
const pcmStartTime = ref(0);
const localVoiceCloneReference = ref("");
const voiceCloneActive = ref(false);
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
    eyebrow: "AI 助手",
    title: "向王涛提问",
    context: "我是授权 AI 助手，可代替本人向招聘方简短回答经历、项目和岗位匹配问题。",
    placeholder: "问：语音 Agent 难点？",
    voiceHint: "按住麦克风说话，松开后识别；也可以文字连续追问。",
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

function timelineParts(title) {
  const parts = String(title || "").split("|").map((part) => part.trim()).filter(Boolean);
  return {
    company: parts[0] || title,
    role: parts[1] || "",
    period: parts[2] || "",
  };
}

function timelineCompany(title) {
  return timelineParts(title).company;
}

function timelineRole(title) {
  const parts = timelineParts(title);
  return parts.role || parts.company;
}

function timelinePeriod(title) {
  return timelineParts(title).period || "经历";
}

function compactMarkdown(text, maxBullets = 3) {
  const lines = String(text || "").split("\n");
  let bulletCount = 0;
  const compact = [];
  for (const line of lines) {
    const isBullet = line.trim().startsWith("- ");
    if (isBullet) {
      bulletCount += 1;
      if (bulletCount > maxBullets) continue;
    }
    compact.push(line);
  }
  return compact.join("\n").trim();
}

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
    content: `你好，我是${meta.value.name || "王涛"}的授权 AI 助手。你可以像面试官一样连续追问，我会尽量用短回答说明经历、项目和岗位匹配。`,
  });

  try {
    const voice = await getVoiceConfig();
    voiceConfigured.value = voice.configured;
    localVoiceCloneReference.value = localStorage.getItem("ai-profile-voice-clone-reference") || "";
    voiceCloneActive.value = Boolean(voice.voiceCloneEnabled || localVoiceCloneReference.value);
    if (voice.configured && canRecord) {
      voiceHint.value = voiceCloneActive.value
        ? "小米 ASR/TTS 已接入，按住麦克风说话，松开后识别；回答将使用参考音色复刻。"
        : `小米在线 ASR/TTS 已接入，已加载 ${voice.hotwordCount || 0} 个候选热词；按住麦克风说话，松开后识别。`;
      warmVoiceHotwords();
    } else if (!canRecord) {
      voiceHint.value = "当前浏览器不支持录音，或可能是浏览器对本网页禁用了麦克风，请使用文字输入。";
    } else {
      voiceHint.value = "后端未配置小米语音 Key，请使用文字输入。";
    }
  } catch {
    voiceHint.value = "语音服务暂时不可用，请使用文字输入。";
  }
});

async function warmVoiceHotwords() {
  try {
    const result = await getVoiceHotwords();
    if (result.count) {
      voiceHint.value = voiceCloneActive.value
        ? `小米 ASR/TTS 已接入，已加载 ${result.count} 个 ASR 热词；按住说话，回答将使用参考音色复刻。`
        : `小米在线 ASR/TTS 已接入，已加载 ${result.count} 个 ASR 热词；按住麦克风说话，松开后识别。`;
    }
  } catch {
    // 热词预热失败不影响语音主流程。
  }
}

async function ask(question) {
  const content = question.trim();
  if (!content || loading.value) return;
  input.value = "";
  messages.value.push({ id: Date.now(), role: "user", content });
  loading.value = true;
  try {
    const result = await askProfile(content, messages.value);
    messages.value.push({ id: Date.now() + 1, role: "assistant", content: result.answer });
    await playAnswer(result.answer);
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

async function pressVoiceStart(event) {
  if (event?.repeat || voicePressing.value || listening.value || voiceLoading.value) {
    return;
  }
  if (!voiceConfigured.value) {
    voiceHint.value = "小米语音服务未配置，请使用文字输入。";
    return;
  }
  if (!canRecord) {
    voiceHint.value = "当前浏览器不支持录音，或可能是浏览器对本网页禁用了麦克风，请使用文字输入。";
    return;
  }
  if (event?.currentTarget && event.pointerId !== undefined) {
    voicePointerTarget.value = event.currentTarget;
    voicePointerId.value = event.pointerId;
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }
  voicePressing.value = true;
  await startRecording();
}

function pressVoiceEnd(event) {
  if (!voicePressing.value && !listening.value) return;
  releaseVoicePointer(event);
  voicePressing.value = false;
  stopRecording();
}

function releaseVoicePointer(event) {
  const target = voicePointerTarget.value || event?.currentTarget;
  const pointerId = voicePointerId.value ?? event?.pointerId;
  if (target && pointerId !== null && pointerId !== undefined) {
    target.releasePointerCapture?.(pointerId);
  }
  voicePointerTarget.value = null;
  voicePointerId.value = null;
}

async function startRecording() {
  voiceLoading.value = true;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    if (!voicePressing.value) {
      stream.getTracks().forEach((track) => track.stop());
      voiceHint.value = "按住麦克风说话，松开后识别。";
      return;
    }
    const mimeType = chooseMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    audioChunks.value = [];
    recorder.ondataavailable = (event) => {
      if (event.data?.size) audioChunks.value.push(event.data);
    };
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      await submitRecording(mimeType || "audio/webm");
    };
    mediaRecorder.value = recorder;
    recorder.start();
    listening.value = true;
    voiceHint.value = "正在录音，松开麦克风后提交识别。";
  } catch (error) {
    voicePressing.value = false;
    voiceHint.value = `无法启动录音：${error.message}。可能是浏览器对本网页禁用了麦克风。`;
  } finally {
    voiceLoading.value = false;
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state !== "inactive") {
    voiceHint.value = "正在提交小米 ASR 识别...";
    mediaRecorder.value.stop();
  }
  voicePressing.value = false;
  listening.value = false;
}

async function submitRecording(mimeType) {
  if (!audioChunks.value.length) {
    voiceHint.value = "没有录到有效音频，请重试。";
    return;
  }
  voiceLoading.value = true;
  try {
    const sourceBlob = new Blob(audioChunks.value, { type: mimeType });
    const wavBlob = await convertBlobToWav(sourceBlob);
    const text = await streamTranscribeVoice(wavBlob, (partialText) => {
      input.value = partialText;
      voiceHint.value = "正在接收小米 ASR 流式识别结果...";
    });
    input.value = text.trim();
    voiceHint.value = "已识别语音，可编辑后发送。";
  } catch (error) {
    try {
      const sourceBlob = new Blob(audioChunks.value, { type: mimeType });
      const wavBlob = await convertBlobToWav(sourceBlob);
      const result = await transcribeVoice(wavBlob);
      input.value = result.text;
      voiceHint.value = "已识别语音，可编辑后发送。";
    } catch (fallbackError) {
      voiceHint.value = `小米 ASR 识别失败：${fallbackError.message || error.message}`;
    }
  } finally {
    voiceLoading.value = false;
  }
}

async function playAnswer(text) {
  if (!voiceConfigured.value || !text.trim()) return;
  try {
    if (!localVoiceCloneReference.value && (window.AudioContext || window.webkitAudioContext)) {
      await playStreamingPcm(text);
      return;
    }
    await playBufferedVoice(text);
  } catch (error) {
    try {
      await playBufferedVoice(text);
    } catch (fallbackError) {
      voiceHint.value = `小米 TTS 播放失败：${fallbackError.message || error.message}`;
    }
  }
}

function chooseMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((item) => MediaRecorder.isTypeSupported(item)) || "";
}

async function playBufferedVoice(text) {
  const blob = await synthesizeVoice(text, localVoiceCloneReference.value);
  if (currentAudioUrl.value) URL.revokeObjectURL(currentAudioUrl.value);
  currentAudioUrl.value = URL.createObjectURL(blob);
  const audio = new Audio(currentAudioUrl.value);
  await audio.play();
}

async function playStreamingPcm(text) {
  const stream = await streamSynthesizeVoice(text, localVoiceCloneReference.value);
  if (!stream) throw new Error("浏览器不支持流式音频。");

  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!audioContext.value) audioContext.value = new AudioContextClass({ sampleRate: 24000 });
  if (audioContext.value.state === "suspended") await audioContext.value.resume();

  pcmStartTime.value = Math.max(audioContext.value.currentTime + 0.08, pcmStartTime.value);
  const reader = stream.getReader();
  let pending = new Uint8Array(0);

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (!value?.length) continue;

    pending = mergeUint8(pending, value);
    const usableLength = pending.length - (pending.length % 2);
    if (usableLength < 4800) continue;

    const chunk = pending.slice(0, usableLength);
    pending = pending.slice(usableLength);
    schedulePcmChunk(chunk);
  }

  if (pending.length >= 2) {
    schedulePcmChunk(pending.slice(0, pending.length - (pending.length % 2)));
  }
}

function schedulePcmChunk(bytes) {
  const context = audioContext.value;
  const samples = bytes.length / 2;
  const buffer = context.createBuffer(1, samples, 24000);
  const channel = buffer.getChannelData(0);
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

  for (let index = 0; index < samples; index += 1) {
    channel[index] = Math.max(-1, Math.min(1, view.getInt16(index * 2, true) / 32768));
  }

  const source = context.createBufferSource();
  source.buffer = buffer;
  source.connect(context.destination);
  source.start(pcmStartTime.value);
  pcmStartTime.value += buffer.duration;
}

function mergeUint8(left, right) {
  if (!left.length) return right;
  const merged = new Uint8Array(left.length + right.length);
  merged.set(left, 0);
  merged.set(right, left.length);
  return merged;
}

async function convertBlobToWav(blob) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return blob;

  const arrayBuffer = await blob.arrayBuffer();
  const context = new AudioContextClass();
  try {
    const decoded = await context.decodeAudioData(arrayBuffer);
    return encodeWav(decoded);
  } finally {
    await context.close();
  }
}

function encodeWav(audioBuffer) {
  const channels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const length = audioBuffer.length * channels * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);
  const channelData = Array.from({ length: channels }, (_, index) => audioBuffer.getChannelData(index));
  let offset = 44;

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + length, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * channels * 2, true);
  view.setUint16(32, channels * 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, length, true);

  for (let index = 0; index < audioBuffer.length; index += 1) {
    for (let channel = 0; channel < channels; channel += 1) {
      const sample = Math.max(-1, Math.min(1, channelData[channel][index]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }
  }

  return new Blob([buffer], { type: "audio/wav" });
}

function writeString(view, offset, text) {
  for (let index = 0; index < text.length; index += 1) {
    view.setUint8(offset + index, text.charCodeAt(index));
  }
}
</script>
