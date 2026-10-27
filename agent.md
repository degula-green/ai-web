# AI-Content-Automation 本机运行说明

> 更新时间：2026-10-26
> 适用机器：Windows  
> 项目根目录：`D:\python\code\AI-Content-Automation-main`

本文记录当前机器上已经验证过的启动方式、端口、依赖关系和模块可用状态。  
不要直接套用旧文档中的 `E:\AI内容自动化` 路径。

---

## 1. 当前结论

当前项目由主应用和多个独立子服务组成，不是单体应用。

已验证可用：

- 主后端 `8000`
- 主前端 `5173`
- AI Agent 后端 `8002`（基础服务、LLM 对话、TTS）
- DownloadServer `8205`（服务可启动）
- CookieBridge `8274`（服务和扩展可用）
- TTS 口播音频生成与浏览器试听
- MinIO 本地上传和本地访问
- `sign-service` `8989`（JS 签名，依赖 Node.js）
- `crawler-engine` `8005`（已还原，需手动启动）

当前缺失或受限：

- 抖音、小红书等内容获取链路已具备签名能力，仍受有效 Cookie 限制
- 数字人接口已存在，但 RunningHub / DashScope 需要公网可访问的图片、音频、视频 URL
- 多模态模特图分析依赖支持多模态的激活配置，当前未满足
- 发布 runtime 仍是占位实现

---

## 2. 目录与入口

| 模块 | 目录 | 入口 |
|---|---|---|
| 主后端 | `backend` | `app.main:app` |
| 主前端 | `frontend` | Vue 3 + Vite |
| Agent 后端 | `backend\agent-stack\ai-agent-service\backend` | `api.main:app` |
| Agent 前端 | `backend\agent-stack\ai-agent-service\frontend` | React + Vite |
| DownloadServer | `backend\agent-stack\download-service\DownloadServer` | `app.py` |
| CookieBridge | `backend\agent-stack\cookie-bridge` | `start.bat` 或 `server\app.py` |
| 签名服务 | `backend\agent-stack\sign-service` | `app.py`（Tornado，JS 签名） |
| 爬虫引擎 | `backend\agent-stack\crawler-engine` | `api_server.py`（FastAPI，8005） |

---

## 3. 端口与访问地址

| 服务 | 端口 | 地址 | 说明 |
|---|---:|---|---|
| MySQL | 3306 | `127.0.0.1:3306` | 主库 `ai_content_automation` |
| Redis | 6379 | `127.0.0.1:6379` | 主后端依赖 |
| MinIO API | 9000 | `127.0.0.1:9000` | 桶 `ai-content-assets` |
| 主后端 | 8000 | `http://127.0.0.1:8000` | FastAPI |
| Agent 后端 | 8002 | `http://127.0.0.1:8002` | FastAPI |
| 主前端 | 5173 | `http://localhost:5173` | Vue 3 |
| Agent 前端 | 5374 | `http://localhost:5374` | React |
| DownloadServer | 8205 | `http://127.0.0.1:8205` | Tornado |
| CookieBridge | 8274 | `http://127.0.0.1:8274` | Tornado + WebSocket |
| 爬虫引擎 | 8005 | `http://127.0.0.1:8005` | FastAPI，需独立启动 |
| 签名服务 | 8989 | `http://127.0.0.1:8989` | Tornado + Node.js 签名 |

### 前端访问注意

Vite 当前实际监听在 `::1`，因此使用：

```text
http://localhost:5173
http://localhost:5374
```

不要使用：

```text
http://127.0.0.1:5173
http://127.0.0.1:5374
```

除非明确把 Vite 改为监听 `127.0.0.1` 或 `0.0.0.0`。

---

## 4. 启动前依赖

### 4.1 基础软件

确保以下程序已经启动或可用：

- MySQL 8.0
- Redis
- MinIO
- Python 3.12
- `uv`
- Node.js 与 npm（签名服务要求 Node.js >= 16，抖音 `a_bogus` 依赖它）
- ffmpeg（视频处理需要）

### 4.2 环境文件

主后端：

```text
D:\python\code\AI-Content-Automation-main\backend\.env
```

