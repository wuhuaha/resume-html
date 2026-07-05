<template>
  <main class="page-shell compact admin-page unified-admin-page">
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
        <h1>{{ showcaseMode ? "展示项目模式" : "输入修改密码" }}</h1>
        <p class="muted-copy">
          {{ showcaseMode ? showcaseNotice : "进入内容工作台，维护资料库和首页展示编排。" }}
        </p>

        <form v-if="!showcaseMode" class="login-form" @submit.prevent="login">
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
        <div v-else class="login-form">
          <n-button type="primary" size="large" :loading="loading" @click="enterShowcase">
            进入体验后台
          </n-button>
          <div class="admin-switch-login">
            <n-input
              v-model:value="adminPasswordInput"
              size="large"
              type="password"
              show-password-on="mousedown"
              placeholder="管理密码"
              @keyup.enter="switchToAdminMode"
            />
            <n-button size="large" :loading="adminModeLoading" @click="switchToAdminMode">
              切换到管理员模式
            </n-button>
          </div>
        </div>

        <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
          {{ status }}
        </n-alert>
      </div>
    </section>

    <template v-else>
      <header class="admin-page-head">
        <div>
          <p class="eyebrow">作者后台</p>
          <h1>内容工作台</h1>
          <p class="muted-copy">
            资料库维护事实 Markdown；首页编排调整公开页面展示。手动和 AI 能力都在同一个入口内完成。
          </p>
          <p v-if="showcaseMode" class="showcase-inline-note">
            {{ adminMode ? "当前已切换到管理员模式，保存会真实写入线上内容。" : showcaseNotice }}
          </p>
        </div>
        <div class="admin-head-actions">
          <span v-if="showcaseMode" :class="['save-state', adminMode ? 'is-admin' : 'is-demo']">
            {{ adminMode ? "管理员模式" : "体验模式" }}
          </span>
          <span :class="['save-state', activeDirty ? 'is-dirty' : '']">{{ activeDirty ? "有未保存修改" : "已同步" }}</span>
          <n-button v-if="showcaseMode && !adminMode" secondary type="primary" @click="showAdminSwitch = !showAdminSwitch">
            切换到管理员模式
          </n-button>
          <n-button quaternary @click="logout">退出</n-button>
        </div>
      </header>

      <section v-if="showcaseMode && showAdminSwitch && !adminMode" class="admin-switch-panel">
        <div>
          <h2>管理员模式</h2>
          <p>输入管理密码后，本页保存、上传、删除等操作会真实写入线上内容。</p>
        </div>
        <div class="admin-switch-form">
          <n-input
            v-model:value="adminPasswordInput"
            type="password"
            show-password-on="mousedown"
            placeholder="管理密码"
            @keyup.enter="switchToAdminMode"
          />
          <n-button type="primary" :loading="adminModeLoading" @click="switchToAdminMode">
            确认切换
          </n-button>
        </div>
      </section>

      <div class="admin-mode-tabs">
        <button type="button" :class="{ active: mode === 'content' }" @click="mode = 'content'">
          <FileText :size="17" />
          <span>资料库</span>
        </button>
        <button type="button" :class="{ active: mode === 'home' }" @click="mode = 'home'">
          <LayoutTemplate :size="17" />
          <span>首页编排</span>
        </button>
        <button type="button" :class="{ active: mode === 'style' }" @click="mode = 'style'">
          <Palette :size="17" />
          <span>视觉风格</span>
        </button>
        <button type="button" :class="{ active: mode === 'resume' }" @click="mode = 'resume'">
          <FileDown :size="17" />
          <span>简历导出</span>
        </button>
        <button type="button" :class="{ active: mode === 'voice' }" @click="mode = 'voice'">
          <Mic :size="17" />
          <span>语音音色</span>
        </button>
      </div>

      <n-alert v-if="showcaseMode" class="admin-alert showcase-alert" type="warning" :bordered="false">
        {{ adminMode ? "当前处于管理员模式：保存、上传和删除会真实写入线上内容，请确认后操作。" : "当前处于展示项目模式：后台已免验证。你可以体验导入、AI 生成、首页编排、风格预览和导出策略调整；如需保存，请点击“切换到管理员模式”并输入管理密码。" }}
      </n-alert>

      <section v-if="mode === 'content'" class="ai-two-column">
        <aside class="workspace-panel ai-command-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>写入</h2>
              <p>{{ showcaseMode && !adminMode ? "展示模式下可编辑草稿；切换到管理员模式后可保存到内容源。" : "保存当前 Markdown，或重新读取内容源。" }}</p>
            </div>

            <div class="button-row">
              <n-button type="primary" size="large" :loading="saving" @click="saveMarkdown">
                <template #icon><Save :size="18" /></template>
                保存 Markdown
              </n-button>
              <n-button size="large" :loading="loading" @click="loadMarkdown">
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

            <n-button block secondary size="large" :disabled="!file" :loading="converting" @click="convert">
              <template #icon><FileText :size="18" /></template>
              导入到编辑器
            </n-button>
          </section>

          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>AI 辅助</h2>
              <p>基于当前 Markdown 改写、重排和精简，不新增事实。</p>
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

            <n-button
              block
              type="primary"
              :loading="markdownAiLoading"
              :disabled="!markdownInstruction.trim()"
              @click="runMarkdownEdit"
            >
              <template #icon><Bot :size="18" /></template>
              生成资料草稿
            </n-button>
          </section>

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
              <span>{{ sectionCount }} 个章节</span>
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

      <section v-else-if="mode === 'home'" class="ai-two-column home-compose-layout">
        <aside class="workspace-panel ai-command-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>调整首页</h2>
              <p>{{ showcaseMode && !adminMode ? "展示模式下可基于当前 Markdown 生成首页草稿并预览；切换到管理员模式后可保存到公开首页。" : "修改 Markdown 后，先重新生成首页草稿，确认预览后再保存首页。" }}</p>
            </div>

            <n-button
              block
              type="primary"
              size="large"
              :loading="homeRegenerating"
              :disabled="!markdown.trim()"
              @click="regenerateHomeFromMarkdown"
            >
              <template #icon><RefreshCw :size="18" /></template>
              基于当前 Markdown 重新生成首页
            </n-button>

            <p class="admin-flow-hint">
              适合在资料库 Markdown 修改后使用；下方“按说明微调”只会继续调整当前首页草稿。
            </p>

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
                按说明微调草稿
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
          </section>

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

      <section v-else-if="mode === 'style'" class="ai-two-column style-compose-layout">
        <aside class="workspace-panel ai-command-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>风格预设</h2>
              <p>{{ showcaseMode && !adminMode ? "展示模式下可切换并预览风格；切换到管理员模式后保存会让公开页面生效。" : "参考设计系统审美抽象为项目内置预设。选择后先预览，保存后公开页面生效。" }}</p>
            </div>

            <div class="style-preset-list">
              <button
                v-for="preset in stylePresets"
                :key="preset.key"
                type="button"
                :class="{ active: preset.key === selectedStyleKey }"
                @click="selectStyle(preset.key)"
              >
                <span class="style-swatch" :style="{ background: preset.accent }"></span>
                <span>
                  <strong>{{ preset.label }}</strong>
                  <small>{{ preset.source }}</small>
                </span>
              </button>
            </div>

            <div class="ai-command-row">
              <n-button type="primary" :loading="styleSaving" :disabled="selectedStyleKey === publishedStyleKey" @click="saveStyleDraft">
                <template #icon><Save :size="18" /></template>
                保存风格
              </n-button>
              <n-button :disabled="selectedStyleKey === publishedStyleKey" @click="resetStylePreview">
                <template #icon><RefreshCw :size="18" /></template>
                恢复已发布
              </n-button>
            </div>
          </section>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-main-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">Style preview</p>
              <h2>{{ selectedStyle?.label || "视觉风格" }}</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ selectedStyleKey === publishedStyleKey ? "已发布" : "预览中" }}</span>
              <span>{{ selectedStyle?.density === "comfortable" ? "舒展密度" : "紧凑密度" }}</span>
            </div>
          </div>

          <div class="style-preview">
            <div class="style-preview-hero">
              <p class="eyebrow">{{ selectedStyle?.source }}</p>
              <h3>{{ selectedStyle?.label }}</h3>
              <p>{{ selectedStyle?.description }}</p>
            </div>
            <div class="style-token-grid">
              <article>
                <span>主色</span>
                <strong>{{ selectedStyle?.accent }}</strong>
              </article>
              <article>
                <span>辅助色</span>
                <strong>{{ selectedStyle?.accent2 }}</strong>
              </article>
              <article>
                <span>圆角</span>
                <strong>{{ selectedStyle?.radius }}</strong>
              </article>
              <article>
                <span>卡片质感</span>
                <strong>{{ selectedStyle?.cardTone }}</strong>
              </article>
            </div>
            <div class="style-demo-row">
              <n-button type="primary">
                <template #icon><Palette :size="17" /></template>
                主按钮
              </n-button>
              <n-button secondary>次级按钮</n-button>
            </div>
            <div class="style-mini-cards">
              <article>
                <span>01</span>
                <h4>语音 Agent</h4>
                <p>强调岗位匹配、技术深度和可验证结果。</p>
              </article>
              <article>
                <span>02</span>
                <h4>工程证据</h4>
                <p>用项目、时间线和指标支撑能力判断。</p>
              </article>
            </div>
          </div>
        </section>
      </section>

      <section v-else-if="mode === 'resume'" class="ai-two-column resume-config-layout">
        <aside class="workspace-panel ai-command-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>导出策略</h2>
              <p>{{ showcaseMode && !adminMode ? "展示模式下可调整导出策略体验配置；切换到管理员模式后可保存为线上默认策略。" : "控制 ATS 一页纸和其他导出模式的内容预算、版面密度和保留范围。" }}</p>
            </div>

            <div class="style-preset-list">
              <button
                v-for="(item, key) in resumeConfig.modes"
                :key="key"
                type="button"
                :class="{ active: key === resumeConfig.activeMode }"
                @click="selectResumeMode(key)"
              >
                <span class="style-swatch resume-mode-swatch">{{ item.targetPages || '∞' }}</span>
                <span>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.description }}</small>
                </span>
              </button>
            </div>

            <div class="admin-section-heading secondary-heading">
              <h2>默认样式模板</h2>
              <p>参考 JSON Resume、Reactive Resume、OpenResume 和 RenderCV 的思路，模板负责版式，LLM 负责内容取舍。</p>
            </div>

            <div class="style-preset-list">
              <button
                v-for="(item, key) in resumeConfig.templates"
                :key="key"
                type="button"
                :class="{ active: key === resumeConfig.activeTemplate }"
                @click="selectResumeTemplate(key)"
              >
                <span class="style-swatch" :style="{ background: item.accent }"></span>
                <span>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.inspiration }}</small>
                </span>
              </button>
            </div>

            <div class="ai-command-row">
              <n-button type="primary" :loading="resumeConfigSaving" :disabled="!resumeConfigDirty" @click="saveResumeConfigDraft">
                <template #icon><Save :size="18" /></template>
                保存导出策略
              </n-button>
              <n-button :loading="resumeConfigLoading" @click="loadResumeConfig">
                <template #icon><RefreshCw :size="18" /></template>
                重新加载
              </n-button>
            </div>
          </section>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-main-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">Resume export</p>
              <h2>{{ activeResumeMode.label }} · {{ activeResumeTemplate.label }}</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ activeResumeMode.targetPages ? `${activeResumeMode.targetPages} 页目标` : "不限页数" }}</span>
              <span>{{ resumeConfigDirty ? "未保存" : "已同步" }}</span>
            </div>
          </div>

          <div class="resume-config-grid">
            <label>
              <span>摘要行数</span>
              <input v-model.number="activeResumeMode.summaryLines" type="number" min="1" max="5" @input="touchResumeConfig" />
            </label>
            <label>
              <span>核心能力条数</span>
              <input v-model.number="activeResumeMode.skillCount" type="number" min="3" max="10" @input="touchResumeConfig" />
            </label>
            <label>
              <span>经历公司数</span>
              <input v-model.number="activeResumeMode.experienceCount" type="number" min="1" max="6" @input="touchResumeConfig" />
            </label>
            <label>
              <span>每段经历 bullet</span>
              <input v-model.number="activeResumeMode.experienceBullets" type="number" min="1" max="8" @input="touchResumeConfig" />
            </label>
            <label>
              <span>项目数量</span>
              <input v-model.number="activeResumeMode.projectCount" type="number" min="0" max="5" @input="touchResumeConfig" />
            </label>
            <label>
              <span>每项目 bullet</span>
              <input v-model.number="activeResumeMode.projectBullets" type="number" min="1" max="6" @input="touchResumeConfig" />
            </label>
            <label>
              <span>字号</span>
              <input v-model.number="activeResumeMode.fontSize" type="number" min="10.5" max="15" step="0.1" @input="touchResumeConfig" />
            </label>
            <label>
              <span>行高</span>
              <input v-model.number="activeResumeMode.lineHeight" type="number" min="1.18" max="1.7" step="0.01" @input="touchResumeConfig" />
            </label>
            <label>
              <span>页边距 mm</span>
              <input v-model.number="activeResumeMode.pageMarginMm" type="number" min="6" max="18" @input="touchResumeConfig" />
            </label>
            <label>
              <span>分区间距 px</span>
              <input v-model.number="activeResumeMode.sectionSpacing" type="number" min="4" max="24" @input="touchResumeConfig" />
            </label>
          </div>

          <div class="resume-config-toggles">
            <label>
              <input v-model="activeResumeMode.includeAwards" type="checkbox" @change="touchResumeConfig" />
              <span>保留奖项荣誉</span>
            </label>
            <label>
              <input v-model="activeResumeMode.includeCertificates" type="checkbox" @change="touchResumeConfig" />
              <span>保留证书信息</span>
            </label>
            <label>
              <input v-model="activeResumeMode.includeBirth" type="checkbox" @change="touchResumeConfig" />
              <span>保留出生日期</span>
            </label>
            <label>
              <input v-model="activeResumeMode.includeAvatar" type="checkbox" @change="touchResumeConfig" />
              <span>允许模板显示头像</span>
            </label>
          </div>

          <div class="resume-config-section">
            <div class="admin-section-heading inline-heading">
              <h2>样式模板配置</h2>
              <p>{{ activeResumeTemplate.description }}</p>
            </div>
            <div class="resume-config-grid">
              <label>
                <span>模板名称</span>
                <input v-model="activeResumeTemplate.label" type="text" @input="touchResumeConfig" />
              </label>
              <label>
                <span>参考来源</span>
                <input v-model="activeResumeTemplate.inspiration" type="text" @input="touchResumeConfig" />
              </label>
              <label>
                <span>主色</span>
                <input v-model="activeResumeTemplate.accent" type="text" @input="touchResumeConfig" />
              </label>
              <label>
                <span>布局</span>
                <select v-model="activeResumeTemplate.layout" @change="touchResumeConfig">
                  <option value="single">单栏</option>
                  <option value="sidebar">侧栏</option>
                  <option value="timeline">时间线</option>
                  <option value="brief">技术档案</option>
                  <option value="compact">紧凑</option>
                </select>
              </label>
              <label>
                <span>头像位置</span>
                <select v-model="activeResumeTemplate.avatarPlacement" @change="touchResumeConfig">
                  <option value="header-right">页眉右侧</option>
                  <option value="sidebar-top">侧栏顶部</option>
                </select>
              </label>
              <label class="full-row">
                <span>LLM 模板策略</span>
                <textarea v-model="activeResumeTemplate.llmInstruction" rows="3" @input="touchResumeConfig"></textarea>
              </label>
            </div>
            <div class="resume-config-toggles">
              <label>
                <input v-model="activeResumeTemplate.footerEnabled" type="checkbox" @change="touchResumeConfig" />
                <span>显示开源项目页脚</span>
              </label>
            </div>
          </div>

          <div class="resume-config-section">
            <div class="admin-section-heading inline-heading">
              <h2>导出头像</h2>
              <p>{{ resumeAvatarExportHint }}</p>
            </div>
            <div class="resume-avatar-row enhanced">
              <div class="resume-avatar-preview">
                <img v-if="resumeAvatarPreviewUrl" :src="resumeAvatarPreviewUrl" alt="简历头像预览" />
                <div v-else class="resume-avatar-placeholder">
                  <Upload :size="22" />
                </div>
                <div>
                  <span>{{ resumeAvatar.enabled ? "当前导出头像" : "未上传头像" }}</span>
                  <strong>{{ resumeAvatar.filename || resumeAvatarFileName || "可选 JPG / PNG / WebP" }}</strong>
                  <small v-if="resumeAvatar.size">{{ formatBytes(resumeAvatar.size) }}</small>
                  <small>{{ resumeAvatarPlacementText }}</small>
                </div>
              </div>
              <label class="avatar-upload-button">
                <Upload :size="18" />
                <span>{{ resumeAvatarFileName || "上传照片头像" }}</span>
                <input type="file" accept="image/png,image/jpeg,image/webp" @change="selectResumeAvatarFile" />
              </label>
              <n-button :disabled="!resumeAvatarFile" :loading="resumeAvatarSaving" @click="saveResumeAvatarFile">
                <template #icon><Save :size="18" /></template>
                保存头像
              </n-button>
              <n-button :disabled="!resumeAvatar.enabled" @click="clearResumeAvatar">
                删除头像
              </n-button>
            </div>
            <div class="resume-config-toggles">
              <label>
                <input v-model="activeResumeMode.includeAvatar" type="checkbox" @change="touchResumeConfig" />
                <span>当前篇幅模式允许导出头像</span>
              </label>
              <label>
                <input v-model="activeResumeTemplate.showAvatar" type="checkbox" @change="touchResumeConfig" />
                <span>当前模板显示头像</span>
              </label>
            </div>
          </div>

          <div class="resume-config-section">
            <div class="admin-section-heading inline-heading">
              <h2>开源署名</h2>
              <p>导出 HTML/PDF 底部显示开源项目来源、作者和仓库地址。</p>
            </div>
            <div class="resume-config-grid">
              <label>
                <span>GitHub 地址</span>
                <input v-model="resumeConfig.branding.githubUrl" type="text" @input="touchResumeConfig" />
              </label>
              <label>
                <span>开源作者</span>
                <input v-model="resumeConfig.branding.author" type="text" @input="touchResumeConfig" />
              </label>
              <label class="full-row">
                <span>页脚说明</span>
                <input v-model="resumeConfig.branding.text" type="text" @input="touchResumeConfig" />
              </label>
            </div>
            <div class="resume-config-toggles">
              <label>
                <input v-model="resumeConfig.branding.enabled" type="checkbox" @change="touchResumeConfig" />
                <span>启用导出页脚开源说明</span>
              </label>
            </div>
          </div>

          <div class="resume-budget-preview">
            <article>
              <span>预计内容预算</span>
              <strong>{{ estimatedBulletBudget }} 条 bullet</strong>
              <p>包含核心能力、经历、项目和可选荣誉。实际导出会按 JD 关键词优先保留相关内容。</p>
            </article>
            <article>
              <span>当前模式说明</span>
              <strong>{{ activeResumeMode.description }}</strong>
              <p>一页纸建议控制在 18-22 条 bullet；两页版可以保留更多项目细节。</p>
            </article>
          </div>
        </section>
      </section>

      <section v-else class="ai-two-column voice-clone-layout">
        <aside class="workspace-panel ai-command-panel">
          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>参考音色</h2>
              <p>
                {{ showcaseMode && !adminMode ? "展示模式下参考音色只保存在当前浏览器，用于本机首页体验，不写入服务器。" : "上传或录制一段 WAV/MP3 参考音频，首页回答将使用小米音色复刻合成。" }}
              </p>
            </div>

            <div class="voice-clone-state">
              <span>{{ voiceReference.enabled || localVoiceReference ? "已启用音色复刻" : "未配置参考音色" }}</span>
              <strong>{{ voiceReference.filename || localVoiceReferenceName || "默认小米音色" }}</strong>
              <small v-if="voiceReference.size || localVoiceReferenceSize">{{ formatBytes(voiceReference.size || localVoiceReferenceSize) }}</small>
              <small v-if="voiceReference.updatedAt">{{ formatDate(voiceReference.updatedAt) }}</small>
            </div>
          </section>

          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>上传音频</h2>
              <p>支持 WAV 或 MP3；小米要求 Base64 后不超过 10 MB。</p>
            </div>

            <label class="upload-box compact-upload">
              <Upload :size="24" />
              <span>{{ voiceFileName || "选择参考音频" }}</span>
              <input type="file" accept=".wav,.mp3,audio/wav,audio/mpeg" @change="selectVoiceFile" />
            </label>

            <n-button block type="primary" :disabled="!voiceFile" :loading="voiceSaving" @click="saveVoiceReferenceFromFile">
              <template #icon><Save :size="18" /></template>
              使用该音频
            </n-button>
          </section>

          <section class="admin-action-section">
            <div class="admin-section-heading">
              <h2>录制样本</h2>
              <p>建议录制 10-20 秒清晰自然语音，环境尽量安静。</p>
            </div>

            <div class="ai-command-row">
              <n-button type="primary" :loading="voiceRecordingBusy" @click="toggleVoiceReferenceRecording">
                <template #icon><Mic :size="18" /></template>
                {{ voiceRecording ? "结束录制" : "开始录制" }}
              </n-button>
              <n-button :disabled="!recordedVoiceBlob" :loading="voiceSaving" @click="saveRecordedVoiceReference">
                <template #icon><Save :size="18" /></template>
                使用录音
              </n-button>
            </div>

            <audio v-if="recordedVoiceUrl" class="voice-reference-player" :src="recordedVoiceUrl" controls></audio>
          </section>

          <section class="admin-action-section">
            <div class="ai-command-row">
              <n-button :disabled="!voiceReference.enabled && !localVoiceReference" @click="clearVoiceReference">
                <template #icon><RefreshCw :size="18" /></template>
                恢复默认音色
              </n-button>
              <n-button :loading="voiceReferenceLoading" @click="loadVoiceReference">
                <template #icon><RefreshCw :size="18" /></template>
                重新读取
              </n-button>
            </div>
          </section>

          <n-alert v-if="status" class="admin-alert" :type="statusType" :bordered="false">
            {{ status }}
          </n-alert>
        </aside>

        <section class="preview-panel ai-main-panel">
          <div class="preview-toolbar">
            <div>
              <p class="eyebrow">Voice clone</p>
              <h2>小米 TTS 音色复刻</h2>
            </div>
            <div class="admin-doc-stats">
              <span>{{ voiceReference.enabled || localVoiceReference ? "参考音色已就绪" : "默认音色" }}</span>
              <span>{{ showcaseMode ? "浏览器本地体验" : "服务端保存" }}</span>
            </div>
          </div>

          <div class="resume-budget-preview">
            <article>
              <span>调用方式</span>
              <strong>mimo-v2.5-tts-voiceclone</strong>
              <p>首页回答播放时，后端会把参考音频作为 audio.voice 传给小米 TTS。没有参考音频时继续使用内置音色。</p>
            </article>
            <article>
              <span>隐私边界</span>
              <strong>{{ showcaseMode ? "不上传保存到服务器" : "仅保存在服务器 storage 目录" }}</strong>
              <p>展示模式下样本只存在当前浏览器 localStorage；正式模式下可删除并恢复默认音色。</p>
            </article>
          </div>
        </section>
      </section>
    </template>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { NAlert, NButton, NInput } from "naive-ui";
