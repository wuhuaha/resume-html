# Configuration

项目的运行配置分为三类：后端环境变量、内容文件、前端构建变量。

## 后端环境变量

后端在 `backend` 目录读取 `.env`。从 `.env.example` 复制：

```powershell
cd backend
Copy-Item .env.example .env
```

关键变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 空 | 为空时 AI 能力降级。 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API base URL。 |
| `DEEPSEEK_CHAT_MODEL` | `deepseek-v4-flash` | 问答和后台编辑模型。 |
| `DEEPSEEK_EXPORT_MODEL` | `deepseek-v4-pro` | 简历导出模型。 |
| `ADMIN_PASSWORD` | `admin` | 后台密码，生产环境必须修改。 |
| `SHOWCASE_MODE` | `false` | 展示模式开关。 |
| `CONTENT_PATH` | `../content/profile.md` | Markdown 内容源。 |
| `HOME_BRIEFING_PATH` | `../content/home_briefing.json` | 首页编排配置。 |
| `SITE_STYLE_PATH` | `../content/site_style.json` | 视觉风格配置。 |
| `RESUME_EXPORT_CONFIG_PATH` | `../content/resume_export_config.json` | 简历导出策略。 |
| `RESUME_AVATAR_PATH` | `../storage/resume_avatar` | 简历导出头像资产路径。 |
| `PROJECT_GITHUB_URL` | `https://github.com/wuhuaha/resume-html` | 导出简历页脚展示的开源项目地址。 |
| `STATIC_DIR` | 空 | 前端静态文件目录。 |
| `FRONTEND_ORIGIN` | `http://127.0.0.1:4173` | CORS 允许的前端地址。 |
| `VOICE_CLONE_REFERENCE_PATH` | `../storage/voice_clone_reference` | 参考音色保存路径。 |

## 内容文件

### `content/profile.md`

事实资料库，包含个人信息、能力摘要、工作经历、项目经历、奖项证书等。AI 问答、首页 briefing 和简历导出都应以这份资料为事实边界。

### `content/home_briefing.json`

首页展示层配置。它可以由后端根据 `profile.md` 生成，也可以由管理员在后台生成和保存。

### `content/site_style.json`

视觉风格配置，目前通过 `activeKey` 选择内置风格预设。

### `content/resume_export_config.json`

简历导出策略配置。可控制：

- `activeMode`：默认篇幅策略，例如 ATS 一页纸、两页精简、完整匹配版。
- `activeTemplate`：默认样式模板。
- `modes`：目标页数、核心能力条数、经历 bullet 数、项目数量、字号、行高、页边距、是否保留出生日期、是否允许头像等。
- `templates`：模板名称、参考来源、布局、主色、字体、是否支持头像、是否显示开源页脚、LLM 生成策略。
- `branding`：导出简历底部开源项目说明，包括 GitHub 地址和作者。

当前内置模板参考了 JSON Resume 的主题生态、Reactive Resume 的布局/颜色/字体可配置理念、OpenResume 的 ATS 可读性，以及 RenderCV 的内容与版式分离思路。

### 简历头像

管理员可在后台上传 JPG、PNG 或 WebP 头像。头像保存到 `RESUME_AVATAR_PATH` 指向的 `storage/` 路径，不进入 Git。导出 HTML 时如果篇幅模式允许头像且当前模板支持头像，后端会把图片转成 data URL 内嵌到 HTML，便于离线打开。

## 前端环境变量

前端默认使用同源 API，开发时通过 Vite proxy 转发 `/api` 到 `127.0.0.1:8000`。

如需显式指定 API：

```env
VITE_API_BASE=https://your-api.example
```

## 配置优先级

- 运行时敏感配置放在 `backend/.env`。
- 可公开的展示内容和策略放在 `content/`。
- 前端构建期配置放在 `frontend/.env*`，但不要提交包含敏感信息的 env 文件。
