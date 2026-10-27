# 视频剪辑数字人后端接口契约

## 当前主草稿

- 主草稿接口：`/api/v1/avatar-clip-drafts`
- 兼容镜像：`/api/v1/creation-drafts`
- 同一条剪辑草稿在两张表里共用同一个 `draft_id`

当前建议：

- 剪辑数字人页面新增、保存、读取、渲染、播放统一依赖 `avatar-clip-drafts`
- `creation-drafts` 仅保留为兼容镜像，供旧链路和通用分发逻辑继续读取

## 推荐接口

1. `POST /api/v1/avatar-clip-drafts`
2. `PATCH /api/v1/avatar-clip-drafts/{draft_id}`
3. `GET /api/v1/avatar-clip-drafts/{draft_id}`
4. `GET /api/v1/avatar-clip-drafts`
5. `POST /api/v1/avatar-clip-drafts/{draft_id}/clip-render`
6. `GET /api/v1/avatar-clip-drafts/{draft_id}/clipped-video`

## 前端最小依赖字段

- `draft_id`
- `title`
- `status`
- `rewritten_copy`
- `voice_params`
- `digital_human_params`
- `clip_params`
- `selected_product_id`
- `selected_product_profile`
- `selected_selling_point_ids`
- `selected_clip_asset_ids`
- `selected_reference_asset_ids`
- `material_summary`
- `script_style`
- `duration_seconds`
- `render_plan`
- `output_url`

## `clip_params` 统一字段

输入配置字段：

- `subtitle_mode`
- `background_mode`
- `title_template`
- `overlay_title`
- `overlay_subtitle`
- `overlay_tag`
- `voice_volume`
- `bgm_mode`
- `bgm_asset_url`
- `bgm_volume`
- `render_plan`

输出结果字段：

- `clipped_video_url`
- `clipped_video_playback_path`
- `playback_requires_auth`
- `playback_path`
- `output_url`

约定：

- `playback_path` / `output_url` 表示前端可直接用于预览的最终播放地址
- 若 `playback_requires_auth=true`，优先使用 `clipped_video_playback_path`
- 若 `playback_requires_auth=false`，优先使用 `clipped_video_url`

## 渲染接口

`POST /api/v1/avatar-clip-drafts/{draft_id}/clip-render`

请求体：

```json
{
  "segments": [
    { "start": 0, "end": 2.5, "text": "..." }
  ]
}
```

说明：

- `segments` 可选
- 有值时优先使用前端传入的时间轴
- 无值时后端按 `rewritten_copy`、`transcript.segments`、音频时长自动兜底

响应体重点：

```json
{
  "draft": {
    "draft_id": "draft_xxx",
    "clip_params": {
      "clipped_video_url": "...",
      "clipped_video_playback_path": "/api/v1/avatar-clip-drafts/draft_xxx/clipped-video",
      "playback_requires_auth": true,
      "playback_path": "/api/v1/avatar-clip-drafts/draft_xxx/clipped-video",
      "output_url": "/api/v1/avatar-clip-drafts/draft_xxx/clipped-video"
    }
  },
  "srt_preview": "...",
  "playback_requires_auth": true
}
```

## 已知兼容层

- `avatar-clip-drafts` 保存时仍会镜像同步到 `creation-drafts`
- 分发服务当前仍从 `creation-drafts` 取视频地址
- 历史 `content_info.product_marketing_video` 仍可能存在，但不再作为渲染主契约