Agent 后端：

```text
D:\python\code\AI-Content-Automation-main\backend\agent-stack\ai-agent-service\.env
```

注意：Agent 后端的 `.env` 在 `ai-agent-service` 根目录，不在 `backend` 子目录。

### 4.3 关键配置

主后端 `backend\.env` 至少需要：

```ini
APP_HOST=0.0.0.0
APP_PORT=8000
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=<本机 MySQL 密码>
MYSQL_DATABASE=ai_content_automation
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_BUCKET=ai-content-assets
AUTH_JWT_SECRET=<与 Agent 侧一致的密钥>
```

Agent `.env` 至少需要：

```ini
AGENT_DB_HOST=localhost
AGENT_DB_PORT=3306
AGENT_DB_USER=root
AGENT_DB_PASSWORD=<本机 MySQL 密码>
AGENT_DB_NAME=ai_content_automation
DOWNLOAD_SERVER_BASE=http://127.0.0.1:8205
DOWNLOAD_SERVER_TIMEOUT=60
USE_MOCK=false
```

重要：

- 主后端和 Agent 后端必须使用同一个 JWT 密钥。
- Agent 端代码读取的变量名是 `AUTH_JWT_SECRET`。
- 不要把真实 Key 写进本文档或提交到 Git。

### 4.4 模型和供应商配置

聊天模型、TTS、数字人配置存放于数据库表 `llm_configs`，不是全部写在 `.env` 中。

当前已存在的主要配置：

| `config_name` | 用途 |
|---|---|
| `ds` | DeepSeek 聊天 |
| `bailian-qwen` | 通义千问，多模态能力已标记 |
| `cosyvoice-v3-flash` | CosyVoice 系统音色 TTS |
| `cosyvoice-v3.5-plus` | CosyVoice TTS |
| `voice-enrollment` | 声音复刻 / 声音设计 |
| `wan2.2-s2v` | RunningHub 图片数字人 |
| `videoretalk` | DashScope VideoRetalk |

注意：

- 模型下拉列表会读取整张 `llm_configs` 表，因此会同时出现 TTS 和数字人配置。
- 不是每个配置都能作为聊天模型使用。
- 数字人和 TTS 通过 `config_name` 独立取配置，不依赖当前激活的聊天模型。
- 当前激活聊天配置是 `ds`，它不支持多模态。

---

## 5. 正确启动顺序

建议按以下顺序启动，每一项使用独立终端。

### 第 0 步：启动基础设施

先确认：

```text
MySQL  3306
Redis  6379
MinIO  9000
```

### 第 1 步：启动主后端 8000

```powershell
cd D:\python\code\AI-Content-Automation-main\backend
uv sync --python 3.12
uv run --python 3.12 --no-sync python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：

```powershell
curl.exe http://127.0.0.1:8000/api/v1/health
```

### 第 2 步：启动签名服务 8989

抖音、小红书、B 站的平台请求带有反爬签名参数。签名服务缺失时 DownloadServer 能启动，但内容详情会在 Cookie 登录态校验或详情接口阶段失败。

依赖：Python 3.12、Node.js >= 16。抖音默认走 `PyExecJS -> Node -> pkg/js/douyin.js`，不需要启动浏览器。

首次部署或 `.venv` 丢失时先安装依赖：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\sign-service
uv sync --python 3.12
```

启动：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\sign-service
$env:APP_PORT = "8989"
$env:APP_ADDRESS = "127.0.0.1"
$env:SIGN_TYPE = "javascript"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv run --python 3.12 python app.py
```

注意：

- 必须在 `sign-service` 目录下启动，因为 `pkg/js/douyin.js` 按相对路径加载。
- 主后端当前不会自动拉起签名服务，需要单独启动。
- 只监听 `127.0.0.1`，不要暴露到公网。
- Windows 控制台默认 GBK 时，启动日志中的 `⚠` 会触发 `UnicodeEncodeError`。启动前必须设置 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`。

验证：

```powershell
curl.exe http://127.0.0.1:8989/signsrv/pong
```

期望返回：

