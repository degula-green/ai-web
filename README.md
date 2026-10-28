# AI内容自动化

这是当前正在维护的主仓库，目标是把内容采集、文案处理、口播数字人、视频剪辑和平台运营能力收敛到一套可运行工程中。

## 仓库结构

- `backend/`
  主后端工程。包含 FastAPI 主服务、创作草稿、认证、上传、剪辑渲染，以及 `agent-stack` 相关子系统。
- `frontend/`
  当前在维护的 Vue 3 前端。`/creation/avatar` 等页面以这里为准。
- `docs/`
  项目文档、接口文档、数据库设计和历史设计材料。
- `scripts/`
  仓库级辅助脚本，包含 `start-all` / `stop-all` 一键启动与停止脚本。
- `dev_doc/`
  排障记录和阶段性方案文档。

## 当前主线

- 主后端入口：`backend/app`
- 主前端入口：`frontend/src`
- 口播数字人联调：
  `frontend/src/views/CreationAvatarView.vue`
  `backend/app/services/clip_render_service.py`
  `backend/agent-stack/ai-agent-service`

## 启动方式

### 一键启动（推荐）

前置条件：MySQL `3306`、Redis `6379`、MinIO `9000` 已启动。启动脚本不负责这三个基础设施，只做检测和提示。

```powershell
# 启动全部项目服务
scripts\start-all.bat

# 停止全部项目服务
scripts\stop-all.bat
```

也可以直接调用 PowerShell 脚本：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-all.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-all.ps1
```

### 启动顺序与端口

| 顺序 | 服务 | 端口 | 健康检查 |
|---:|---|---:|---|
| 1 | 主后端 | 8000 | `/api/v1/health` |
| 2 | 签名服务 | 8989 | `/signsrv/pong` |
| 3 | DownloadServer | 8205 | `/ping` |
| 4 | 爬虫引擎 | 8005 | `/openapi.json` |
| 5 | Agent 后端 | 8002 | `/health` |
| 6 | CookieBridge | 8274 | `/ping` |
| 7 | 主前端 | 5173 | `/` |
| 8 | Agent 前端 | 5374 | `/` |

顺序有依赖关系，不能随意调整：

- `8989` 必须先于 `8205` 和 `8005`
- `8205` 必须先于 `8002`（`8002` 启动时会 ping `8205`，失败会退出）
- 主后端不会自动拉起 `8005`，必须由脚本或手动启动

### 可选参数

```text
scripts\start-all.bat -SkipFrontend       # 只启动后端，不启动两个前端
scripts\start-all.bat -SkipCrawler        # 跳过爬虫引擎 8005
scripts\start-all.bat -SkipCookieBridge   # 跳过 CookieBridge 8274
```

### 启动脚本行为

- 已在运行的端口自动跳过，可重复执行，不会重复起进程
- 每个服务启动后轮询健康检查，超时即判定失败
- 日志写入 `.tmp\runlogs\<服务名>.out.log` 与 `.err.log`
- 有失败项时打印日志路径，并以非 0 退出码结束
- PID 记录在 `.tmp\runlogs\pids.json`

### 停止脚本行为

- 优先按 `pids.json` 记录的 PID 停止，找不到时按端口兜底
- 只停止本项目 8 个端口，不会全局 `taskkill python.exe` / `node.exe`
- 停止后复核端口，仍有残留时返回非 0
- 保留 MySQL、Redis、MinIO 不动

### 访问地址

- 主前端：`http://localhost:5173`
- Agent 前端：`http://localhost:5374`
- 主后端：`http://127.0.0.1:8000`
- Agent 后端：`http://127.0.0.1:8002`

### 手动启动（单服务调试）

脚本不会自动安装依赖。首次部署或依赖变更后，先在各子目录执行一次：

```powershell
# 主后端
cd backend
uv sync --python 3.12

# 主前端
cd frontend
npm install

# 爬虫引擎
cd backend\agent-stack\crawler-engine
uv sync --python 3.12
```

单独启动主后端：

```powershell
cd backend
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

单独启动主前端：

```powershell
cd frontend
npm run dev -- --host localhost --port 5173
```

其余服务（`8989`、`8205`、`8005`、`8002`、`8274`、`5374`）的单独启动命令见 `agent.md` 第 5 节。

## 清理原则

- `backend/tests/`、`backend/app/**` 下的正式测试和业务代码默认保留。
- `dev_doc/`、`docs/source_materials/` 下的阶段方案与参考材料只作记录，不参与运行。
- 临时日志、锁文件、截图、手工调试脚本在确认无业务价值后直接清理。
- 目录说明优先维护在各目录自己的 `README.md` 中，避免信息只留在聊天记录里。

## 本轮整理范围

- 更新顶层和主要目录说明文档。
- 清理明显无效的临时文件和历史残留。
- 不主动删除仍可能用于回归验证的正式测试目录。
