以下仅写“3. 认证与权限接口”，并按当前已确定的身份权限域数据库设计来约束接口对象与字段命名。接口采用 REST 风格；系统角色已明确包括普通用户、系统管理员、智能体工作流设计者，且关键动作需要留痕、可审计。 

## 3. 认证与权限接口

### 3.1 用户登录接口

#### 1. 接口基础信息

* 接口名称：用户登录接口
* 接口路径：`/api/v1/auth/login`
* 请求方式：`POST`
* 接口描述：用户通过用户名、手机号、邮箱或微信等方式登录系统，创建登录会话并返回访问令牌。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`

#### 2. 请求参数

| 参数名           | 类型     | 必填 | 默认值   | 备注                                                     |
| ------------- | ------ | -- | ----- | ------------------------------------------------------ |
| loginType     | String | 是  | 无     | 登录方式：`username` / `phone` / `email` / `wechat`         |
| identity      | String | 是  | 无     | 登录标识，对应 `iam_user_identities.identity_key`             |
| credential    | String | 否  | 无     | 登录凭证。`username/phone/email` 登录时传密码或验证码；`wechat` 登录时可不传 |
| loginCode     | String | 否  | 无     | 微信登录授权码，`loginType=wechat` 时使用                         |
| deviceType    | String | 是  | `web` | 设备类型：`web` / `mobile` / `miniapp`                      |
| deviceId      | String | 否  | 无     | 设备标识                                                   |
| clientVersion | String | 否  | 无     | 客户端版本                                                  |
| osName        | String | 否  | 无     | 操作系统名称                                                 |
| browserName   | String | 否  | 无     | 浏览器名称                                                  |
| userAgent     | String | 否  | 无     | 用户代理字符串                                                |
| ipAddress     | String | 否  | 无     | 客户端IP，通常由网关透传                                          |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx",
    "refreshToken": "refresh_xxx",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "sessionId": "sess_admin_202604020001",
    "user": {
      "id": 1,
      "userNo": "U20260001",
      "username": "superadmin",
      "nickname": "超级管理员",
      "realName": "系统管理员",
      "avatarUrl": null,
      "gender": 1,
      "phone": "13800000001",
      "email": "superadmin@example.com",
      "status": "active",
      "userType": "admin"
    },
    "roles": [
      {
        "roleId": 1,
        "roleCode": "super_admin",
        "roleName": "超级管理员"
      }
    ]
  }
}
```

##### （2）失败返回

```json
{
  "code": 401,
  "msg": "用户名或密码错误",
  "data": null
}
```

##### （3）返回参数说明

| 参数名               | 类型     | 备注                                |
| ----------------- | ------ | --------------------------------- |
| code              | int    | 状态码                               |
| msg               | String | 提示信息                              |
| data.accessToken  | String | 访问令牌                              |
| data.refreshToken | String | 刷新令牌                              |
| data.tokenType    | String | 令牌类型，固定为 `Bearer`                 |
| data.expiresIn    | int    | 访问令牌有效期，单位秒                       |
| data.sessionId    | String | 会话ID，对应 `iam_sessions.session_id` |
| data.user         | Object | 当前登录用户信息，对应 `iam_users`           |
| data.roles        | Array  | 当前用户角色列表                          |

#### 4. 异常状态码说明

| 状态码 | 说明      | 解决方案                            |
| --- | ------- | ------------------------------- |
| 400 | 参数错误    | 检查 `loginType`、`identity` 等参数   |
| 401 | 认证失败    | 检查账号、密码、验证码或微信授权码               |
| 403 | 账号不可用   | 检查用户状态是否为 `disabled` / `locked` |
| 409 | 认证方式未启用 | 检查对应身份标识是否启用                    |
| 500 | 服务器异常   | 联系后端排查                          |

#### 5. 调用示例

##### 请求示例

```json
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "loginType": "username",
  "identity": "superadmin",
  "credential": "123456",
  "deviceType": "web",
  "deviceId": "device_admin_web_001",
  "clientVersion": "1.0.0",
  "osName": "Windows 10",
  "browserName": "Chrome"
}
```