import {
  Bot,
  FileDown,
  FileText,
  LayoutTemplate,
  Mic,
  Palette,
  RefreshCw,
  Save,
  Settings,
  Upload,
} from "lucide-vue-next";
import {
  clearStoredAdminPassword,
  getStoredAdminPassword,
  setStoredAdminPassword,
} from "../adminAuth";
import {
  adminLogin,
  aiEditHomeBriefing,
  aiEditMarkdown,
  deleteResumeAvatar,
  deleteVoiceCloneReference,
  getAdminMode,
  getAdminSiteStyle,
  getAdminResumeExportConfig,
  getHomeBriefingDraft,
  getMarkdownDocument,
  getResumeAvatar,
  getVoiceCloneReference,
  importDocument,
  previewMarkdownBriefing,
  reindexContent,
  saveAdminSiteStyle,
  saveAdminResumeExportConfig,
  saveHomeBriefing,
  saveMarkdownDocument,
  saveResumeAvatar,
  saveVoiceCloneReference,
} from "../api";
import BriefingPreview from "../components/BriefingPreview.vue";
import MarkdownLiteEditor from "../components/MarkdownLiteEditor.vue";
import ThemeSwitcher from "../components/ThemeSwitcher.vue";
import {
  activeKey,
  activeTheme,
  applyStylePayload,
  clearThemePreview,
  markPublishedStyle,
  publishedStyleKey,
  setTheme,
  stylePresets,
} from "../theme";

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

