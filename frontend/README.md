# Frontend

`frontend/` 是当前在维护的 Vue 3 + Vite 前端工程。

## 目录说明

- `src/`
  主前端源码，当前开发都以这里为准。
- `public/`
  静态资源。
- `scripts/`
  页面截图、对比等辅助脚本。
- `dist/`
  构建产物，可重新生成，不作为手工维护目录。

## 关键页面

- 口播数字人创作台：
  `src/views/CreationAvatarView.vue`

## 启动方式

```powershell
npm install
npm run dev
```

如需指定主后端地址：

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## 清理约定

- `dist/`、截图、调试日志、一次性测试脚本不长期保留。
- `test_fetch.js` 这类手工联调文件如果没有持续用途，应优先清理。
- 页面说明优先写回组件附近或本 README，不单独散落在临时文本中。