##### 返回示例

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "accessToken": "xxx",
    "refreshToken": "xxx",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "sessionId": "sess_admin_202604020001"
  }
}
```

---

### 3.2 用户登出接口

#### 1. 接口基础信息

* 接口名称：用户登出接口
* 接口路径：`/api/v1/auth/logout`
* 请求方式：`POST`
* 接口描述：当前登录用户退出系统，当前会话失效。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名       | 类型     | 必填 | 默认值  | 备注                    |
| --------- | ------ | -- | ---- | --------------------- |
| sessionId | String | 否  | 当前会话 | 需要显式登出的会话ID；不传则登出当前会话 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "登出成功",
  "data": {
    "sessionId": "sess_admin_202604020001",
    "sessionStatus": "logout",
    "logoutAt": "2026-04-02 10:30:00"
  }
}
```

##### （2）失败返回

```json
{
  "code": 401,
  "msg": "登录已失效",
  "data": null
}
```

##### （3）返回参数说明

| 参数名                | 类型     | 备注   |
| ------------------ | ------ | ---- |
| code               | int    | 状态码  |
| msg                | String | 提示信息 |
| data.sessionId     | String | 会话ID |
| data.sessionStatus | String | 会话状态 |
| data.logoutAt      | String | 登出时间 |

#### 4. 异常状态码说明

| 状态码 | 说明        | 解决方案           |
| --- | --------- | -------------- |
| 401 | 未登录或会话已失效 | 重新登录           |
| 404 | 会话不存在     | 检查 `sessionId` |
| 500 | 服务器异常     | 联系后端排查         |

#### 5. 调用示例

```json
POST /api/v1/auth/logout HTTP/1.1
Content-Type: application/json
Authorization: Bearer xxx

{
  "sessionId": "sess_admin_202604020001"
}
```

---

### 3.3 获取当前登录用户接口

#### 1. 接口基础信息

* 接口名称：获取当前登录用户接口
* 接口路径：`/api/v1/auth/me`
* 请求方式：`GET`
* 接口描述：获取当前登录用户信息、角色信息和当前会话信息。
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
    "user": {
      "id": 1,
      "userNo": "U20260001",
      "username": "superadmin",
      "nickname": "超级管理员",
      "realName": "系统管理员",
      "avatarUrl": null,
      "gender": 1,
      "phone": "13800000001",
      "email": "superadmin@example.com",
      "status": "active",
      "userType": "admin",
      "lastLoginAt": "2026-04-02 10:00:00",
      "lastLoginIp": "127.0.0.1"
    },
    "roles": [
      {
        "roleId": 1,
        "roleCode": "super_admin",
        "roleName": "超级管理员",
        "roleType": "system"
      }
    ],
    "permissions": [
      "user:manage",
      "platform_account:manage"
    ],
    "currentSession": {
      "sessionId": "sess_admin_202604020001",
      "loginType": "username",
      "deviceType": "web",
      "loginAt": "2026-04-02 10:00:00",
      "lastActiveAt": "2026-04-02 10:15:00",
      "expiredAt": "2026-04-09 10:00:00",
      "sessionStatus": "active"
    }
  }
}
```

##### （2）失败返回

```json
{
  "code": 401,
  "msg": "未登录或登录已失效",
  "data": null
}
```

##### （3）返回参数说明

| 参数名                 | 类型     | 备注                       |
| ------------------- | ------ | ------------------------ |
| data.user           | Object | 当前用户信息，对应 `iam_users`    |
| data.roles          | Array  | 当前用户角色列表                 |
| data.permissions    | Array  | 当前用户权限编码列表               |
| data.currentSession | Object | 当前会话信息，对应 `iam_sessions` |

#### 4. 异常状态码说明

| 状态码 | 说明        | 解决方案   |
| --- | --------- | ------ |
| 401 | 未登录或登录已失效 | 重新登录   |
| 500 | 服务器异常     | 联系后端排查 |

#### 5. 调用示例

```json
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer xxx
```

---

### 3.4 刷新Token接口

#### 1. 接口基础信息

* 接口名称：刷新Token接口
* 接口路径：`/api/v1/auth/refresh`
* 请求方式：`POST`
* 接口描述：使用刷新令牌刷新访问令牌，并延长当前会话有效期。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`

#### 2. 请求参数

