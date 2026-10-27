以下仅写“4. 数据采集接口”，并按当前数据采集域数据库设计、UI 设计以及前端页面的实际交互来约束接口。

本阶段只做采集、缓存、入库、查询与导出，不包含内容分析、仿写、标签推断、相似内容检索等增强能力。

## 4. 数据采集接口

### 4.1 接口设计原则

- 接口采用 REST 风格，统一前缀为 `/api/v1/data-collection`
- 所有接口均基于当前登录用户上下文执行，不在请求中显式传 `ownerUserId`
- 图文、视频、热榜分开处理，避免一张表和一套接口同时承担多种内容结构
- 主表去重按 `platform_source + content_id` 逻辑唯一键执行，不依赖 MySQL 外键
- Redis 只做短时缓存和入库中转，选中入库后立即删除对应缓存
- 热榜缓存保留 1 小时，超过 1 小时后自动重新抓取刷新
- 用户未选择入库的关键词采集结果，最多保留 1 小时后自动过期

### 4.2 通用约定

#### 1. 返回格式

接口统一返回如下结构：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

#### 2. 分页格式

分页接口统一使用如下字段：

- `pageNo`：当前页，从 `1` 开始
- `pageSize`：每页条数
- `total`：总条数
- `list`：数据列表

#### 3. 通用枚举

- `platformCode`：平台编码，当前重点为 `douyin`
- `contentKind`：内容类型，当前支持 `image`、`video`
- `sourceScene`：数据来源场景，当前支持 `hot_rank`、`keyword_search`
- `taskStatus`：任务状态，当前支持 `pending`、`running`、`completed`、`failed`
- `importStatus`：入库状态，当前支持 `not_imported`、`importing`、`imported`

### 4.3 接口一览

| 接口名称 | 请求方式 | 接口路径 | 用途 |
| --- | --- | --- | --- |
| 数据采集总览接口 | GET | `/api/v1/data-collection/overview` | 返回首页统计卡片与平台概览 |
| 平台列表接口 | GET | `/api/v1/data-collection/platforms` | 返回平台列表，供首页平台卡片使用 |
| 平台明细接口 | GET | `/api/v1/data-collection/platforms/{platformCode}` | 返回平台基础信息与汇总统计 |
| 平台热榜接口 | GET | `/api/v1/data-collection/platforms/{platformCode}/hot-ranks` | 返回平台热榜列表 |
| 创建关键词采集任务接口 | POST | `/api/v1/data-collection/keyword-tasks` | 创建关键词采集任务并触发采集 |
| 查询关键词任务接口 | GET | `/api/v1/data-collection/keyword-tasks/{taskNo}` | 查询任务状态与统计 |
| 查询关键词结果接口 | GET | `/api/v1/data-collection/keyword-tasks/{taskNo}/results` | 查询 Redis 中的采集结果 |
| 内容详情接口 | GET | `/api/v1/data-collection/contents/{contentId}` | 查询热榜或关键词结果的内容详情 |
| 素材入库接口 | POST | `/api/v1/data-collection/materials/import` | 将选中的 Redis 结果入库到 MySQL |
| 我的素材库接口 | GET | `/api/v1/data-collection/users/me/materials` | 查询当前用户的素材库 |
| 删除素材关系接口 | DELETE | `/api/v1/data-collection/users/me/material-relations/{chainId}` | 删除当前用户与素材的关系 |
| 导出接口 | POST | `/api/v1/data-collection/platforms/{platformCode}/export` | 导出热榜或素材库数据 |

### 4.4 数据采集总览接口

#### 1. 接口基础信息

* 接口名称：数据采集总览接口
* 接口路径：`/api/v1/data-collection/overview`
* 请求方式：`GET`
* 接口描述：返回数据采集首页所需的统计卡片、平台列表与最新同步信息。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

