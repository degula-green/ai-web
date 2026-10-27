# AI内容自动化

本仓库用于落地一套面向内容运营场景的 AI 内容自动化工作流，核心目标是把“热点发现、素材采集、品牌融合、多模态生成、人工审核、自动分发、数据回流”串成一条可验证、可扩展的工程链路。

当前仓库不是单一的文案生成项目，也不是单一的爬虫脚本集合，而是围绕需求清单逐步拆解和验证的项目工作区。现阶段已经完成了第 4 章“多源头数据采集模块”和第 5 章“品牌价值与视觉资产库”的最小可运行验证，并已形成对应的技术说明文档、测试脚本和输出结果。

## 项目定位

本项目聚焦“AI 内容自动化工作流”场景，重点解决以下问题：

- 外部热点内容和优质素材如何持续采集
- 外部内容如何转成可复用的品牌卖点和视觉资产
- 后续如何基于这些输入完成图文/视频生成、人工审核和自动分发

对应的业务主链路为：

`热点发现 -> 多平台采集 -> 链接解析 -> 品牌卖点提炼 -> 视觉资产沉淀 -> 多模态生成 -> 审核协同 -> 自动分发 -> 数据回流`

## 与需求清单的对应关系

| 需求模块 | 当前状态 | 仓库对应位置 |
| --- | --- | --- |
| 1. 多源头数据采集模块 | 已完成最小真实验证 | `第四章-多源头数据采集模块/` |
| 2. 品牌价值与视觉资产库 | 已完成最小真实验证 | `第五章-品牌价值与视觉资产库/` |
| 3. 多模态 AI 仿写与适配引擎 | 方案整理中 | `AI内容自动化工作流技术方案初版.md` |
| 4. 人机协同与质控模块 | 方案整理中 | `AI内容自动化工作流技术方案初版.md` |
| 5. 自动化分发与反馈闭环 | 方案整理中 | `AI内容自动化工作流技术方案初版.md` |
| 6. 链接驱动的内容解析模块 | 方案整理中 | `AI内容自动化工作流技术方案初版.md` |
| 7. 爆款视频特征分析与建模 | 方案整理中 | `AI内容自动化工作流技术方案初版.md` |

## 当前已验证能力

### 1. 多平台热点内容采集

第 4 章已经完成真实平台热榜抓取验证，当前已跑通的平台包括：

- YouTube
- 小红书
- 抖音
- Bilibili

当前已验证的能力包括：

- 热榜/热门页真实访问
- 热点内容标题、链接、作者等基础字段提取
- 结果结构化保存
- 小红书关键词搜索结果采集
- 封面素材下载与素材清单输出

其中，小红书验证结果已经形成热榜、搜索、过滤、账号和素材清单的完整输出；YouTube 已完成 Shorts 页面真实滚动抓取；抖音与 Bilibili 已完成真实热门内容抓取并纳入统一采集验证项目。

### 2. 品牌卖点与视觉资产沉淀

第 5 章已经基于第 4 章采集结果完成最小闭环验证。当前验证链路为：

`固定产品参数输入 -> 读取小红书关键词搜索结果（新手开车技巧）-> 卖点提炼 -> 视觉资产整理 -> 输出品牌卖点库 -> 输出视觉资产库`

当前已验证的能力包括：

- 将固定产品参数与外部图文内容结合
- 从小红书关键词搜索结果中识别用户痛点、表达方式和可迁移内容钩子
- 生成可供后续内容生成使用的品牌卖点库
- 从封面素材和本地下载资源中整理视觉资产条目
- 输出品牌卖点库、视觉资产库和汇总结果

## 仓库结构

```text
AI内容自动化/
├─ AI内容自动化工作流技术方案初版.md
├─ README.md
├─ 需求清单.docx
├─ 第四章-多源头数据采集模块/
│  ├─ xhs_real_validation/
│  ├─ douyin_real_validation/
│  ├─ bilibili_real_validation/
│  ├─ youtube_shorts_real_validation/
│  └─ real_collection_project/
├─ 第五章-品牌价值与视觉资产库/
│  ├─ product_params.sample.json
│  ├─ build_brand_selling_points.py
│  ├─ build_visual_asset_library.py
│  ├─ run_brand_asset_pipeline.py
│  └─ output/
├─ openclaw-skills/
├─ pages/
├─ dify-main/
└─ 素材暂存区/
```

