-- 数字人草稿箱主表迁移 SQL
-- 目标：
-- 1. 建立统一草稿索引主表 avatar_drafts
-- 2. 为现有 creation_drafts 回填草稿箱索引
-- 3. 支持按用户 + 场景快速查询草稿箱

CREATE TABLE IF NOT EXISTS `avatar_drafts` (
  `draft_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '草稿ID，数字人草稿全局唯一主键',
  `user_id` bigint unsigned NOT NULL COMMENT '所属用户ID',
  `scene_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '场景编码：talk/sales/product/model',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '草稿标题，用于草稿箱列表展示',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT '草稿状态：draft/rewritten/gallery_generated/completed 等',
  `current_step_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '当前步骤编码，用于恢复用户所在步骤',
  `progress` int DEFAULT NULL COMMENT '步骤进度，建议范围 0-100',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0 未删除，1 已删除',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`draft_id`),
  KEY `idx_avatar_drafts_user_scene_updated` (`user_id`,`scene_code`,`updated_at`),
  KEY `idx_avatar_drafts_user_updated` (`user_id`,`updated_at`),
  KEY `idx_avatar_drafts_scene_status` (`scene_code`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字人草稿箱主表';

-- 基础回填：
-- 这里按 digital_human_params.video_purpose 做显式映射。
-- 更复杂的历史脏数据修复由应用层回填逻辑处理。
INSERT INTO `avatar_drafts` (
  `draft_id`,
  `user_id`,
  `scene_code`,
  `title`,
  `status`,
  `current_step_code`,
  `progress`,
  `is_deleted`,
  `created_at`,
  `updated_at`
)
SELECT
  cd.`id` AS `draft_id`,
  cd.`user_id`,
  CASE JSON_UNQUOTE(JSON_EXTRACT(cd.`digital_human_params`, '$.video_purpose'))
    WHEN '口播数字人' THEN 'talk'
    WHEN '卖货数字人' THEN 'sales'
    WHEN '带货数字人' THEN 'sales'
    WHEN '产品介绍数字人' THEN 'product'
    WHEN '模特数字人' THEN 'model'
    ELSE 'talk'
  END AS `scene_code`,
  cd.`title`,
  cd.`status`,
  CASE
    WHEN LOWER(cd.`status`) IN ('draft', 'extracted') THEN 'copywriting'
    WHEN LOWER(cd.`status`) = 'rewritten' THEN 'rewrite'
    WHEN LOWER(cd.`status`) LIKE '%voice%' THEN 'voice'
    WHEN LOWER(cd.`status`) LIKE '%video%' THEN 'digital_human'
    WHEN LOWER(cd.`status`) IN ('completed', 'gallery_generated') THEN 'completed'
    ELSE NULL
  END AS `current_step_code`,
  CASE
    WHEN LOWER(cd.`status`) = 'draft' THEN 10
    WHEN LOWER(cd.`status`) = 'extracted' THEN 25
    WHEN LOWER(cd.`status`) = 'rewritten' THEN 45
    WHEN LOWER(cd.`status`) LIKE '%voice%' THEN 60
    WHEN LOWER(cd.`status`) LIKE '%video%' THEN 80
    WHEN LOWER(cd.`status`) IN ('completed', 'gallery_generated') THEN 100
    ELSE NULL
  END AS `progress`,
  0 AS `is_deleted`,
  cd.`created_at`,
  cd.`updated_at`
FROM `creation_drafts` cd
ON DUPLICATE KEY UPDATE
  `user_id` = VALUES(`user_id`),
  `scene_code` = VALUES(`scene_code`),
  `title` = VALUES(`title`),
  `status` = VALUES(`status`),
  `current_step_code` = VALUES(`current_step_code`),
  `progress` = VALUES(`progress`),
  `is_deleted` = VALUES(`is_deleted`),
  `updated_at` = VALUES(`updated_at`);