无

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "stats": {
      "platformCount": 6,
      "todayFetched": 34502,
      "hotRankUpdates": 128,
      "keywordTaskCount": 45,
      "keywordTaskActive": 8
    },
    "platforms": [
      {
        "platformCode": "douyin",
        "platformName": "抖音",
        "icon": "music_note",
        "latestUpdateTime": "5分钟前",
        "hotRankCount": 50,
        "keywordTaskCount": 8,
        "status": "collecting",
        "themeColor": "text-gray-900 bg-gray-100 border-gray-200"
      }
    ]
  }
}
```

##### （2）返回参数说明

| 参数名 | 类型 | 备注 |
| --- | --- | --- |
| `data.stats.platformCount` | Int | 接入平台数 |
| `data.stats.todayFetched` | Int | 今日抓取总数 |
| `data.stats.hotRankUpdates` | Int | 热榜更新次数 |
| `data.stats.keywordTaskCount` | Int | 关键词任务数 |
| `data.stats.keywordTaskActive` | Int | 进行中任务数 |
| `data.platforms` | Array | 平台列表，字段与前端 `PlatformSummary` 保持一致 |

### 4.5 平台列表接口

#### 1. 接口基础信息

* 接口名称：平台列表接口
* 接口路径：`/api/v1/data-collection/platforms`
* 请求方式：`GET`
* 接口描述：返回平台卡片列表，供首页平台采集大厅使用。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

无

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": [
    {
      "platformCode": "douyin",
      "platformName": "抖音",
      "icon": "music_note",
      "latestUpdateTime": "5分钟前",
      "hotRankCount": 50,
      "keywordTaskCount": 8,
      "status": "collecting",
      "themeColor": "text-gray-900 bg-gray-100 border-gray-200"
    }
  ]
}
```

##### （2）返回参数说明

| 参数名 | 类型 | 备注 |
| --- | --- | --- |
| `platformCode` | String | 平台编码 |
| `platformName` | String | 平台名称 |
| `icon` | String | 图标名 |
| `latestUpdateTime` | String | 最近同步时间 |
| `hotRankCount` | Int | 当前平台热榜数量 |
| `keywordTaskCount` | Int | 当前平台关键词任务数 |
| `status` | String | 平台状态：`normal` / `collecting` / `error` |
| `themeColor` | String | 卡片主题色样式 |

### 4.6 平台明细接口

#### 1. 接口基础信息

* 接口名称：平台明细接口
* 接口路径：`/api/v1/data-collection/platforms/{platformCode}`
* 请求方式：`GET`
* 接口描述：返回某个平台的基础信息、最新同步状态、热榜统计与关键词任务统计。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 是 | 无 | 平台编码，如 `douyin` |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "platformCode": "douyin",
    "platformName": "抖音",
    "status": "collecting",
    "latestUpdateTime": "10分钟前",
    "hotRankCount": 50,
    "keywordTaskCount": 8,
    "supportsContentKinds": ["image", "video"],
    "lastSyncAt": "2026-04-06 10:00:00"
  }
}
```

### 4.7 平台热榜接口

#### 1. 接口基础信息

* 接口名称：平台热榜接口
* 接口路径：`/api/v1/data-collection/platforms/{platformCode}/hot-ranks`
* 请求方式：`GET`
* 接口描述：返回某个平台的热榜列表，供“全站热榜”标签页展示。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 是 | 无 | 平台编码 |
| `snapshotNo` | String | 否 | 最新快照 | 热榜快照编号，不传则取最新快照 |
| `boardType` | String | 否 | 无 | 榜单类型，如全站热榜、分类热榜 |
| `timeRange` | String | 否 | `24h` | 时间范围，如 `24h`、`3d`、`week` |
| `sortBy` | String | 否 | `heat` | 排序方式：`heat` / `time` / `engagement` |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `20` | 每页条数 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 128,
    "list": [
      {
        "contentId": "aweme_123456789",
        "rank": 1,
        "title": "2024年必须掌握的 AI 提效工具盘点(第1弹)",
        "summary": "从文字生成到视频生成，梳理了目前市面上最好用的几款 AI 工具...",
        "authorName": "科技前沿探索者",
        "publishTime": "2小时前",
        "hotValue": 5991000,
        "likes": 20000,
        "comments": 4749,
        "shares": 1685,
        "views": 47000,
        "tags": ["AI工具", "效率提升", "干货分享"],
        "sourceUrl": "https://www.douyin.com/...",
        "sourceType": "hot_rank",
        "contentKind": "video",
        "snapshotNo": "HK20260406_100000",
        "materialId": null,
        "chainId": null,
        "importStatus": "not_imported"
      }
    ]
  }
}
```

##### （2）返回参数说明

