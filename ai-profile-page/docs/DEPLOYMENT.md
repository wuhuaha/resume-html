# Deployment

本文档记录一种简单、可维护的生产部署方式：前端构建为静态文件，FastAPI 同时提供 API 和静态页面，由 systemd 管理进程，并在外层用 Nginx 或云服务器安全组暴露 80/443。

## 构建前端

```powershell
cd frontend
npm ci
npm run build
```

构建产物位于 `frontend/dist`。

## 准备后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=
ADMIN_PASSWORD=change-me
SHOWCASE_MODE=false
STATIC_DIR=../frontend/dist
FRONTEND_ORIGIN=https://your-domain.example
```

如果需要语音能力，再填写小米 MiMo 相关配置：

```env
XIAOMI_MIMO_API_KEY=
XIAOMI_MIMO_ASR_MODEL=mimo-v2.5-asr
XIAOMI_MIMO_TTS_MODEL=mimo-v2.5-tts
XIAOMI_MIMO_TTS_VOICECLONE_MODEL=mimo-v2.5-tts-voiceclone
```

## 启动服务

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

如果 `STATIC_DIR` 指向 `frontend/dist`，访问后端根路径即可打开前端页面。

## systemd 示例

```ini
[Unit]
Description=AI Profile Page
After=network.target

[Service]
WorkingDirectory=/opt/ai-profile-page/backend
Environment=PATH=/opt/ai-profile-page/backend/.venv/bin
ExecStart=/opt/ai-profile-page/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## Nginx 示例

```nginx
server {
    listen 80;
    server_name your-domain.example;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

生产环境建议开启 HTTPS。浏览器在非安全上下文下可能禁止麦克风，导致语音输入不可用。

## 展示模式部署

如果只是公开演示后台体验：

```env
SHOWCASE_MODE=true
```

展示模式会免管理密码，但所有保存类接口都会返回失败提示，不会写入公开首页或线上内容。