| 参数名          | 类型     | 必填 | 默认值 | 备注   |
| ------------ | ------ | -- | --- | ---- |
| refreshToken | String | 是  | 无   | 刷新令牌 |
| sessionId    | String | 是  | 无   | 会话ID |
| deviceType   | String | 否  | 无   | 设备类型 |
| deviceId     | String | 否  | 无   | 设备标识 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "刷新成功",
  "data": {
    "accessToken": "new_access_token_xxx",
    "refreshToken": "new_refresh_token_xxx",
    "tokenType": "Bearer",
    "expiresIn": 7200,
    "sessionId": "sess_admin_202604020001"
  }
}
```

##### （2）失败返回

```json
{
  "code": 401,
  "msg": "刷新令牌无效或已过期",
  "data": null
}
```

##### （3）返回参数说明

| 参数名               | 类型     | 备注      |
| ----------------- | ------ | ------- |
| data.accessToken  | String | 新访问令牌   |
| data.refreshToken | String | 新刷新令牌   |
| data.tokenType    | String | 令牌类型    |
| data.expiresIn    | int    | 有效期，单位秒 |
| data.sessionId    | String | 会话ID    |

#### 4. 异常状态码说明

| 状态码 | 说明         | 解决方案                          |
| --- | ---------- | ----------------------------- |
| 400 | 参数错误       | 检查 `refreshToken`、`sessionId` |
| 401 | 刷新令牌无效或已过期 | 重新登录                          |
| 404 | 会话不存在      | 检查 `sessionId`                |
| 500 | 服务器异常      | 联系后端排查                        |

#### 5. 调用示例

```json
POST /api/v1/auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refreshToken": "refresh_xxx",
  "sessionId": "sess_admin_202604020001",
  "deviceType": "web",
  "deviceId": "device_admin_web_001"
}
```

---

### 3.5 用户列表接口

#### 1. 接口基础信息

* 接口名称：用户列表接口
* 接口路径：`/api/v1/iam/users`
* 请求方式：`GET`
* 接口描述：分页查询用户列表，支持按账号、状态、类型、角色筛选。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名      | 类型      | 必填 | 默认值 | 备注                                                               |
| -------- | ------- | -- | --- | ---------------------------------------------------------------- |
| keyword  | String  | 否  | 无   | 关键词，匹配 `username` / `nickname` / `real_name` / `phone` / `email` |
| status   | String  | 否  | 无   | 用户状态：`active` / `disabled` / `locked` / `pending`                |
| userType | String  | 否  | 无   | 用户类型：`normal` / `admin` / `designer` / `reviewer`                |
| roleCode | String  | 否  | 无   | 角色编码，如 `super_admin`                                             |
| pageNo   | Integer | 否  | 1   | 页码                                                               |
| pageSize | Integer | 否  | 20  | 每页数量                                                             |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "userNo": "U20260001",
        "username": "superadmin",
        "nickname": "超级管理员",
        "realName": "系统管理员",
        "phone": "13800000001",
        "email": "superadmin@example.com",
        "status": "active",
        "userType": "admin",
        "lastLoginAt": "2026-04-02 10:00:00",
        "roles": [
          {
            "roleId": 1,
            "roleCode": "super_admin",
            "roleName": "超级管理员"
          }
        ]
      }
    ],
    "pageNo": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

##### （2）失败返回

```json
{
  "code": 403,
  "msg": "无权限访问用户列表",
  "data": null
}
```

##### （3）返回参数说明

| 参数名           | 类型    | 备注   |
| ------------- | ----- | ---- |
| data.list     | Array | 用户列表 |
| data.pageNo   | int   | 当前页码 |
| data.pageSize | int   | 每页数量 |
| data.total    | int   | 总记录数 |

#### 4. 异常状态码说明

| 状态码 | 说明    | 解决方案    |
| --- | ----- | ------- |
| 401 | 未登录   | 重新登录    |
| 403 | 无权限   | 联系管理员授权 |
| 500 | 服务器异常 | 联系后端排查  |

#### 5. 调用示例

```json
GET /api/v1/iam/users?keyword=super&status=active&pageNo=1&pageSize=20 HTTP/1.1
Authorization: Bearer xxx
```

---

### 3.6 角色列表接口

#### 1. 接口基础信息

* 接口名称：角色列表接口
* 接口路径：`/api/v1/iam/roles`
* 请求方式：`GET`
* 接口描述：分页查询角色列表，支持按角色编码、类型、状态筛选。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名       | 类型      | 必填 | 默认值 | 备注                                    |
| --------- | ------- | -- | --- | ------------------------------------- |
| keyword   | String  | 否  | 无   | 匹配 `roleCode` / `roleName`            |
| roleType  | String  | 否  | 无   | 角色类型：`system` / `business` / `custom` |
| status    | String  | 否  | 无   | 角色状态：`active` / `disabled`            |
| isBuiltin | Integer | 否  | 无   | 是否系统内置：`0` / `1`                      |
| pageNo    | Integer | 否  | 1   | 页码                                    |
| pageSize  | Integer | 否  | 20  | 每页数量                                  |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "roleCode": "super_admin",
        "roleName": "超级管理员",
        "roleType": "system",
        "status": "active",
        "sortOrder": 1,
        "isBuiltin": 1,
        "description": "拥有系统全部管理权限"
      }
    ],
    "pageNo": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

##### （2）失败返回

```json
{
  "code": 403,
  "msg": "无权限访问角色列表",
  "data": null
}
```

##### （3）返回参数说明

| 参数名           | 类型    | 备注   |
| ------------- | ----- | ---- |
| data.list     | Array | 角色列表 |
| data.pageNo   | int   | 当前页码 |
| data.pageSize | int   | 每页数量 |
| data.total    | int   | 总记录数 |

#### 4. 异常状态码说明

| 状态码 | 说明    | 解决方案    |
| --- | ----- | ------- |
| 401 | 未登录   | 重新登录    |
| 403 | 无权限   | 联系管理员授权 |
| 500 | 服务器异常 | 联系后端排查  |

#### 5. 调用示例

```json
GET /api/v1/iam/roles?roleType=system&status=active&pageNo=1&pageSize=20 HTTP/1.1
Authorization: Bearer xxx
```

---

### 3.7 权限列表接口

#### 1. 接口基础信息

* 接口名称：权限列表接口
* 接口路径：`/api/v1/iam/permissions`
* 请求方式：`GET`
* 接口描述：分页查询权限列表，支持按模块、动作、类型、状态筛选。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

#### 2. 请求参数

| 参数名            | 类型      | 必填 | 默认值 | 备注                                      |
| -------------- | ------- | -- | --- | --------------------------------------- |
| keyword        | String  | 否  | 无   | 匹配 `permissionCode` / `permissionName`  |
| moduleCode     | String  | 否  | 无   | 模块编码，如 `task` / `review` / `workflow`   |
| actionCode     | String  | 否  | 无   | 动作编码，如 `create` / `approve`             |
| permissionType | String  | 否  | 无   | 权限类型：`menu` / `api` / `button` / `data` |
| status         | String  | 否  | 无   | 权限状态：`active` / `disabled`              |
| parentId       | Long    | 否  | 无   | 父权限ID                                   |
| pageNo         | Integer | 否  | 1   | 页码                                      |
| pageSize       | Integer | 否  | 20  | 每页数量                                    |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "list": [
      {
        "id": 1,
        "permissionCode": "user:manage",
        "permissionName": "用户管理",
        "moduleCode": "user",
        "actionCode": "manage",
        "permissionType": "api",
        "parentId": null,
        "path": "/api/v1/users",
        "status": "active",
        "sortOrder": 1,
        "isBuiltin": 1,
        "description": "用户管理相关权限"
      }
    ],
    "pageNo": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

##### （2）失败返回

```json
{
  "code": 403,
  "msg": "无权限访问权限列表",
  "data": null
}
```

##### （3）返回参数说明

| 参数名           | 类型    | 备注   |
| ------------- | ----- | ---- |
| data.list     | Array | 权限列表 |
| data.pageNo   | int   | 当前页码 |
| data.pageSize | int   | 每页数量 |
| data.total    | int   | 总记录数 |

#### 4. 异常状态码说明

| 状态码 | 说明    | 解决方案    |
| --- | ----- | ------- |
| 401 | 未登录   | 重新登录    |
| 403 | 无权限   | 联系管理员授权 |
| 500 | 服务器异常 | 联系后端排查  |

#### 5. 调用示例

```json
GET /api/v1/iam/permissions?moduleCode=task&permissionType=api&pageNo=1&pageSize=20 HTTP/1.1
Authorization: Bearer xxx
```

---

### 3.8 用户分配角色接口

#### 1. 接口基础信息

* 接口名称：用户分配角色接口
* 接口路径：`/api/v1/iam/users/{userId}/roles`
* 请求方式：`PUT`
* 接口描述：按用户维度覆盖更新角色关系，写入 `iam_user_roles`。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

路径参数：

| 参数名    | 类型   | 必填 | 默认值 | 备注                     |
| ------ | ---- | -- | --- | ---------------------- |
| userId | Long | 是  | 无   | 用户ID，对应 `iam_users.id` |

Body 参数：

| 参数名     | 类型          | 必填 | 默认值 | 备注               |
| ------- | ----------- | -- | --- | ---------------- |
| roleIds | Array<Long> | 是  | 无   | 目标角色ID列表，采用覆盖式分配 |
| remark  | String      | 否  | 无   | 分配备注             |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "分配成功",
  "data": {
    "userId": 2,
    "roleIds": [2, 4],
    "roles": [
      {
        "roleId": 2,
        "roleCode": "operator",
        "roleName": "运营人员"
      },
      {
        "roleId": 4,
        "roleCode": "reviewer",
        "roleName": "审核人员"
      }
    ]
  }
}
```

