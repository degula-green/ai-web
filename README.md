# AI内容自动化

这是当前正在维护的主仓库，目标是把内容采集、文案处理、口播数字人、视频剪辑和平台运营能力收敛到一套可运行工程中。

## 仓库结构

- `backend/`
  主后端工程。包含 FastAPI 主服务、创作草稿、认证、上传、剪辑渲染，以及 `agent-stack` 相关子系统。
- `frontend/`
  当前在维护的 Vue 3 前端。`/creation/avatar` 等页面以这里为准。
- `docs/`
  项目文档、接口文档、数据库设计和历史设计材料。
- `legacy/`
  旧原型、外部参考仓库、章节式实验代码和历史产物。默认只读，不作为当前开发入口。

## 当前主线

- 主后端入口：`backend/app`
- 主前端入口：`frontend/src`
- 口播数字人联调：
  `frontend/src/views/CreationAvatarView.vue`
  `backend/app/services/clip_render_service.py`
  `backend/agent-stack/ai-agent-service`

## 启动方式

### 后端

```powershell
cd backend
uv sync
uv run python -m uvicorn app.main:app --reload
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

默认开发地址：

- 前端：`http://localhost:5173`
- 主后端：`http://localhost:8000`

## 清理原则

- `backend/tests/`、`backend/app/**` 下的正式测试和业务代码默认保留。
- `legacy/` 下的实验脚本、外部镜像和历史测试优先视为归档，不参与当前主线开发。
- 临时日志、锁文件、截图、手工调试脚本在确认无业务价值后直接清理。
- 目录说明优先维护在各目录自己的 `README.md` 中，避免信息只留在聊天记录里。

## 本轮整理范围

- 更新顶层和主要目录说明文档。
- 清理明显无效的临时文件和历史残留。
- 不主动删除仍可能用于回归验证的正式测试目录。