const mode = ref("content");
const password = ref(getStoredAdminPassword());
const authenticated = ref(false);
const showcaseMode = ref(false);
const adminMode = ref(false);
const showAdminSwitch = ref(false);
const adminPasswordInput = ref("");
const adminModeLoading = ref(false);
const loading = ref(false);
const status = ref("");
const statusType = ref("info");

const markdown = ref("");
const documentPath = ref("");
const sectionCount = ref(0);
const markdownInstruction = ref("");
const markdownDirty = ref(false);
const markdownAiLoading = ref(false);
const saving = ref(false);
const converting = ref(false);
const file = ref(null);
const selectedName = ref("");

const homeBriefing = ref(null);
const homeInstruction = ref("");
const homeDirty = ref(false);
const homeSaved = ref(false);
const homeLoading = ref(false);
const homeAiLoading = ref(false);
const homeRegenerating = ref(false);
const homeSaving = ref(false);
const selectedStyleKey = ref(activeKey.value);
const styleSaving = ref(false);
const resumeConfig = ref({
  activeMode: "one-page",
  activeTemplate: "ats-classic",
  modes: {},
  templates: {},
  sectionOrder: ["summary", "skills", "experience", "projects", "awards"],
  branding: {
    enabled: true,
    githubUrl: "https://github.com/wuhuaha/resume-html",
    author: "王涛",
    text: "本简历由开源项目 Resume HTML 生成",
  },
});
const resumeConfigLoading = ref(false);
const resumeConfigSaving = ref(false);
const resumeConfigDirty = ref(false);
const resumeAvatar = ref({ enabled: false, filename: "", contentType: "", size: 0, updatedAt: "", dataUrl: "", message: "" });
const resumeAvatarFile = ref(null);
const resumeAvatarFileName = ref("");
const resumeAvatarLocalPreview = ref("");
const resumeAvatarSaving = ref(false);
const voiceReference = ref({ enabled: false, filename: "", contentType: "", size: 0, updatedAt: "", message: "" });
const voiceReferenceLoading = ref(false);
const voiceSaving = ref(false);
const voiceFile = ref(null);
const voiceFileName = ref("");
const voiceRecording = ref(false);
const voiceRecordingBusy = ref(false);
const voiceRecorder = ref(null);
const voiceRecordingChunks = ref([]);
const recordedVoiceBlob = ref(null);
const recordedVoiceUrl = ref("");
const localVoiceReference = ref(localStorage.getItem("ai-profile-voice-clone-reference") || "");
const localVoiceReferenceName = ref(localStorage.getItem("ai-profile-voice-clone-reference-name") || "");
const localVoiceReferenceSize = ref(Number(localStorage.getItem("ai-profile-voice-clone-reference-size") || 0));
const showcaseNotice = "当前为展示项目模式：后台免验证，可体验生成与预览；保存会被拦截，不会写入公开首页或线上内容。";