## 关键目录说明

### `AI内容自动化工作流技术方案初版.md`

当前项目的主技术说明文档。现阶段第 4 章和第 5 章已经按真实验证结果回写。

### `第四章-多源头数据采集模块/`

存放多平台采集验证代码和输出结果，重点包括：

- `xhs_real_validation/xhs_real_crawler.py`
- `douyin_real_validation/douyin_hot_crawler.py`
- `bilibili_real_validation/bilibili_real_crawler.py`
- `youtube_shorts_real_validation/youtube_shorts_real_crawler.py`
- `real_collection_project/`：聚合式最小采集项目，包含原始结果、过滤结果、账号库和素材清单

### `第五章-品牌价值与视觉资产库/`

存放品牌卖点提炼与视觉资产整理的最小验证代码和结果，重点包括：

- `product_params.sample.json`
- `build_brand_selling_points.py`
- `build_visual_asset_library.py`
- `run_brand_asset_pipeline.py`
- `output/brand_selling_points.json`
- `output/visual_asset_library.json`
- `output/brand_asset_summary.json`

### `openclaw-skills/`

存放 OpenClaw 相关技能和工作流接入能力，当前用于后续自动化编排扩展。

### `dify-main/`

引入的 Dify 代码与参考资源，主要用于后续 AI 工作流编排、界面和能力对照。

## 当前可直接查看的验证结果

### 第 4 章采集验证

- 小红书热榜与关键词搜索结果：`第四章-多源头数据采集模块/xhs_real_validation/output/`
- 抖音与 Bilibili 聚合验证结果：`第四章-多源头数据采集模块/real_collection_project/output/`
- YouTube Shorts 抓取结果：`第四章-多源头数据采集模块/youtube_shorts_real_validation/youtube_shorts_results.json`

### 第 5 章品牌与资产验证

- 品牌卖点库：`第五章-品牌价值与视觉资产库/output/brand_selling_points.json`
- 视觉资产库：`第五章-品牌价值与视觉资产库/output/visual_asset_library.json`
- 汇总结果：`第五章-品牌价值与视觉资产库/output/brand_asset_summary.json`

## 快速运行

### 1. 运行第 4 章 YouTube Shorts 真实抓取验证

```powershell
cd "E:\AI内容自动化\第四章-多源头数据采集模块\youtube_shorts_real_validation"
python -m pip install -r requirements.txt
python -m playwright install chromium
python youtube_shorts_real_crawler.py
```

### 2. 运行第 4 章小红书真实抓取验证

```powershell
cd "E:\AI内容自动化\第四章-多源头数据采集模块\xhs_real_validation"
python -m pip install -r requirements.txt
python xhs_real_crawler.py
```

### 3. 运行第 5 章品牌卖点与视觉资产验证

```powershell
cd "E:\AI内容自动化\第五章-品牌价值与视觉资产库"
python run_brand_asset_pipeline.py
```

## 当前阶段的结论

基于仓库中的现有代码和输出结果，可以明确确认两点：

- 多平台热点内容采集已经具备真实实现基础，不再停留在概念阶段。
- 基于已采集内容的品牌卖点提炼和视觉资产沉淀已经形成最小闭环，可继续向生成模块衔接。

当前阶段尚未完全接入的部分主要包括：

- OpenClaw / 搜索引擎的全网卖点补充
- 飞书确认与审核链路
- 完整的品牌自有视觉资产管理
- 多模态生成、自动分发和数据回流的工程化打通

## 适合谁看

这个仓库适合以下几类角色直接使用：

- 项目负责人：快速了解需求清单的落地进度
- 研发人员：查看已验证脚本、输出结构和后续可扩展点
- 产品/运营：理解当前系统已具备的采集和品牌输入能力
- 汇报场景：直接引用技术说明文档和验证结果截图

## 说明

本仓库当前重心是“验证关键模块是否真实可跑”，不是一次性完成整套系统开发。因此，仓库内既包含技术方案文档，也包含按章节拆分的最小验证项目。后续开发将继续以“先验证、再收敛、后模块化”的方式推进。
