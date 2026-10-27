# download-service

下载解析服务，包含：

- `DownloadServer/`：Python 下载解析后端
- `DownloadUI/`：桌面端调试 UI

## 依赖

- Python 3.8+
- Node.js
- `sign-service`

## 启动

后端：

```bat
cd DownloadServer
python app.py
```

前端：

```bat
cd DownloadUI
npm install
npm run dev
```

## 说明

本目录是当前项目内部使用的下载子系统，文档和启动方式均以本仓库为准，不再使用上游仓库命名。
