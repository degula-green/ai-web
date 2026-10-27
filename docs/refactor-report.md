# 仓库重构记录

## 1. 仓库现状分析

### 当前目录问题

- 顶层同时混放正式代码、原型页面、外部仓库、压缩包、设计稿和测试输出。
- 后端工程入口缺失，没有统一的 API、Service、Repository、AI、Adapter 分层。
- AI 能力散落在脚本与测试目录中，无法承接长期迭代。

### 代码混杂情况

- `frontend-vue3-refactor/`: 当前 Vue 3 前端工作目录，可继续演进。
- `Tiktok/`: 抖音采集、解析、知识库、Memory、发布等原型与验证脚本。
- `MediaCrawler-main/`: 第三方抓取基础仓。
- `DailyHotApi-master/`: 热榜聚合参考仓。
- `业务模块原件/`: 章节式样例、参考实现和资料集合。
- `图文原件/`: PRD、架构图、UI 设计稿。
- `pages/`: HTML 原型页。

### AI 相关缺失点

- 缺少统一 Prompt 目录与版本边界。
- 缺少统一 Model Router。
- 缺少任务级 Memory 抽象与持久化位置。
- 缺少 Knowledge Base / RAG / Context Builder 的工程归宿。
- 缺少输出结构化解析抽象。

### 风险点

- 原型代码对 `MediaCrawler-main` 路径耦合明显，不适合作为正式服务直接演进。
- 顶层大量外部仓被直接纳入版本控制，后续协作成本极高。
- 前端当前未完全切到 Element Plus，但本轮不做 UI 大修，只先划清边界。

## 2. 旧代码分类

### 保留并迁移

- `frontend-vue3-refactor/` -> 复制为 `frontend/`
  - 理由：这是现阶段唯一可继续演进的 Vue 3 前端代码。
- `图文原件/` -> `docs/source_materials`
  - 理由：属于产品、设计、技术方案文档，应归到文档域。

### 暂存到 legacy

- `Tiktok/` -> `legacy/prototypes/tiktok`
  - 理由：包含高价值原型，但目录结构是实验式，且强耦合外部仓。
- `pages/` -> `legacy/prototypes/pages-html`
  - 理由：属于旧 HTML 原型。
- `DailyHotApi-master/` -> `legacy/external/DailyHotApi-master`
  - 理由：外部参考仓，不应继续占用根目录。
- `MediaCrawler-main/` -> `legacy/external/MediaCrawler-main`
  - 理由：第三方依赖型仓库，后续作为适配参考而非正式主应用。
- `marketer/` -> `legacy/external/marketer`
  - 理由：外部 UI / Agent 参考仓。
- `业务模块原件/` -> `legacy/source_modules`
  - 理由：章节式样例与素材集合，不适合继续直接演进。
- `素材暂存区/` -> `legacy/artifacts`
  - 理由：临时文件与历史产物。
- `frontend-vue3-refactor.zip` -> `legacy/archives/frontend-vue3-refactor.zip`
  - 理由：归档压缩包。

### 保留在 scripts / experiments

- `backend/scripts/`
  - 理由：后续用于数据修复、导入、迁移和验证脚本。
- `scripts/`
  - 理由：仓库级辅助脚本预留。

### 已完成清理

- `frontend-vue3-refactor/`
  - 理由：确认与 `frontend/` 除 README 外无有效差异后，已删除旧副本，避免双目录并行。

## 3. 本轮目标目录

```text
root/
  backend/
  frontend/
  docs/
  legacy/
  scripts/
```

`backend/app/` 内部按 `api / services / db / modules / ai / adapters / workers / core` 分层。

## 4. 本轮交付

- FastAPI 服务可启动
- `/api/v1/health` 可访问
- `POST /api/v1/tasks` 可创建最小任务
- `GET /api/v1/tasks/{task_id}` 可查询状态
- Celery app 可导入
- AI 链路有 stub 入口
- 3 个基础测试可运行
