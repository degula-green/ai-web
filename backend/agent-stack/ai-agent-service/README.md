# ai-agent-service

AI 与 Agent 能力服务，负责内容提取、改写、TTS、数字人、SSE 对话与相关前后端联调。

## 目录

- `backend/`
  Python API 服务与 Agent 能力实现。
- `frontend/`
  前端调试界面。
- `docs/`
  本子系统的架构、部署和产品说明。

## 本地依赖

- Python 3.10 - 3.12
- `uv`
- Node.js
- MySQL
- `ffmpeg`
- 同级目录下的 `../download-service`
- 同级目录下的 `../sign-service`

## 启动

后端：

```bat
cd backend
uv sync --python 3.12 --no-editable
uv run --python 3.12 --no-editable --no-sync python -m uvicorn api.main:app --host 0.0.0.0 --port 8002
```

前端：

```bat
cd frontend
npm install
npm run dev
```

## Docker

`docker-compose.yml` 默认通过相对路径引用同级目录下的 `download-service` 和 `sign-service`。
