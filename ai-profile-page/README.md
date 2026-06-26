# AI 个人能力介绍页

面向招聘方的公开个人介绍页。访客可以浏览能力摘要、项目经历和时间线，也可以通过文字或语音向 AI 助手提问，并根据岗位 JD 导出匹配版简历。

## 运行方式

### 后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

在 `backend/.env` 中配置：

```env
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-v4-flash
DEEPSEEK_EXPORT_MODEL=deepseek-v4-pro
ADMIN_PASSWORD=admin
```

未配置 API Key 时，公开页面仍可浏览，AI 问答和导出会使用本地资料给出保守兜底结果。

### 前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 4173
```

访问 `http://127.0.0.1:4173/`。

## 内容维护

主要内容位于 `content/profile.md`。作者后台 `/admin` 支持直接编辑 Markdown、上传 Word/PDF/Markdown 转草稿、保存后刷新资料索引。

后台修改密码由后端环境变量 `ADMIN_PASSWORD` 控制；不配置时默认是 `admin`。生产部署时应改成强密码，并保证 `backend/.env` 不进入 Git。