##### （2）失败返回

```json
{
  "code": 404,
  "msg": "用户不存在",
  "data": null
}
```

##### （3）返回参数说明

| 参数名          | 类型    | 备注        |
| ------------ | ----- | --------- |
| data.userId  | Long  | 用户ID      |
| data.roleIds | Array | 已分配角色ID列表 |
| data.roles   | Array | 角色详情列表    |

#### 4. 异常状态码说明

| 状态码 | 说明       | 解决方案                  |
| --- | -------- | --------------------- |
| 400 | 参数错误     | 检查 `roleIds` 是否为空     |
| 401 | 未登录      | 重新登录                  |
| 403 | 无权限      | 联系管理员授权               |
| 404 | 用户或角色不存在 | 检查 `userId`、`roleIds` |
| 409 | 角色状态不可分配 | 检查角色是否已禁用             |
| 500 | 服务器异常    | 联系后端排查                |

#### 5. 调用示例

```json
PUT /api/v1/iam/users/2/roles HTTP/1.1
Content-Type: application/json
Authorization: Bearer xxx

{
  "roleIds": [2, 4],
  "remark": "运营兼审核"
}
```

---

### 3.9 角色分配权限接口

#### 1. 接口基础信息

* 接口名称：角色分配权限接口
* 接口路径：`/api/v1/iam/roles/{roleId}/permissions`
* 请求方式：`PUT`
* 接口描述：按角色维度覆盖更新权限关系，写入 `iam_role_permissions`。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

