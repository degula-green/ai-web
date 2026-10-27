# AI内容自动化系统品牌管理接口 API文档【V1.0】

## 1. 文档说明

本文档用于规范“品牌管理（品牌产品与资产库）”模块的接口设计，覆盖前端 `brand-manager` 页面当前交互所需的核心能力：

- 品牌/产品档案维护
- 营销卖点维护（手工新增/编辑/删除）
- 视觉素材上传与管理
- 主创空间品牌上下文注入

当前版本说明（V1）：
- 前端 UI 中的“AI 联网建档”“AI 卖点提炼”“飞书审批推送”能力先保留交互占位。
- 后端接口文档暂不纳入上述三类能力，后续在 V1.x 再补充。

本文档已对齐：

- 数据库：`backend/app/db/mysql/ai_content_automation.sql`（`brand_products`、`brand_selling_points`、`brand_visual_assets`）
- 数据库设计说明：`docs/数据库设计/5_2_品牌产品与资产库数据库设计_v_1_0.md`
- 前端 UI 与类型：`frontend/src/views/brand-manager`、`frontend/src/types/brandInjection.ts`
- 后端框架风格：`FastAPI + /api/v1 + contract_success(code/msg/data)`

## 2. 接口设计原则

- 统一前缀：`/api/v1/brand-knowledge`
- 统一鉴权：`Authorization: Bearer {token}`
- 统一返回：

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

- 数据隔离：所有数据按当前登录用户隔离（`user_id`）
- 逻辑删除：档案、卖点、素材均走 `is_deleted=1`
- ID 返回规范：数据库为 `BIGINT`，接口统一返回 `String`（防止前端精度问题）

## 3. 通用约定

### 3.1 分页结构

```json
{
  "pageNo": 1,
  "pageSize": 20,
  "total": 135,
  "list": []
}
```

### 3.2 枚举定义

- `sellingPointType`：`required` / `optional` / `forbidden`
- `sellingPointSource`：`manual` / `ai` / `external`
- `sellingPointStatus`：`draft` / `pending_confirm` / `confirmed` / `rejected`
- `assetType`：`logo` / `ui` / `promo` / `product` / `video`

注：`rejected` 为前端已使用状态，建议后端按业务需要同步支持（V1 若未启用可仅作为保留值）。

### 3.3 前端字段与数据库字段映射

| 前端/API字段 | 数据库字段 | 说明 |
| --- | --- | --- |
| `brandId` | `brand_products.id` | 品牌档案ID（本质为产品线档案ID） |
| `tone` | `brand_products.tone_voice` | 前端调性字段映射 |
| `forbiddenPhrases` | `brand_products.forbidden_phrases` | JSON 数组 |
| `sellingPoints[].scenarios` | `brand_selling_points.applicable_scenarios` | 场景字段映射 |
| `visualAssets[].thumbnail` | `brand_visual_assets.thumbnail_url` | 缩略图字段映射 |
| `visualAssets[].scenarios` | `brand_visual_assets.applicable_scenarios` | 场景字段映射 |
| `visualAssets[].relatedSellingPointIds` | `brand_visual_assets.extra_data.relatedSellingPointIds` | 关联卖点列表存入 `extra_data` |

### 3.4 素材类型映射（API -> DB）

| API `assetType` | DB `asset_type` |
| --- | --- |
| `logo` | `brand_logo` |
| `ui` | `product_ui` |
| `promo` | `promo_img` |
| `video` | `video_asset` |
| `product` | `product_ui`（V1 先复用） |

## 4. 接口一览