const adminPassword = computed(() => (adminMode.value ? getStoredAdminPassword() || password.value : ""));
const displayPath = computed(() => {
  if (!documentPath.value) return "content/profile.md";
  return documentPath.value.split(/[\\/]/).slice(-3).join("/");
});
const previewTitle = computed(() => homeBriefing.value?.hero?.statement || "等待生成首页编排");
const selectedStyle = computed(() => stylePresets.value.find((preset) => preset.key === selectedStyleKey.value) || activeTheme.value);
const activeResumeMode = computed(() => {
  const modes = resumeConfig.value.modes || {};
  return modes[resumeConfig.value.activeMode] || {};
});
const activeResumeTemplate = computed(() => {
  const templates = resumeConfig.value.templates || {};
  return templates[resumeConfig.value.activeTemplate] || {};
});
const estimatedBulletBudget = computed(() => {
  const mode = activeResumeMode.value;
  const awards = mode.includeAwards ? 4 : 0;
  return (
    Number(mode.skillCount || 0)
    + Number(mode.experienceCount || 0) * Number(mode.experienceBullets || 0)
    + Number(mode.projectCount || 0) * Number(mode.projectBullets || 0)
    + awards
  );
});
const resumeAvatarPreviewUrl = computed(() => resumeAvatarLocalPreview.value || resumeAvatar.value.dataUrl || "");
const resumeAvatarPlacementText = computed(() => {
  if (!activeResumeMode.value.includeAvatar) return "当前篇幅模式未启用头像";
  if (!activeResumeTemplate.value.showAvatar) return "当前模板未显示头像";
  if (!resumeAvatar.value.enabled && !resumeAvatarFile.value) return "上传后将用于 HTML/PDF 导出";
  return activeResumeTemplate.value.avatarPlacement === "sidebar-top" ? "导出位置：左侧栏顶部" : "导出位置：页眉右侧";
});
const resumeAvatarExportHint = computed(() => {
  if (showcaseMode.value && !adminMode.value) {
    return "展示模式下可选择头像预览，但不会写入服务器；切换到管理员模式后可保存为导出资产。";
  }
  return "上传照片头像后，可通过篇幅模式和模板开关决定是否出现在导出的 HTML/PDF 中。";
});
const activeDirty = computed(() => {
  if (mode.value === "content") return markdownDirty.value;
  if (mode.value === "home") return homeDirty.value;
  if (mode.value === "resume") return resumeConfigDirty.value || Boolean(resumeAvatarFile.value);
  if (mode.value === "voice") return false;
  return selectedStyleKey.value !== publishedStyleKey.value;
});