#### 2. 请求参数

路径参数：

| 参数名    | 类型   | 必填 | 默认值 | 备注                     |
| ------ | ---- | -- | --- | ---------------------- |
| roleId | Long | 是  | 无   | 角色ID，对应 `iam_roles.id` |

Body 参数：

| 参数名           | 类型          | 必填 | 默认值 | 备注               |
| ------------- | ----------- | -- | --- | ---------------- |
| permissionIds | Array<Long> | 是  | 无   | 目标权限ID列表，采用覆盖式分配 |
| remark        | String      | 否  | 无   | 授权备注             |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "授权成功",
  "data": {
    "roleId": 2,
    "permissionIds": [2, 3],
    "permissions": [
      {
        "permissionId": 2,
        "permissionCode": "task:create",
        "permissionName": "创建任务"
      },
      {
        "permissionId": 3,
        "permissionCode": "review:approve",
        "permissionName": "审核通过"
      }
    ]
  }
}
```

##### （2）失败返回

```json
{
  "code": 404,
  "msg": "角色不存在",
  "data": null
}
```

##### （3）返回参数说明

| 参数名                | 类型    | 备注        |
| ------------------ | ----- | --------- |
| data.roleId        | Long  | 角色ID      |
| data.permissionIds | Array | 已授权权限ID列表 |
| data.permissions   | Array | 权限详情列表    |

#### 4. 异常状态码说明

| 状态码 | 说明       | 解决方案                        |
| --- | -------- | --------------------------- |
| 400 | 参数错误     | 检查 `permissionIds`          |
| 401 | 未登录      | 重新登录                        |
| 403 | 无权限      | 联系管理员授权                     |
| 404 | 角色或权限不存在 | 检查 `roleId`、`permissionIds` |
| 409 | 权限状态不可分配 | 检查权限是否已禁用                   |
| 500 | 服务器异常    | 联系后端排查                      |

#### 5. 调用示例

```json
PUT /api/v1/iam/roles/2/permissions HTTP/1.1
Content-Type: application/json
Authorization: Bearer xxx