```json
{"biz_code":0,"msg":"OK!","isok":true,"data":{"message":"pong"}}
```

抖音签名接口验证：

```powershell
$body = @{
  uri = "/aweme/v1/web/aweme/detail/"
  query_params = "aweme_id=7618889733136744496&device_platform=webapp&aid=6383"
  user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
  cookies = "<当前 dy cookies>"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8989/signsrv/v1/douyin/sign" -Method Post -ContentType "application/json" -Body $body
```

期望 `isok=true` 且 `data.a_bogus` 非空。


### 第 3 步：启动 DownloadServer 8205

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\download-service\DownloadServer
.\.venv\Scripts\python.exe app.py
```

如果 `.venv` 不存在：

```powershell
uv sync --python 3.12
uv run python app.py
```

验证：

```powershell
curl.exe http://127.0.0.1:8205/ping
```

说明：

- `/ping` 正常只代表 DownloadServer 进程活着。
- 抖音、小红书内容详情还需要 `sign-service:8989` 和有效 Cookie。

### 第 4 步：启动 Agent 后端 8002

必须在 DownloadServer `8205` 已启动后执行，因为 Agent 启动时会 ping DownloadServer。若需要分析抖音等链接，还要先启动 `sign-service:8989`。

说明：8002 启动时只强依赖 8205；8989 缺失不会阻止 8002 启动，但内容获取会失败。

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\ai-agent-service\backend
uv sync --no-editable
uv run --no-editable python -m uvicorn api.main:app --host 0.0.0.0 --port 8002
```

说明：

- 本模块的 `backend\.python-version` 为 `3.11`，`pyproject.toml` 声明 `>=3.10,<3.13`，因此**不要**给 `uv` 传 `--python 3.12`，否则会出现环境不一致警告。
- 不传 `--python` 时，`uv` 会自动读取 `.python-version`（3.11）。
- 不要加 `--no-sync`，避免“环境版本不匹配但仍继续运行”的隐式行为。
- 首次启动或依赖变更后执行一次 `uv sync --no-editable` 即可。

验证：

```powershell
curl.exe http://127.0.0.1:8002/health
```

如果 8002 启动后立即退出，优先检查：

1. `8205` 是否可访问
2. Agent `.env` 的数据库配置
3. `AUTH_JWT_SECRET` 是否可读取

### 第 5 步：启动 CookieBridge 8274，可选

需要自动同步浏览器 Cookie 时启动：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\cookie-bridge
.\start.bat
```

或手动启动：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\cookie-bridge\server
uv sync
uv run app.py
```

验证：

```powershell
curl.exe http://127.0.0.1:8274/ping
curl.exe http://127.0.0.1:8274/api/status
```

浏览器扩展需在 Chrome 扩展管理页加载：

```text
backend\agent-stack\cookie-bridge\extension
```

### 第 6 步：启动主前端 5173

```powershell
cd D:\python\code\AI-Content-Automation-main\frontend
npm install
npm run dev -- --host localhost --port 5173
```

访问：

```text
http://localhost:5173
```

### 第 7 步：启动 Agent 前端 5374，可选

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\ai-agent-service\frontend
npm install
npm run dev
```

访问：

```text
http://localhost:5374
```

Agent 前端代理关系：

```text
/api/v1/auth          -> 8000
/api/v1/remix         -> 8002
/api/v1/llm-config    -> 8002
/api/v1/insight-modes -> 8002
/assets               -> 8002
/media                -> 8002
```

---

### 第 8 步：启动爬虫引擎 8005

`crawler-engine` 是独立子服务，主后端**不会**自动拉起它（`lifecycle.py` 中 `media_crawler_service.startup()` 已被注释）。必须手动启动。

首次部署先装依赖：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\crawler-engine
uv sync --python 3.12
```

启动：

```powershell
cd D:\python\code\AI-Content-Automation-main\backend\agent-stack\crawler-engine
uv run python api_server.py
```

验证：

```powershell
curl.exe http://127.0.0.1:8005/openapi.json
```

期望返回 200。

**启动注意事项（重要）**：

