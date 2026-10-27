# AI内容自动化系统平台账号管理接口 API文档【V1.0】

## 1. 文档说明

本文档用于规范平台账号管理模块的接口设计。该模块负责处理各社交平台（抖音、小红书等）的账号绑定、授权验证、Session 持久化及账号状态监控。

本阶段核心流程：**系统内扫码授权**。即后端启动无头浏览器获取二维码，前端展示，用户扫码后后端捕获 Session 并存入数据库。

### 接口设计原则
- 统一前缀：`/api/v1/platforms/accounts`
- 权限隔离：所有操作仅限当前登录系统用户。
- 异步处理：扫码流程采用“创建任务 -> 轮询状态”模式。

## 2. 通用约定

### 返回格式
```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

### 授权状态枚举 (authStatus)
- `authorized`: 已授权（Session 有效）
- `expired`: 已过期（需要重新授权）
- `need_reauth`: 待重新验证
- `authenticating`: 授权中（正在扫描）

## 3. 接口一览

| 接口名称 | 请求方式 | 接口路径 | 用途 |
| --- | --- | --- | --- |
| 账号授权总览 | GET | `/api/v1/platforms/accounts/overview` | 返回用户绑定的账号统计及平台状态 |
| 账号列表查询 | GET | `/api/v1/platforms/accounts` | 获取当前用户绑定的所有平台账号 |
| 获取登录二维码 | POST | `/api/v1/platforms/accounts/auth/qrcode` | 触发后端开启浏览器获取登录二维码 |
| 检查扫码状态 | GET | `/api/v1/platforms/accounts/auth/check` | 轮询扫码结果及登录状态 |
| 获取账号详情 | GET | `/api/v1/platforms/accounts/{accountId}` | 获取单个账号的详细资料 |
| 同步账号信息 | POST | `/api/v1/platforms/accounts/{accountId}/sync` | 手动触发从平台侧同步昵称、头像等资料 |
| 解绑账号 | DELETE | `/api/v1/platforms/accounts/{accountId}` | 删除账号绑定及关联的 Session |

## 4. 接口详细说明

### 4.1 获取登录二维码
* **接口名称**：获取登录二维码
* **接口路径**：`/api/v1/platforms/accounts/auth/qrcode`
* **请求方式**：`POST`
* **接口描述**：调用后，后端将启动一个 Playwright 实例前往相应平台登录页，截取二维码并返回。该实例将保留一段时间（如 120 秒）等待用户扫码。

**请求参数：**
| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `platformCode` | String | 是 | 平台编码，如 `douyin` |

**返回参数：**
```json
{
  "code": 200,
  "msg": "二维码获取成功",
  "data": {
    "loginSessionId": "auth_task_123456",
    "qrCodeBase64": "data:image/png;base64,xxxx...",
    "expireIn": 120,
    "platformCode": "douyin"
  }
}
```

---

### 4.2 检查扫码状态
* **接口名称**：检查扫码状态
* **接口路径**：`/api/v1/platforms/accounts/auth/check`
* **请求方式**：`GET`
* **接口描述**：前端根据 `loginSessionId` 进行轮询，获取用户扫码后的结果。

**请求参数：**
| 参数名 | 类型 | 必填 | 备注 |
| --- | --- | --- | --- |
| `loginSessionId` | String | 是 | 获取二维码接口返回的任务标识 |

**返回参数：**
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "authorized", 
    "accountId": "1001",
    "nickname": "AI内容研究员",
    "avatarUrl": "https://...",
    "authTime": "2026-04-08 17:30:00"
  }
}
```
*注：status 可能为 `wait_scan` (等待扫码), `wait_confirm` (已扫码待手机确认), `authorized` (授权成功), `failed` (失败/超时)。*

---

### 4.3 账号列表查询
* **接口名称**：账号列表查询
* **接口路径**：`/api/v1/platforms/accounts`
* **请求方式**：`GET`

**请求参数：**
| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `platformCode` | String | 否 | 无 | 筛选特定平台 |
| `authStatus` | String | 否 | 无 | 筛选授权状态 |

**返回参数：**
```json
{
  "code": 200,
  "data": [
    {
      "accountId": "1001",
      "platformCode": "douyin",
      "accountName": "138****8888",
      "nickname": "AI_Content_Master",
      "avatarUrl": "...",
      "authStatus": "authorized",
      "expiresAt": "2026-05-08 17:00:00",
      "lastSyncAt": "2026-04-08 10:00:00"
    }
  ]
}
```

---

### 4.4 解绑账号
* **接口名称**：解绑账号
* **接口路径**：`/api/v1/platforms/accounts/{accountId}`
* **请求方式**：`DELETE`
* **接口描述**：彻底删除该账号的授权信息及本地数据库中的 Session。

**返回参数：**
```json
{
  "code": 200,
  "msg": "解绑成功",
  "data": {
    "accountId": "1001",
    "unbindAt": "2026-04-08 17:35:00"
  }
}
```

## 5. 异常处理

| 状态码 | 业务含义 | 解决方案 |
| --- | --- | --- |
| 401 | 未登录或 Token 失效 | 重新登录系统 |
| 403 | 无权操作该账号 | 检查 ownerUserId 归属 |
| 408 | 扫码超时 | 提示用户重新获取二维码 |
| 429 | 请求过快 | 检查轮询间隔（建议 2-3 秒一次） |
| 500 | 后端浏览器启动失败 | 检查服务器 Playwright/Docker 环境 |

## 6. 后续扩展说明
- 后续将增加 **“密码登录”** 接口，用于支持那些可以通过 账号+密码+验证码 登录且更稳定的平台。
- 将增加 **“多设备管理”**，记录 Session 绑定的浏览器指纹。