| 接口名称 | 请求方式 | 接口路径 | 用途 |
| --- | --- | --- | --- |
| 品牌档案列表 | GET | `/api/v1/brand-knowledge/products` | 左侧卡片列表（检索/分页） |
| 新建品牌档案（手动） | POST | `/api/v1/brand-knowledge/products` | 手动创建品牌产品档案 |
| 品牌档案详情 | GET | `/api/v1/brand-knowledge/products/{brandId}` | 右侧抽屉基本信息 |
| 更新品牌档案 | PUT | `/api/v1/brand-knowledge/products/{brandId}` | 保存基本参数与禁用词 |
| 删除品牌档案 | DELETE | `/api/v1/brand-knowledge/products/{brandId}` | 删除档案及关联卖点/素材 |
| 卖点列表 | GET | `/api/v1/brand-knowledge/products/{brandId}/selling-points` | 获取营销卖点列表 |
| 批量保存卖点 | PUT | `/api/v1/brand-knowledge/products/{brandId}/selling-points` | 批量新增/修改/删除卖点 |
| 视觉素材列表 | GET | `/api/v1/brand-knowledge/products/{brandId}/visual-assets` | 获取素材库 |
| 上传视觉素材 | POST | `/api/v1/brand-knowledge/products/{brandId}/visual-assets/upload` | 上传图片/视频素材 |
| 更新视觉素材 | PUT | `/api/v1/brand-knowledge/visual-assets/{assetId}` | 修改标签/用途等元数据 |
| 删除视觉素材 | DELETE | `/api/v1/brand-knowledge/visual-assets/{assetId}` | 删除素材 |
| 生成品牌上下文载荷 | POST | `/api/v1/brand-knowledge/context/payload` | 主创空间拼装品牌注入载荷 |

## 5. 接口详细说明

### 5.1 品牌档案列表

- 接口路径：`/api/v1/brand-knowledge/products`
- 请求方式：`GET`
- 接口描述：用于品牌管理页左侧卡片列表加载。

请求参数：

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `keyword` | String | 否 | 无 | 按品牌名/产品名检索 |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `20` | 每页数量 |
| `sortBy` | String | 否 | `updatedAt` | `updatedAt` / `createdAt` |

返回示例：

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 20,
    "total": 2,
    "list": [
      {
        "brandId": "1001",
        "brandName": "智创网络",
        "productName": "智创内容自动化矩阵 v3",
        "coverUrl": "https://cdn.example.com/brand/1001/cover.png",
        "sellingPointsCount": 12,
        "visualAssetsCount": 16,
        "updatedAt": "2026-04-08 20:15:00"
      }
    ]
  }
}
```

---

### 5.2 新建品牌档案（手动）

- 接口路径：`/api/v1/brand-knowledge/products`
- 请求方式：`POST`

请求参数：

| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `brandName` | String | 是 | 品牌名称 |
| `productName` | String | 是 | 产品/产品线名称 |
| `positioning` | String | 否 | 产品定位 |
| `targetAudience` | String | 否 | 目标人群 |
| `scenarios` | String | 否 | 适用场景 |
| `tone` | String | 否 | 调性，落库映射到 `tone_voice` |
| `forbiddenPhrases` | Array[String] | 否 | 禁用词数组 |
| `coverUrl` | String | 否 | 封面图 URL |

返回示例：

```json
{
  "code": 200,
  "msg": "创建成功",
  "data": {
    "brandId": "1009"
  }
}
```

---

### 5.3 品牌档案详情

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}`
- 请求方式：`GET`

返回示例：

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "brandId": "1001",
    "brandName": "星火智能",
    "productName": "星火内容自动化矩阵系统",
    "positioning": "企业级全渠道内容一站式 AI 生产与分发平台",
    "targetAudience": "MCN机构、企业市场部、电商运营团队",
    "scenarios": "图文批量生成、跨平台矩阵分发",
    "tone": "专业、科技感、高效、值得信赖",
    "forbiddenPhrases": ["便宜", "免费试用"],
    "coverUrl": "https://cdn.example.com/brand/1001/cover.png",
    "createdAt": "2026-04-01 09:00:00",
    "updatedAt": "2026-04-08 20:15:00"
  }
}
```

---

### 5.4 更新品牌档案

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}`
- 请求方式：`PUT`
- 接口描述：更新基础信息区参数。

请求体与 `5.2` 一致。

返回示例：