onMounted(async () => {
  await loadAdminMode();
  if (showcaseMode.value) {
    await enterShowcase();
    return;
  }
  if (password.value) {
    await login();
  }
});

onBeforeUnmount(() => {
  clearResumeAvatarLocalPreview();
  if (recordedVoiceUrl.value) URL.revokeObjectURL(recordedVoiceUrl.value);
});

function setStatus(message, type = "info") {
  status.value = message;
  statusType.value = type;
}

function formatSaveError(error, target = "保存") {
  if (showcaseMode.value && !adminMode.value) {
    return `${target}失败：当前为展示项目模式，可体验生成和预览；请切换到管理员模式并输入管理密码后再保存。`;
  }
  return `${target}失败：${error.message}`;
}

async function loadAdminMode() {
  try {
    const result = await getAdminMode();
    showcaseMode.value = Boolean(result.showcaseMode);
    if (result.message) setStatus(result.message, result.showcaseMode ? "warning" : "info");
  } catch {
    showcaseMode.value = false;
  }
}

async function enterShowcase() {
  loading.value = true;
  try {
    const result = await adminLogin("");
    clearStoredAdminPassword();
    authenticated.value = true;
    showcaseMode.value = Boolean(result.showcaseMode);
    adminMode.value = Boolean(result.adminMode);
    showAdminSwitch.value = false;
    await Promise.all([loadMarkdown(), loadHomeBriefing(), loadSiteStyle(), loadResumeConfig(), loadResumeAvatar(), loadVoiceReference()]);
    setStatus(result.message || showcaseNotice, "warning");
  } catch (error) {
    authenticated.value = false;
    setStatus(error.message, "error");
  } finally {
    loading.value = false;
  }
}