| 参数名 | 类型 | 备注 |
| --- | --- | --- |
| `contentId` | String | 平台内容 ID |
| `rank` | Int | 热榜排名 |
| `title` | String | 标题 |
| `summary` | String | 摘要 |
| `authorName` | String | 作者昵称 |
| `publishTime` | String | 发布时间 |
| `hotValue` | Long | 热度值 |
| `likes/comments/shares/views` | Long | 互动指标 |
| `tags` | Array | 标签列表 |
| `sourceUrl` | String | 原文链接 |
| `sourceType` | String | 来源类型，固定 `hot_rank` |
| `contentKind` | String | 内容类型，`image` / `video` |
| `snapshotNo` | String | 热榜快照编号 |
| `materialId` | String | 已入库后的素材主表 ID，未入库时为空 |
| `chainId` | String | 当前用户关系 ID，未入库时为空 |
| `importStatus` | String | 入库状态 |

### 4.8 创建关键词采集任务接口

#### 1. 接口基础信息

* 接口名称：创建关键词采集任务接口
* 接口路径：`/api/v1/data-collection/keyword-tasks`
* 请求方式：`POST`
* 接口描述：创建关键词采集任务，系统将先把抓取结果存入 Redis，等待用户选择入库。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 是 | 无 | 平台编码，如 `douyin` |
| `keyword` | String | 是 | 无 | 采集关键词，如 `COS` |
| `contentKind` | String | 否 | `image` | 内容类型，当前支持 `image`、`video` |
| `timeRange` | String | 否 | `24h` | 时间范围 |
| `sortBy` | String | 否 | `heat` | 排序方式 |
| `pageSize` | Int | 否 | `20` | 单次返回条数 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "任务已创建",
  "data": {
    "taskNo": "KT202604060001",
    "taskStatus": "running",
    "platformCode": "douyin",
    "keyword": "COS",
    "contentKind": "image",
    "redisKey": "douyin:crawl:item:image:KT202604060001",
    "expireAt": "2026-04-06 12:00:00",
    "resultCount": 0
  }
}
```

##### （2）设计说明

- 任务创建后，采集结果先进入 Redis
- 若用户未选择入库，Redis 结果最多保留 1 小时
- 若用户点击“保留入库”，对应条目立即删除缓存

### 4.9 查询关键词任务接口

#### 1. 接口基础信息

* 接口名称：查询关键词任务接口
* 接口路径：`/api/v1/data-collection/keyword-tasks/{taskNo}`
* 请求方式：`GET`
* 接口描述：查询关键词采集任务状态、结果数量、缓存有效期等信息。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `taskNo` | String | 是 | 无 | 任务编号 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "taskNo": "KT202604060001",
    "platformCode": "douyin",
    "keyword": "COS",
    "contentKind": "image",
    "taskStatus": "running",
    "crawlCount": 30,
    "resultCount": 28,
    "importedCount": 6,
    "cacheExpireAt": "2026-04-06 12:00:00",
    "createdAt": "2026-04-06 11:00:00",
    "updatedAt": "2026-04-06 11:08:00"
  }
}
```

### 4.10 查询关键词结果接口

#### 1. 接口基础信息

