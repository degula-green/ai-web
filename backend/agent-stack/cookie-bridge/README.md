# cookie-bridge

浏览器 Cookie 自动同步桥接服务，包含：

- `server/`：WebSocket + HTTP API 服务
- `extension/`：Chrome 扩展

## 作用

- 从浏览器自动提取多平台 Cookie
- 向后端提供统一的 Cookie 查询接口
- 给 `crawler-engine` 提供自动同步能力，减少手动维护账号池

## 启动

一键启动：

```bat
start.bat
```

手动启动：

```bat
cd server
uv sync
uv run app.py
```

## 扩展安装

在 Chrome 扩展管理页加载 `extension/` 目录即可。