```json
{
  "code": 200,
  "msg": "保存成功",
  "data": {
    "brandId": "1001",
    "updatedAt": "2026-04-08 21:08:00"
  }
}
```

---

### 5.5 删除品牌档案

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}`
- 请求方式：`DELETE`
- 接口描述：逻辑删除档案，并级联逻辑删除卖点与素材。

返回示例：

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": {
    "brandId": "1001",
    "deletedAt": "2026-04-08 21:12:00"
  }
}
```

---

### 5.6 卖点列表

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}/selling-points`
- 请求方式：`GET`

请求参数：

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `type` | String | 否 | 无 | `required` / `optional` / `forbidden` |
| `status` | String | 否 | 无 | `draft` / `pending_confirm` / `confirmed` / `rejected` |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `100` | 默认返回全部卖点 |

返回示例：

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 100,
    "total": 3,
    "list": [
      {
        "id": "2001",
        "title": "全渠道一站式矩阵管理",
        "description": "支持抖音、小红书等多平台",
        "type": "required",
        "weight": 10,
        "source": "manual",
        "status": "confirmed",
        "platforms": ["douyin", "xiaohongshu"],
        "scenarios": ["软件测评", "效率提升演示"],
        "createdAt": "2026-04-06 10:10:00",
        "updatedAt": "2026-04-08 21:00:00"
      }
    ]
  }
}
```

---

### 5.7 批量保存卖点

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}/selling-points`
- 请求方式：`PUT`
- 接口描述：支持前端面板一次性提交新增/修改/删除。

请求参数：

| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `upserts` | Array[Object] | 否 | 新增或更新条目；`id` 为空表示新增 |
| `deleteIds` | Array[String] | 否 | 逻辑删除卖点 ID 列表 |

`upserts` 子项字段：`id`、`title`、`description`、`type`、`weight`、`source`、`status`、`platforms`、`scenarios`。

返回示例：

```json
{
  "code": 200,
  "msg": "保存成功",
  "data": {
    "upserted": 4,
    "deleted": 1
  }
}
```

---

### 5.8 视觉素材列表

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}/visual-assets`
- 请求方式：`GET`

请求参数：

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `assetType` | String | 否 | 无 | `logo` / `ui` / `promo` / `product` / `video` |
| `pageNo` | Int | 否 | `1` | 页码 |
| `pageSize` | Int | 否 | `50` | 每页条数 |

返回示例：

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "pageNo": 1,
    "pageSize": 50,
    "total": 2,
    "list": [
      {
        "id": "3001",
        "assetType": "logo",
        "assetUrl": "https://cdn.example.com/brand/1001/logo.png",
        "thumbnail": "https://cdn.example.com/brand/1001/logo_thumb.png",
        "tags": ["官方Logo", "白底"],
        "relatedSellingPointIds": [],
        "platforms": ["douyin"],
        "scenarios": ["通用"],
        "usableForCover": true,
        "usableForVideo": true,
        "extraData": {
          "width": 1024,
          "height": 1024
        },
        "createdAt": "2026-04-08 20:30:00",
        "updatedAt": "2026-04-08 20:30:00"
      }
    ]
  }
}
```

---

### 5.9 上传视觉素材

- 接口路径：`/api/v1/brand-knowledge/products/{brandId}/visual-assets/upload`
- 请求方式：`POST`
- `Content-Type`：`multipart/form-data`

请求参数：

| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `file` | File | 是 | 图片或视频 |
| `assetType` | String | 是 | `logo` / `ui` / `promo` / `product` / `video` |
| `tags` | String | 否 | JSON 字符串数组，如 `["封面","主KV"]` |
| `platforms` | String | 否 | JSON 字符串数组 |
| `scenarios` | String | 否 | JSON 字符串数组 |
| `relatedSellingPointIds` | String | 否 | JSON 字符串数组 |
| `usableForCover` | Bool | 否 | 默认 `false` |
| `usableForVideo` | Bool | 否 | 默认 `false` |

返回示例：

```json
{
  "code": 200,
  "msg": "上传成功",
  "data": {
    "id": "3009",
    "assetType": "promo",
    "assetUrl": "https://cdn.example.com/brand/1001/assets/3009.png",
    "thumbnail": "https://cdn.example.com/brand/1001/assets/3009_thumb.png"
  }
}
```

---

### 5.10 更新视觉素材

- 接口路径：`/api/v1/brand-knowledge/visual-assets/{assetId}`
- 请求方式：`PUT`

请求参数：

| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `assetType` | String | 否 | 素材类型 |
| `tags` | Array[String] | 否 | 标签 |
| `platforms` | Array[String] | 否 | 适用平台 |
| `scenarios` | Array[String] | 否 | 适用场景 |
| `relatedSellingPointIds` | Array[String] | 否 | 关联卖点 |
| `usableForCover` | Bool | 否 | 是否封面可用 |
| `usableForVideo` | Bool | 否 | 是否视频可用 |

返回示例：

```json
{
  "code": 200,
  "msg": "更新成功",
  "data": {
    "assetId": "3009",
    "updatedAt": "2026-04-08 21:35:00"
  }
}
```

---

### 5.11 删除视觉素材

- 接口路径：`/api/v1/brand-knowledge/visual-assets/{assetId}`
- 请求方式：`DELETE`

返回示例：

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": {
    "assetId": "3009",
    "deletedAt": "2026-04-08 21:36:00"
  }
}
```