* 接口名称：查询关键词结果接口
* 接口路径：`/api/v1/data-collection/keyword-tasks/{taskNo}/results`
* 请求方式：`GET`
* 接口描述：查询 Redis 中尚未入库的关键词采集结果，供前端“素材库预览”和“保留入库”使用。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `taskNo` | String | 是 | 无 | 任务编号 |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `20` | 每页条数 |
| `keyword` | String | 否 | 无 | 二次筛选关键词 |
| `sortBy` | String | 否 | `heat` | 排序方式 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 28,
    "taskNo": "KT202604060001",
    "taskStatus": "running",
    "cacheExpireAt": "2026-04-06 12:00:00",
    "list": [
      {
        "contentId": "aweme_999001",
        "title": "如何利用 ChatGPT 快速生成小红书爆款文案",
        "summary": "为大家整理了一套开箱即用的 prompt...",
        "coverUrl": "https://...",
        "authorName": "内容运营专家",
        "publishTime": "1天前",
        "likes": 1827,
        "comments": 1121,
        "shares": 878,
        "collects": 5563,
        "tags": ["内容营销", "ChatGPT", "小红书运营"],
        "sourceUrl": "https://www.douyin.com/...",
        "sourceType": "keyword_search",
        "contentKind": "image",
        "platformCode": "douyin",
        "importStatus": "not_imported"
      }
    ]
  }
}
```

##### （2）设计说明

- 本接口只读 Redis，不直接读 MySQL 主表
- 前端点击“保留入库”时，应调用素材入库接口
- 结果最多保留 1 小时，超时自动过期

### 4.11 内容详情接口

#### 1. 接口基础信息

* 接口名称：内容详情接口
* 接口路径：`/api/v1/data-collection/contents/{contentId}`
* 请求方式：`GET`
* 接口描述：返回内容详情，支持热榜内容和关键词结果内容。若内容已入库，则同时返回素材主表和当前用户关系信息。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `contentId` | String | 是 | 无 | 平台内容 ID |
| `platformCode` | String | 否 | `douyin` | 平台编码 |
| `contentKind` | String | 否 | 无 | 内容类型，`image` / `video` |
| `sourceScene` | String | 否 | 无 | 来源场景，`hot_rank` / `keyword_search` |
| `sourceRefNo` | String | 否 | 无 | 来源编号，如 `taskNo` 或 `snapshotNo` |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "contentId": "aweme_999001",
    "platformCode": "douyin",
    "contentKind": "image",
    "sourceScene": "keyword_search",
    "materialId": "10086",
    "chainId": "20001",
    "importStatus": "imported",
    "title": "如何利用 ChatGPT 快速生成小红书爆款文案",
    "summary": "为大家整理了一套开箱即用的 prompt...",
    "authorName": "内容运营专家",
    "authorId": "author_001",
    "authorSecUid": "secuid_xxx",
    "authorAvatarUrl": "https://...",
    "publishAt": "2026-04-05 10:00:00",
    "contentUrl": "https://www.douyin.com/...",
    "coverUrl": "https://...",
    "likeCount": 1827,
    "commentCount": 1121,
    "collectCount": 5563,
    "shareCount": 878,
    "playCount": 47000,
    "tagList": ["内容营销", "ChatGPT", "小红书运营"],
    "mediaCount": 1,
    "mediaJson": [],
    "extraJson": {},
    "rawJson": {}
  }
}
```

##### （2）设计说明

- 如果内容尚未入库，则 `materialId`、`chainId`、`importStatus` 为空或 `not_imported`
- 如果内容来自热榜快照，则优先从热榜快照或 Redis 返回详情
- 如果内容来自关键词任务，则优先从 Redis 返回详情

### 4.12 素材入库接口

#### 1. 接口基础信息

* 接口名称：素材入库接口
* 接口路径：`/api/v1/data-collection/materials/import`
* 请求方式：`POST`
* 接口描述：将选中的 Redis 采集结果写入 MySQL 主表，并为当前用户建立素材关系；已存在的内容按 `platform_source + content_id` 去重，不重复插入主表。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 是 | 无 | 平台编码 |
| `contentKind` | String | 是 | 无 | `image` / `video` |
| `sourceScene` | String | 是 | 无 | `hot_rank` / `keyword_search` |
| `sourceRefNo` | String | 是 | 无 | 来源编号，如 `taskNo` 或 `snapshotNo` |
| `contentIds` | Array<String> | 是 | 无 | 选中的平台内容 ID 列表 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "入库成功",
  "data": {
    "platformCode": "douyin",
    "contentKind": "image",
    "sourceScene": "keyword_search",
    "sourceRefNo": "KT202604060001",
    "requestedCount": 3,
    "insertedMaterialCount": 1,
    "linkedCount": 3,
    "duplicateMaterialCount": 2,
    "duplicateLinkCount": 0,
    "deletedRedisCount": 3,
    "materialIds": ["10086"],
    "chainIds": ["20001", "20002", "20003"]
  }
}
```

##### （2）设计说明

- 主表去重规则：`platform_source + content_id`
- 用户关系去重规则：`owner_user_id + content_kind + material_id`
- 对同一内容，多个用户入库时，主表只保留一份，关系表按用户分别增加记录
- 用户选择入库后，对应 Redis 缓存立即删除
- 未被选择的 Redis 内容仍按 TTL 保留到 1 小时后自动失效

### 4.13 我的素材库接口

#### 1. 接口基础信息

* 接口名称：我的素材库接口
* 接口路径：`/api/v1/data-collection/users/me/materials`
* 请求方式：`GET`
* 接口描述：返回当前登录用户的素材库列表。列表数据优先读取 `douyin_user_material_chain`，不直接依赖图文/视频主表 join。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 否 | 无 | 平台编码 |
| `contentKind` | String | 否 | 无 | `image` / `video` |
| `keyword` | String | 否 | 无 | 标题或摘要筛选 |
| `sourceScene` | String | 否 | 无 | 来源场景 |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `20` | 每页条数 |
| `sortBy` | String | 否 | `importedAt` | 排序方式 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 28,
    "list": [
      {
        "chainId": "20001",
        "materialId": "10086",
        "contentId": "aweme_999001",
        "platformCode": "douyin",
        "contentKind": "image",
        "title": "如何利用 ChatGPT 快速生成小红书爆款文案",
        "summary": "为大家整理了一套开箱即用的 prompt...",
        "coverUrl": "https://...",
        "authorName": "内容运营专家",
        "publishAt": "2026-04-05 10:00:00",
        "sourceScene": "keyword_search",
        "importStatus": "imported",
        "selectedAt": "2026-04-06 11:10:00",
        "importedAt": "2026-04-06 11:10:30"
      }
    ]
  }
}
```