1. **必须使用该目录自己的 `.venv`**。它依赖 `httpx==0.28.1`、`pydantic==2.5.2`，与 DownloadServer 的 `httpx==0.24.0` 冲突，不能共用一个环境。

2. **必须在 `crawler-engine` 目录下启动**。`api_server.py` 用 `Path(__file__).parent` 定位 `main.py`，配置与 `data/` 目录也是相对路径。

3. **数据库/Redis 连接由 `api_server.py` 自动从 `backend/.env` 兜底注入**：

   ```text
   MYSQL_HOST     -> RELATION_DB_HOST
   MYSQL_PORT     -> RELATION_DB_PORT
   MYSQL_USER     -> RELATION_DB_USER
   MYSQL_PASSWORD -> RELATION_DB_PWD
   MYSQL_DATABASE -> RELATION_DB_NAME
   REDIS_HOST     -> REDIS_DB_HOST
   REDIS_PORT     -> REDIS_DB_PORT
   REDIS_PASSWORD -> REDIS_DB_PWD
   REDIS_DB       -> REDIS_DB_NUM
   ```

   即使主后端没传 `env_overrides`，也能连对库。

4. **`backend/.env` 里的空密码必须按“空值”处理**。本机 Redis 无密码；若跳过空值，会回退到爬虫默认密码 `123456`，启动后报：

   ```text
   保存检查点失败: Client sent AUTH, but no password is set
   ```

5. **`CHECKPOINT_STORAGE_TYPE` 必须是 `redis`**。`config/base_config.py` 已改为：

   ```python
   CHECKPOINT_STORAGE_TYPE = os.getenv("CHECKPOINT_STORAGE_TYPE", "redis")
   ```

   主后端只从 Redis 读取 checkpoint（`checkpoint:{platform}:{mode}:{id}`）。若为 `file`，爬虫写本地 JSON，主后端读不到，前端显示 0 条。

6. **checkpoint id 必须固定**。`api_server.py` 通过 `CRAWLER_FIXED_CHECKPOINT_ID` 固定子进程写入的 id，保证返回给主后端的 `checkpoint_id` 与实际写入 Redis 的 key 一致。

7. **签名服务 8989 必须先启动**。爬虫调用平台接口需要 `a_bogus` / `w_rid` 等签名。

8. **Cookie 账号池使用 `crawler_cookies_account` 表**。默认 `ACCOUNT_POOL_SAVE_TYPE=mysql`，主后端传 `crawler_cookie_account_id` 后精确取号。当前可用：

   ```text
   dy:   id=1, id=3
   bili: id=2, id=4
   ```

   小红书/快手当前无可用 Cookie。

9. **首次启动会做数据库兼容修复**，可能触发 `ALTER TABLE` 与数据清理（`creator_hash` 回填、昵称脱敏）。属爬虫自身行为，不要中途中断。

10. **修改 `crawler-engine` 代码后必须重启 8005**，否则改动不生效。

---

## 6. 关于爬虫引擎的边界

`crawler-engine` 已还原并可用，但需注意边界：

- 它**不在** AI 单链接解析链路上。`8002 -> 8205 -> 8989` 不依赖它。
- 只有主后端的**任务化爬虫**（关键词搜索、创作者采集、链接详情采集）需要它。
- 未启动 8005 时，主后端任务提交会失败，但 AI 对话式解析不受影响。

---


## 7. 模块可用状态

### 7.1 已验证可用

| 模块 | 状态 | 说明 |
|---|---|---|
| 主后端 8000 | 可用 | 认证、草稿、上传、平台账号等主业务接口 |
| 主前端 5173 | 可用 | Vue 3 创作台 |
| Agent 后端 8002 | 可用 | 基础服务、LLM 对话、TTS |
| Agent 前端 5374 | 可用 | Agent 调试界面 |
| DownloadServer 8205 | 可启动 | 进程健康检查可用 |
| CookieBridge 8274 | 可用 | 扩展 WebSocket 和 Cookie 查询 |
| 签名服务 8989 | 可用 | `/signsrv/pong` 正常，抖音 `a_bogus` 可生成 |
| TTS 音色列表 | 可用 | 系统音色可读取 |
| TTS 口播音频生成 | 可用 | 生成 MP3，本地文件落盘，浏览器可试听 |
| MinIO 本地上传 | 可用 | 上传票据和本地对象访问可用 |