---

### 5.12 生成品牌上下文载荷

- 接口路径：`/api/v1/brand-knowledge/context/payload`
- 请求方式：`POST`
- 接口描述：供主创空间在发起生成前，组装标准品牌上下文。

请求参数：

| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `brandId` | String | 是 | 品牌档案ID |
| `sellingPointIds` | Array[String] | 否 | 勾选卖点 |
| `assetIds` | Array[String] | 否 | 勾选素材 |
| `toneRules` | String | 否 | 附加风格约束 |

返回示例：

```json
{
  "code": 200,
  "msg": "组装成功",
  "data": {
    "brandProfile": {
      "brandId": "1001",
      "brandName": "星火智能",
      "productName": "星火内容自动化矩阵系统",
      "positioning": "企业级全渠道内容一站式 AI 生产与分发平台",
      "targetAudience": "MCN机构、企业市场部",
      "scenarios": "图文批量生成",
      "tone": "专业、科技感",
      "forbiddenPhrases": ["便宜", "免费试用"]
    },
    "requiredSellingPoints": [],
    "optionalSellingPoints": [],
    "forbiddenPhrases": ["便宜", "免费试用"],
    "selectedAssets": [],
    "toneRules": "保持专业口吻"
  }
}
```

## 6. 异常处理

| 状态码 | 业务含义 | 说明 |
| --- | --- | --- |
| `400` | 参数错误 | 参数缺失、类型错误、枚举非法 |
| `401` | 未登录 | Token 缺失或失效 |
| `403` | 无权限 | 非本人数据访问 |
| `404` | 资源不存在 | 品牌档案/卖点/素材不存在 |
| `409` | 状态冲突 | 卖点状态流转非法 |
| `413` | 文件过大 | 上传素材超过限制 |
| `415` | 文件类型不支持 | 非图片/视频类型 |
| `500` | 服务异常 | 系统内部错误 |

## 7. 后端落地建议（与当前框架对齐）

- 路由注册建议：`app/api/v1/brand_knowledge.py`
- 路由前缀建议：在 `app/api/router.py` 增加
  - `api_router.include_router(brand_knowledge_router, prefix="/brand-knowledge", tags=["brand-knowledge"])`
- 返回结构建议：统一使用 `contract_success`
- 鉴权依赖建议：复用 `get_current_auth_context`
- Service/Repository 建议：
  - `app/services/brand_knowledge_service.py`
  - `app/db/repositories/brand_knowledge_repository.py`
- Schema 建议：`app/schemas/brand_knowledge.py`（请求体字段使用 camelCase，与前端保持一致）