async function login() {
  if (!password.value.trim()) {
    setStatus("请输入修改密码。", "warning");
    return;
  }
  loading.value = true;
  try {
    const result = await adminLogin(password.value);
    setStoredAdminPassword(password.value);
    authenticated.value = true;
    showcaseMode.value = Boolean(result.showcaseMode);
    adminMode.value = Boolean(result.adminMode || !result.showcaseMode);
    showAdminSwitch.value = false;
    await Promise.all([loadMarkdown(), loadHomeBriefing(), loadSiteStyle(), loadResumeConfig(), loadResumeAvatar(), loadVoiceReference()]);
    setStatus(result.message, adminMode.value ? "success" : "warning");
  } catch (error) {
    clearStoredAdminPassword();
    authenticated.value = false;
    setStatus(error.message, "error");
  } finally {
    loading.value = false;
  }
}

async function switchToAdminMode() {
  const nextPassword = adminPasswordInput.value.trim();
  if (!nextPassword) {
    setStatus("请输入管理密码。", "warning");
    return;
  }
  adminModeLoading.value = true;
  try {
    const result = await adminLogin(nextPassword);
    if (!result.adminMode) {
      setStatus("管理密码不正确，仍处于体验模式。", "error");
      return;
    }
    setStoredAdminPassword(nextPassword);
    password.value = nextPassword;
    adminPasswordInput.value = "";
    adminMode.value = true;
    authenticated.value = true;
    showcaseMode.value = Boolean(result.showcaseMode);
    showAdminSwitch.value = false;
    await Promise.all([loadMarkdown(), loadHomeBriefing(), loadSiteStyle(), loadResumeConfig(), loadResumeAvatar(), loadVoiceReference()]);
    setStatus(result.message || "已切换到管理员模式。", "success");
  } catch (error) {
    clearStoredAdminPassword();
    adminMode.value = false;
    setStatus(`切换管理员模式失败：${error.message}`, "error");
  } finally {
    adminModeLoading.value = false;
  }
}

function logout() {
  clearStoredAdminPassword();
  password.value = "";
  adminPasswordInput.value = "";
  adminMode.value = false;
  showAdminSwitch.value = false;
  authenticated.value = false;
  markdown.value = "";
  documentPath.value = "";
  sectionCount.value = 0;
  homeBriefing.value = null;
  selectedStyleKey.value = publishedStyleKey.value;
  resumeConfigDirty.value = false;
  markdownDirty.value = false;
  homeDirty.value = false;
  clearResumeAvatarLocalPreview();
  clearThemePreview();
  if (recordedVoiceUrl.value) URL.revokeObjectURL(recordedVoiceUrl.value);
  setStatus("");
}

async function loadMarkdown() {
  loading.value = true;
  try {
    const result = await getMarkdownDocument(adminPassword.value);
    markdown.value = result.markdown;
    documentPath.value = result.path;
    sectionCount.value = result.sections;
    markdownDirty.value = false;
  } catch (error) {
    setStatus(`Markdown 加载失败：${error.message}`, "error");
  } finally {
    loading.value = false;
  }
}

