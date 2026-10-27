# agent-stack 子系统目录

这里存放主项目依赖的几个独立子服务。父目录已经从上游命名调整为 `agent-stack`，用于统一承载 AI、Agent、下载解析、签名、Cookie 桥接和爬虫引擎相关组件。

## 子目录

- `ai-agent-service/`
  AI 与 Agent 能力服务，包含内容提取、改写、TTS、数字人等能力。
- `download-service/`
  下载解析服务与配套 UI。
- `sign-service/`
  签名服务，供爬虫与下载服务调用。
- `cookie-bridge/`
  Cookie 桥接、浏览器扩展和账号授权辅助服务。
- `crawler-engine/`
  爬虫核心与 HTTP API。

## 使用原则

- 这些目录是并列子系统，不是一个单体应用。
- 修改前先确认你要动的是主后端逻辑，还是某个子服务自身。
- 启动、依赖和环境变量以各自目录下的 `README.md` 与启动脚本为准。