{
  "permissionIds": [2, 3],
  "remark": "补充任务与审核权限"
}
```

---

### 3.10 会话列表 / 强制下线接口

#### 3.10.1 会话列表接口

##### 1. 接口基础信息

* 接口名称：会话列表接口
* 接口路径：`/api/v1/iam/sessions`
* 请求方式：`GET`
* 接口描述：分页查询登录会话列表，支持按用户、登录方式、设备类型、状态筛选。
* 版本号：`v1`
* 请求头：

  * `Authorization: Bearer {token}`

##### 2. 请求参数

| 参数名           | 类型      | 必填 | 默认值 | 备注                                               |
| ------------- | ------- | -- | --- | ------------------------------------------------ |
| userId        | Long    | 否  | 无   | 用户ID                                             |
| loginType     | String  | 否  | 无   | 登录方式：`username` / `phone` / `email` / `wechat`   |
| deviceType    | String  | 否  | 无   | 设备类型：`web` / `mobile` / `miniapp`                |
| sessionStatus | String  | 否  | 无   | 会话状态：`active` / `expired` / `revoked` / `logout` |
| pageNo        | Integer | 否  | 1   | 页码                                               |
| pageSize      | Integer | 否  | 20  | 每页数量                                             |

##### 3. 返回参数

###### （1）成功返回

```json
{
  "code": 200,
  "msg": "查询成功",
  "data": {
    "list": [
      {
        "sessionId": "sess_operator_202604020001",
        "userId": 2,
        "identityId": 2,
        "loginType": "phone",
        "deviceType": "web",
        "deviceId": "device_operator_web_001",
        "clientVersion": "1.0.0",
        "osName": "Windows 10",
        "browserName": "Chrome",
        "ipAddress": "127.0.0.1",
        "ipLocation": "本地开发环境",
        "loginAt": "2026-04-02 09:30:00",
        "lastActiveAt": "2026-04-02 09:50:00",
        "expiredAt": "2026-04-09 09:30:00",
        "logoutAt": null,
        "sessionStatus": "active"
      }
    ],
    "pageNo": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

###### （2）失败返回

```json
{
  "code": 403,
  "msg": "无权限访问会话列表",
  "data": null
}
```

###### （3）返回参数说明

| 参数名           | 类型    | 备注   |
| ------------- | ----- | ---- |
| data.list     | Array | 会话列表 |
| data.pageNo   | int   | 当前页码 |
| data.pageSize | int   | 每页数量 |
| data.total    | int   | 总记录数 |

##### 4. 异常状态码说明

| 状态码 | 说明    | 解决方案    |
| --- | ----- | ------- |
| 401 | 未登录   | 重新登录    |
| 403 | 无权限   | 联系管理员授权 |
| 500 | 服务器异常 | 联系后端排查  |

##### 5. 调用示例

```json
GET /api/v1/iam/sessions?userId=2&sessionStatus=active&pageNo=1&pageSize=20 HTTP/1.1
Authorization: Bearer xxx
```

#### 3.10.2 强制下线接口

##### 1. 接口基础信息

* 接口名称：强制下线接口
* 接口路径：`/api/v1/iam/sessions/force-logout`
* 请求方式：`POST`
* 接口描述：强制指定会话失效，将 `iam_sessions.session_status` 更新为 `revoked`，并记录失效原因。
* 版本号：`v1`
* 请求头：

  * `Content-Type: application/json`
  * `Authorization: Bearer {token}`

##### 2. 请求参数

| 参数名          | 类型     | 必填 | 默认值 | 备注     |
| ------------ | ------ | -- | --- | ------ |
| sessionId    | String | 是  | 无   | 会话ID   |
| revokeReason | String | 是  | 无   | 强制下线原因 |

##### 3. 返回参数

###### （1）成功返回

```json
{
  "code": 200,
  "msg": "强制下线成功",
  "data": {
    "sessionId": "sess_operator_202604020001",
    "sessionStatus": "revoked",
    "revokeReason": "管理员强制下线",
    "logoutAt": "2026-04-02 11:00:00"
  }
}
```

###### （2）失败返回

```json
{
  "code": 404,
  "msg": "会话不存在",
  "data": null
}
```

###### （3）返回参数说明

| 参数名                | 类型     | 备注     |
| ------------------ | ------ | ------ |
| data.sessionId     | String | 会话ID   |
| data.sessionStatus | String | 会话状态   |
| data.revokeReason  | String | 强制下线原因 |
| data.logoutAt      | String | 强制下线时间 |

##### 4. 异常状态码说明

| 状态码 | 说明    | 解决方案                          |
| --- | ----- | ----------------------------- |
| 400 | 参数错误  | 检查 `sessionId`、`revokeReason` |
| 401 | 未登录   | 重新登录                          |
| 403 | 无权限   | 联系管理员授权                       |
| 404 | 会话不存在 | 检查 `sessionId`                |
| 409 | 会话已失效 | 无需重复操作                        |
| 500 | 服务器异常 | 联系后端排查                        |

##### 5. 调用示例

```json
POST /api/v1/iam/sessions/force-logout HTTP/1.1
Content-Type: application/json
Authorization: Bearer xxx

{
  "sessionId": "sess_operator_202604020001",
  "revokeReason": "管理员强制下线"
}
```
---

### 3.11 发送验证码接口

#### 1. 接口基础信息

* 接口名称：发送验证码接口
* 接口路径：
  * 邮箱：`/api/v1/auth/email/send-code`
  * 短信：`/api/v1/auth/sms/send-code`
* 请求方式：`POST`
* 接口描述：向指定邮箱或手机号发送验证码，用于登录、注册或重置密码。
* 版本号：`v1`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| email / phone | String | 是 | 无 | 目标邮箱或手机号 |
| scene | String | 否 | `login` | 业务场景：`login` / `register` / `reset_pwd` |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "验证码发送成功",
  "data": {
    "target": "user@example.com",
    "scene": "login",
    "expireSeconds": 600,
    "debugCode": "123456"
  }
}
```

##### （2）返回参数说明

| 参数名 | 类型 | 备注 |
| :--- | :--- | :--- |
| data.target | String | 接收目标 |
| data.scene | String | 业务场景 |
| data.expireSeconds | Integer | 有效期（秒） |
| data.debugCode | String | 开发环境返回的验证码（仅 dev 环境） |

---

### 3.12 校验验证码接口

#### 1. 接口基础信息

* 接口名称：校验验证码接口
* 接口路径：
  * 邮箱：`/api/v1/auth/email/verify-code`
  * 短信：`/api/v1/auth/sms/verify-code`
* 请求方式：`POST`
* 接口描述：校验用户输入的验证码是否正确及有效。
* 版本号：`v1`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| email / phone | String | 是 | 无 | 目标邮箱或手机号 |
| code | String | 是 | 无 | 用户输入的验证码 |
| scene | String | 否 | `login` | 业务场景 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "校验成功",
  "data": {
    "target": "user@example.com",
    "scene": "login",
    "verified": true
  }
}
```

---

### 3.13 用户注册接口

#### 1. 接口基础信息

* 接口名称：用户注册接口
* 接口路径：
  * 邮箱注册：`/api/v1/auth/register/email`
  * 手机注册：`/api/v1/auth/register/phone`
* 请求方式：`POST`
* 接口描述：通过验证码完成新用户注册。
* 版本号：`v1`

#### 2. 请求参数

| 参数名 | 类型 | 必填 | 备注 |
| :--- | :--- | :--- | :--- |
| email / phone | String | 是 | 注册标识 |
| code | String | 是 | 校验码 |
| password | String | 否 | 设置密码 |
| username | String | 否 | 用户名 |
| nickname | String | 否 | 昵称 |

#### 3. 返回参数

##### （1）成功返回

```json
{
  "code": 200,
  "msg": "注册成功",
  "data": {
    "user": {
      "id": 10,
      "username": "newuser",
      "nickname": "新用户",
      "status": "active"
    },
    "identityType": "email",
    "identity": "user@example.com"
  }
}
```

---

这 13 个接口现在已经完成了完整的身份权限域闭环，路径、对象和字段命名都和当前设计保持一致。