async function saveMarkdown() {
  saving.value = true;
  try {
    const result = await saveMarkdownDocument(adminPassword.value, markdown.value);
    sectionCount.value = result.sections;
    markdownDirty.value = false;
    await loadHomeBriefing();
    setStatus(`${result.message} 如需更新公开首页，请切到“首页编排”并点击“基于当前 Markdown 重新生成首页”。`, "success");
  } catch (error) {
    setStatus(formatSaveError(error, "Markdown 保存"), "error");
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
    markdownDirty.value = true;
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

async function regenerateHomeFromMarkdown() {
  if (!markdown.value.trim()) return;
  homeRegenerating.value = true;
  try {
    const result = await previewMarkdownBriefing(adminPassword.value, markdown.value);
    homeBriefing.value = result;
    homeSaved.value = false;
    homeDirty.value = true;
    setStatus(
      result.aiConfigured ? "已基于当前 Markdown 重新生成首页草稿。" : "已基于当前 Markdown 生成本地首页草稿；后端未配置 DeepSeek API Key。",
      result.aiConfigured ? "success" : "warning",
    );
  } catch (error) {
    setStatus(`首页重新生成失败：${error.message}`, "error");
  } finally {
    homeRegenerating.value = false;
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
    setStatus(formatSaveError(error, "首页保存"), "error");
  } finally {
    homeSaving.value = false;
  }
}

async function loadSiteStyle() {
  try {
    const result = await getAdminSiteStyle(adminPassword.value);
    applyStylePayload(result);
    selectedStyleKey.value = result.activeKey;
    markPublishedStyle(result.activeKey);
  } catch (error) {
    setStatus(`视觉风格加载失败：${error.message}`, "error");
  }
}

function selectStyle(key) {
  selectedStyleKey.value = key;
  setTheme(key);
}

function resetStylePreview() {
  selectedStyleKey.value = publishedStyleKey.value;
  clearThemePreview();
  setStatus("已恢复到当前公开风格。", "info");
}

async function saveStyleDraft() {
  styleSaving.value = true;
  try {
    const result = await saveAdminSiteStyle(adminPassword.value, selectedStyleKey.value);
    applyStylePayload(result);
    markPublishedStyle(result.activeKey);
    selectedStyleKey.value = result.activeKey;
    setStatus("视觉风格已保存，公开页面将使用该预设。", "success");
  } catch (error) {
    setStatus(formatSaveError(error, "风格保存"), "error");
  } finally {
    styleSaving.value = false;
  }
}

async function loadResumeConfig() {
  resumeConfigLoading.value = true;
  try {
    resumeConfig.value = await getAdminResumeExportConfig(adminPassword.value);
    if (!resumeConfig.value.branding) {
      resumeConfig.value.branding = { enabled: true, githubUrl: "https://github.com/wuhuaha/resume-html", author: "王涛", text: "本简历由开源项目 Resume HTML 生成" };
    }
    resumeConfigDirty.value = false;
  } catch (error) {
    setStatus(`导出策略加载失败：${error.message}`, "error");
  } finally {
    resumeConfigLoading.value = false;
  }
}

function selectResumeMode(key) {
  resumeConfig.value.activeMode = key;
  resumeConfigDirty.value = true;
}

function selectResumeTemplate(key) {
  resumeConfig.value.activeTemplate = key;
  resumeConfigDirty.value = true;
}

function touchResumeConfig() {
  resumeConfigDirty.value = true;
}

async function saveResumeConfigDraft() {
  resumeConfigSaving.value = true;
  try {
    resumeConfig.value = await saveAdminResumeExportConfig(adminPassword.value, resumeConfig.value);
    resumeConfigDirty.value = false;
    setStatus("简历导出策略已保存。", "success");
  } catch (error) {
    setStatus(formatSaveError(error, "导出策略保存"), "error");
  } finally {
    resumeConfigSaving.value = false;
  }
}

async function loadResumeAvatar() {
  try {
    resumeAvatar.value = await getResumeAvatar(adminPassword.value);
  } catch (error) {
    setStatus(`简历头像读取失败：${error.message}`, "error");
  }
}

function selectResumeAvatarFile(event) {
  const selected = event.target.files?.[0] || null;
  clearResumeAvatarLocalPreview();
  resumeAvatarFile.value = selected;
  resumeAvatarFileName.value = selected?.name || "";
  if (selected) {
    try {
      validateResumeAvatarFile(selected);
      resumeAvatarLocalPreview.value = URL.createObjectURL(selected);
    } catch (error) {
      resumeAvatarFile.value = null;
      resumeAvatarFileName.value = "";
      setStatus(error.message, "error");
    }
  }
  event.target.value = "";
}

async function saveResumeAvatarFile() {
  if (!resumeAvatarFile.value) return;
  resumeAvatarSaving.value = true;
  try {
    validateResumeAvatarFile(resumeAvatarFile.value);
    resumeAvatar.value = await saveResumeAvatar(adminPassword.value, resumeAvatarFile.value, resumeAvatarFile.value.name || "resume-avatar.png");
    resumeAvatarFile.value = null;
    resumeAvatarFileName.value = "";
    clearResumeAvatarLocalPreview();
    setStatus("简历头像已保存，支持头像的模板导出时会使用。", "success");
  } catch (error) {
    setStatus(formatSaveError(error, "头像保存"), "error");
  } finally {
    resumeAvatarSaving.value = false;
  }
}

async function clearResumeAvatar() {
  try {
    resumeAvatarFile.value = null;
    resumeAvatarFileName.value = "";
    clearResumeAvatarLocalPreview();
    resumeAvatar.value = await deleteResumeAvatar(adminPassword.value);
    setStatus("简历头像已删除。", "success");
  } catch (error) {
    setStatus(formatSaveError(error, "头像删除"), "error");
  }
}

function validateResumeAvatarFile(file) {
  if (!["image/jpeg", "image/jpg", "image/png", "image/webp"].includes(file.type)) {
    throw new Error("简历头像只支持 JPG、PNG 或 WebP。");
  }
  if (file.size > 2 * 1024 * 1024) {
    throw new Error("头像文件不能超过 2 MB。");
  }
}

function clearResumeAvatarLocalPreview() {
  if (resumeAvatarLocalPreview.value) {
    URL.revokeObjectURL(resumeAvatarLocalPreview.value);
    resumeAvatarLocalPreview.value = "";
  }
}

async function loadVoiceReference() {
  voiceReferenceLoading.value = true;
  try {
    voiceReference.value = await getVoiceCloneReference(adminPassword.value);
    localVoiceReference.value = localStorage.getItem("ai-profile-voice-clone-reference") || "";
    localVoiceReferenceName.value = localStorage.getItem("ai-profile-voice-clone-reference-name") || "";
    localVoiceReferenceSize.value = Number(localStorage.getItem("ai-profile-voice-clone-reference-size") || 0);
  } catch (error) {
    setStatus(`音色读取失败：${error.message}`, "error");
  } finally {
    voiceReferenceLoading.value = false;
  }
}

function selectVoiceFile(event) {
  const selected = event.target.files?.[0] || null;
  voiceFile.value = selected;
  voiceFileName.value = selected?.name || "";
}

async function saveVoiceReferenceFromFile() {
  if (!voiceFile.value) return;
  voiceSaving.value = true;
  try {
    await saveVoiceReferenceBlob(voiceFile.value, voiceFile.value.name || "voice-reference.wav");
  } catch (error) {
    setStatus(`参考音色保存失败：${error.message}`, "error");
  } finally {
    voiceSaving.value = false;
  }
}

async function saveRecordedVoiceReference() {
  if (!recordedVoiceBlob.value) return;
  voiceSaving.value = true;
  try {
    await saveVoiceReferenceBlob(recordedVoiceBlob.value, "recorded-voice-reference.wav");
  } catch (error) {
    setStatus(`录音保存失败：${error.message}`, "error");
  } finally {
    voiceSaving.value = false;
  }
}

async function saveVoiceReferenceBlob(blob, filename) {
  const normalized = blob.type.includes("wav") ? blob : await convertBlobToWav(blob);
  validateVoiceReferenceBlob(normalized);
  if (showcaseMode.value && !adminMode.value) {
    const dataUrl = await blobToDataUrl(normalized);
    localStorage.setItem("ai-profile-voice-clone-reference", dataUrl);
    localStorage.setItem("ai-profile-voice-clone-reference-name", filename);
    localStorage.setItem("ai-profile-voice-clone-reference-size", String(normalized.size));
    localVoiceReference.value = dataUrl;
    localVoiceReferenceName.value = filename;
    localVoiceReferenceSize.value = normalized.size;
    setStatus("展示模式：参考音色已保存在当前浏览器，首页同一浏览器会使用该音色复刻。", "success");
    return;
  }
  voiceReference.value = await saveVoiceCloneReference(adminPassword.value, normalized, filename);
  setStatus("参考音色已保存，首页 TTS 将使用小米音色复刻。", "success");
}

async function clearVoiceReference() {
  try {
    localStorage.removeItem("ai-profile-voice-clone-reference");
    localStorage.removeItem("ai-profile-voice-clone-reference-name");
    localStorage.removeItem("ai-profile-voice-clone-reference-size");
    localVoiceReference.value = "";
    localVoiceReferenceName.value = "";
    localVoiceReferenceSize.value = 0;
    if (!showcaseMode.value || adminMode.value) {
      voiceReference.value = await deleteVoiceCloneReference(adminPassword.value);
    }
    setStatus("已恢复默认音色。", "success");
  } catch (error) {
    setStatus(`恢复默认音色失败：${error.message}`, "error");
  }
}

async function toggleVoiceReferenceRecording() {
  if (voiceRecording.value) {
    stopVoiceReferenceRecording();
    return;
  }
  await startVoiceReferenceRecording();
}

async function startVoiceReferenceRecording() {
  voiceRecordingBusy.value = true;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = chooseVoiceMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    voiceRecordingChunks.value = [];
    recorder.ondataavailable = (event) => {
      if (event.data?.size) voiceRecordingChunks.value.push(event.data);
    };
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      const blob = new Blob(voiceRecordingChunks.value, { type: mimeType || "audio/webm" });
      recordedVoiceBlob.value = await convertBlobToWav(blob);
      if (recordedVoiceUrl.value) URL.revokeObjectURL(recordedVoiceUrl.value);
      recordedVoiceUrl.value = URL.createObjectURL(recordedVoiceBlob.value);
      setStatus("录音已生成，可试听后点击“使用录音”。", "success");
    };
    voiceRecorder.value = recorder;
    recorder.start();
    voiceRecording.value = true;
    setStatus("正在录制参考音色，再次点击结束。", "info");
  } catch (error) {
    setStatus(`无法开始录音：${error.message}`, "error");
  } finally {
    voiceRecordingBusy.value = false;
  }
}

function stopVoiceReferenceRecording() {
  if (voiceRecorder.value && voiceRecorder.value.state !== "inactive") {
    voiceRecorder.value.stop();
  }
  voiceRecording.value = false;
}

function chooseVoiceMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((item) => MediaRecorder.isTypeSupported(item)) || "";
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

function validateVoiceReferenceBlob(blob) {
  if (!["audio/wav", "audio/mpeg", "audio/mp3"].includes(blob.type)) {
    throw new Error("参考音色只支持 WAV 或 MP3。");
  }
  if (Math.ceil(blob.size * 4 / 3) > 10 * 1024 * 1024) {
    throw new Error("参考音频过大：Base64 后不能超过 10 MB。");
  }
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("读取音频失败。"));
    reader.readAsDataURL(blob);
  });
}

function formatBytes(size) {
  if (!size) return "0 B";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}
</script>