### 7.2 TTS 已验证细节

接口：

```text
POST http://127.0.0.1:8002/api/v1/tts/generate
```

已验证结果：

- DashScope 返回 `audio_url`
- 服务将音频落盘到 `backend\agent-stack\ai-agent-service\backend\data\assets\tts\generated`
- 前端上传到 MinIO 后写入 `generatedAudioUrl`
- 浏览器 `<audio>` 可以正常播放

查看音色：

```powershell
curl.exe "http://127.0.0.1:8002/api/v1/tts/voices?page=1&page_size=10&status=enabled"
```

生成测试音频：

```powershell
$body = @{
  voice_asset_id = 1
  text = "这是一段数字人口播测试。"
  audio_format = "mp3"
  tts_config_name = "cosyvoice-v3-flash"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8002/api/v1/tts/generate" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

返回重点：

- `data.audio_url`：DashScope 临时地址
- `data.local_audio_url`：8002 的 `/media/...` 地址
- `data.record_id`：TTS 生成记录 ID

音频播放优先使用前端上传到 MinIO 后的 URL，不要长期依赖供应商临时签名 URL。

### 7.3 部分可用

| 模块 | 状态 | 限制 |
|---|---|---|
| LLM 对话 | 可用 | 当前激活配置为 `ds` |
| 内容链接分析 | 部分可用 | 签名服务已通，当前 Cookie 被抖音风控拒绝 |
| 图片数字人 `wan2.2-s2v` | 接口可用 | 真实出片依赖公网图片和音频 URL |
| VideoRetalk | 接口可用 | 真实出片依赖公网视频和音频 URL |
| 模特图 gallery | 受限 | 依赖 RunningHub 和多模态分析 |
| 平台账号 / Cookie 同步 | 部分可用 | 需要扩展绑定和有效 Cookie |

### 7.4 当前不可用或未完成

| 模块 | 状态 | 原因 |
|---|---|---|
| 抖音 / 小红书内容获取 | 部分可用 | 签名服务已通，当前 Cookie 被平台风控拒绝（Uifid Not Found） |
| 爬虫任务 API 8005 | 可用 | 需手动启动，见第 5 节第 8 步 |
| 发布 runtime | 占位 | 发布链路未完成 |
| 多模态模特图分析 | 当前不可用 | `MULTIMODAL_ENABLED=false`，激活的 `ds` 不支持多模态 |

---

## 8. 数字人使用条件

数字人接口：

```text
POST /api/v1/digital-human/s2v/submit
POST /api/v1/digital-human/videoretalk/submit
GET  /api/v1/digital-human/s2v/tasks/{task_id}
GET  /api/v1/digital-human/videoretalk/tasks/{task_id}
```

配置检查：

```powershell
curl.exe http://127.0.0.1:8002/api/v1/llm-config
```

应确认：

```text
wan2.2-s2v  has_api_key=true
videoretalk has_api_key=true
```

无成本连通性检查：

```powershell
curl.exe "http://127.0.0.1:8002/api/v1/digital-human/s2v/tasks/123456789?config_name=wan2.2-s2v"
```

返回 `errorCode=1004` 或“任务不存在”说明 RunningHub 鉴权已通。

```powershell
curl.exe "http://127.0.0.1:8002/api/v1/digital-human/videoretalk/tasks/123456789?config_name=videoretalk"
```

返回 `task_status=UNKNOWN` 说明 DashScope 鉴权已通。

### 重要限制

数字人云服务不能读取你本机的：

```text
http://127.0.0.1:9000/...
http://localhost:9000/...
```

MinIO 当前返回的是本地地址，浏览器可以访问，但 RunningHub / DashScope 在云端访问不到。

要真正生成数字人视频，必须：

1. MinIO 桶 `ai-content-assets` 保持 public read
2. 图片、音频、视频具备公网可访问 URL
3. 将公网 URL 传给数字人接口

仅把 MinIO 桶设为 public 不够，还需要公网域名、反向代理或隧道。

### 检测接口说明

`s2v/detect` 当前是本地占位检测：

```text
POST /api/v1/digital-human/s2v/detect
```

它会直接返回：

```json
{"check_pass": true, "skipped": true}
```

这不代表图片真的通过人脸检测，不要把它当作质量校验。

---

## 9. 健康检查清单

```powershell
curl.exe http://127.0.0.1:8000/api/v1/health
curl.exe http://127.0.0.1:8205/ping
curl.exe http://127.0.0.1:8989/signsrv/pong
curl.exe http://127.0.0.1:8002/health
curl.exe http://127.0.0.1:8274/ping
```

前端：

```text
http://localhost:5173
http://localhost:5374
```

MinIO：

```text
http://127.0.0.1:9000
```

---

## 10. 常见问题

### 内容获取返回 500 且日志提示 8989 连接失败

先确认签名服务：

    curl.exe http://127.0.0.1:8989/signsrv/pong

如果连接被拒绝：

1. 确认已在 backend\agent-stack\sign-service 目录启动 app.py
2. 确认 8989 未被其它进程占用
3. 确认 SIGN_SRV_HOST / SIGN_SRV_PORT 与 DownloadServer 配置一致

如果 pong 正常但内容仍失败，检查：

1. /signsrv/v1/douyin/sign 是否能返回非空 a_bogus
2. 8205 日志中的具体平台错误
3. Cookie 是否有效、是否与请求 User-Agent 匹配

### 内容获取返回 Blocked by ArgusSecurityPlugin

错误：

    Blocked by ArgusSecurityPlugin Uifid Not Found

这类错误来自抖音平台侧风控，不是签名服务故障。优先处理：

1. 重新完成抖音账号授权，刷新 Cookie
2. 授权浏览器与 DOUYIN_FIXED_USER_AGENT 的 UA 尽量一致
3. 确认 Cookie 中 sessionid、ttwid、UIFID 均存在


### 8002 启动失败

先检查 8205：

```powershell
curl.exe http://127.0.0.1:8205/ping
```

Agent 启动时会调用 DownloadServer 的 `/ping`，失败会主动退出。

### 内容获取返回 biz_code=2

错误：

```json
{"biz_code":2,"msg":"异常! 检查cookies登录态失败。","isok":false}
```

优先检查：

1. `sign-service:8989` 是否可用
2. `platform_accounts` / `platform_account_sessions` 里是否有当前用户的有效 Cookie
3. CookieBridge 扩展是否已经绑定到当前用户
4. 是否误用了测试账号的 `sessionid=fresh-token`

### 数字人提交失败

优先检查：

1. `image_url`、`audio_url` 是否是公网地址
2. 地址能否被外部网络直接 GET
3. RunningHub 或 DashScope 的 Key 是否有效
4. `llm_configs` 中对应配置是否存在且 `has_api_key=true`

### 音频听不了

检查顺序：

1. TTS 生成记录状态是否为 `success`
2. `data.local_audio_url` 对应文件是否存在
3. 前端最终使用的是 MinIO URL，不是供应商临时 URL
4. MinIO 对象 URL 是否返回 `200`，Content-Type 是否为 `audio/mpeg`
5. 浏览器开发者工具 Network 中 `<audio>` 请求是否被 CORS 或 403 拦截

当前已验证音频可以正常播放。

### 模型下拉出现 TTS / 数字人配置

这是前端直接展示整张 `llm_configs` 表导致的，不代表这些配置都能用于聊天。

聊天只使用当前激活的聊天配置，当前为：

```text
ds
```

---

## 11. 维护约定

- 启动命令以本文档为准，旧文档中的 `E:\AI内容自动化` 路径已过时。
- `crawler-engine` 必须手动启动（主后端不会自动拉起），未启动时任务化采集不可用。
- 修改 `crawler-engine` 后要重启 8005，否则改动不生效。
- 新增服务后，先更新端口表、健康检查项和模块状态表。
- 不把 API Key、密码、Cookie、JWT 密钥写入本文档。
- 每次验证后更新“更新时间”和对应模块状态。
