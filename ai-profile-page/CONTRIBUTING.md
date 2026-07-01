# Contributing

感谢你愿意改进 AI Profile Page。这个项目的核心原则是：内容事实可追溯、交互对招聘方友好、默认配置不泄露隐私。

## 开发流程

1. Fork 仓库并创建功能分支。
2. 按 README 完成本地后端和前端启动。
3. 保持改动聚焦，避免把个人数据、密钥、部署产物提交到仓库。
4. 提交前至少运行：

```powershell
cd frontend
npm run build

cd ..\backend
python -m compileall app
```

## 代码约定

- 前端遵循现有 Vue 组件和 CSS 组织方式。
- 后端保持 FastAPI 路由、Pydantic schema、业务模块分离。
- 文档和示例配置只能使用占位值，不能出现真实 API Key、密码、服务器凭据或个人敏感信息。
- AI 相关提示词应约束事实边界，不能引导模型编造经历、成果、数字或公司信息。

## Pull Request 建议

请在 PR 中说明：

- 改动目的。
- 影响的页面或 API。
- 已运行的验证命令。
- 如涉及 UI，请附桌面端和移动端截图。

## 内容贡献

`content/profile.md` 是示例个人资料。发布自己的版本前，请替换为自己的事实资料，并确认没有泄露不应公开的联系方式、内部项目细节或客户敏感信息。