##### （2）设计说明

- 素材库列表优先走关系表，避免列表页直接回查主表
- 详情页再按 `materialId` 查询主表
- 这样可以保证“按用户看素材”的高频查询更快

### 4.14 删除素材关系接口

#### 1. 接口基础信息

* 接口名称：删除素材关系接口
* 接口路径：`/api/v1/data-collection/users/me/material-relations/{chainId}`
* 请求方式：`DELETE`
* 接口描述：删除当前用户与某个素材的关系，不影响其他用户对同一素材的引用。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `chainId` | String | 是 | 无 | 用户素材关系 ID |

#### 3. 返回参数

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": {
    "chainId": "20001",
    "deletedAt": "2026-04-06 11:20:00"
  }
}
```

### 4.15 导出接口

#### 1. 接口基础信息

* 接口名称：导出接口
* 接口路径：`/api/v1/data-collection/platforms/{platformCode}/export`
* 请求方式：`POST`
* 接口描述：导出热榜或素材库数据，支持后续生成 CSV、XLSX 或 JSON 文件。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 是 | 无 | 平台编码 |
| `exportScope` | String | 是 | 无 | `hot_rank` / `library` |
| `contentKind` | String | 否 | 无 | `image` / `video` |
| `fileType` | String | 否 | `xlsx` | 导出格式：`xlsx` / `csv` / `json` |
| `sourceRefNo` | String | 否 | 无 | 热榜快照编号或关键词任务编号 |

#### 3. 返回参数

```json
{
  "code": 200,
  "msg": "导出任务已创建",
  "data": {
    "exportNo": "EX202604060001",
    "fileType": "xlsx",
    "fileName": "douyin_hot_rank_20260406.xlsx",
    "downloadUrl": "https://...",
    "expireAt": "2026-04-07 11:00:00"
  }
}
```

### 4.16 异常状态码说明

| 状态码 | 说明 | 解决方案 |
| --- | --- | --- |
| 400 | 参数错误 | 检查平台编码、分页参数、任务编号等 |
| 401 | 未登录或会话失效 | 重新登录 |
| 403 | 无权限 | 检查当前用户角色和权限 |
| 404 | 资源不存在 | 检查平台编码、任务编号、contentId |
| 409 | 数据冲突 | 说明内容已存在或关系已存在 |
| 500 | 服务器异常 | 联系后端排查 |

### 4.17 设计说明

- `douyin_image_materials` 与 `douyin_video_materials` 是素材主表，只保存一份标准化内容
- `douyin_user_material_chain` 负责当前登录用户与素材的关系，不承担内容正文存储职责
- 热榜数据单独进入 `douyin_hot_rank_items`，不和素材表混存
- 关键词采集结果先进入 Redis，选中后再入 MySQL，选中即删缓存
- 主表去重键统一按 `platform_source + content_id` 执行
- 当前阶段不提供仿写、标签推断、相似内容分析接口，后续版本再单独扩展

