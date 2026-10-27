-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: ai_content_automation
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agent_checkpoint_writes`
--

DROP TABLE IF EXISTS `agent_checkpoint_writes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_checkpoint_writes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `thread_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话线程 ID',
  `checkpoint_ns` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '检查点命名空间',
  `checkpoint_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联的检查点 ID',
  `task_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务 ID',
  `task_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '任务路径',
  `idx` int NOT NULL COMMENT '写入序号',
  `channel` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通道名称',
  `type` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '写入类型',
  `blob` longblob COMMENT '序列化的写入数据',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_write` (`thread_id`(64),`checkpoint_ns`(64),`checkpoint_id`(64),`task_id`(64),`idx`),
  KEY `idx_checkpoint` (`thread_id`(64),`checkpoint_ns`(64),`checkpoint_id`(64))
) ENGINE=InnoDB AUTO_INCREMENT=379 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LangGraph Agent 检查点中间写入';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_checkpoints`
--

DROP TABLE IF EXISTS `agent_checkpoints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_checkpoints` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联用户 ID',
  `thread_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话线程 ID',
  `checkpoint_ns` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '检查点命名空间',
  `checkpoint_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检查点 ID (UUID)',
  `parent_checkpoint_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '父检查点 ID',
  `checkpoint` longblob NOT NULL COMMENT '序列化的检查点数据',
  `metadata` longblob COMMENT '检查点元数据',
  `channel_versions` json DEFAULT NULL COMMENT '通道版本信息',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_checkpoint` (`thread_id`(64),`checkpoint_ns`(64),`checkpoint_id`(64)),
  KEY `idx_thread_ns` (`thread_id`(64),`checkpoint_ns`(64)),
  KEY `idx_parent` (`parent_checkpoint_id`),
  KEY `idx_created` (`created_at`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=256 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LangGraph Agent 检查点存储';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_session_messages`
--

DROP TABLE IF EXISTS `agent_session_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_session_messages` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `message_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息 ID (UUID)',
  `session_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联会话 ID',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色: user/assistant/system',
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `segments_json` json DEFAULT NULL COMMENT '消息 segments 元数据 (thinking, tool_call 等)',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `message_id` (`message_id`),
  KEY `idx_session` (`session_id`),
  KEY `idx_session_time` (`session_id`,`created_at`),
  CONSTRAINT `agent_session_messages_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `agent_sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 会话消息历史';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_sessions`
--

DROP TABLE IF EXISTS `agent_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_sessions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `session_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话 ID (UUID)',
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联用户 ID',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '新对话' COMMENT '会话标题',
  `first_message` text COLLATE utf8mb4_unicode_ci COMMENT '首条消息内容',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `llm_config_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'LLM config name used for this session',
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_id` (`session_id`),
  KEY `idx_updated` (`updated_at` DESC),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 会话元数据';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_store`
--

DROP TABLE IF EXISTS `agent_store`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_store` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联用户 ID',
  `namespace` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '命名空间 (JSON 数组序列化)',
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '存储键',
  `value` longblob NOT NULL COMMENT '存储值 (JSON)',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ns_key` (`namespace`(191),`key`),
  KEY `idx_updated` (`updated_at`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LangGraph Agent 长期记忆存储';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_token_usage_logs`
--

DROP TABLE IF EXISTS `ai_token_usage_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_token_usage_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned NOT NULL COMMENT '消耗归属用户ID（iam_users.id）',
  `task_id` varchar(64) DEFAULT NULL COMMENT '关联任务ID（tasks.id）',
  `scene` varchar(64) NOT NULL COMMENT '调用场景，如 rewrite_analyze/rewrite_generate',
  `provider_code` varchar(32) NOT NULL COMMENT '模型供应商编码',
  `model_name` varchar(128) NOT NULL COMMENT '模型名',
  `input_tokens` int NOT NULL DEFAULT '0' COMMENT '输入token',
  `output_tokens` int NOT NULL DEFAULT '0' COMMENT '输出token',
  `cached_tokens` int NOT NULL DEFAULT '0' COMMENT '缓存命中token',
  `total_tokens` int NOT NULL DEFAULT '0' COMMENT '总token',
  `estimated_cost` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '估算成本',
  `currency` varchar(16) NOT NULL DEFAULT 'CNY' COMMENT '币种',
  `request_id` varchar(128) DEFAULT NULL COMMENT '请求链路ID',
  `remark` text COMMENT '备注',
  `metadata_json` json DEFAULT NULL COMMENT '扩展信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_token_usage_logs_user_created` (`user_id`,`created_at`),
  KEY `idx_ai_token_usage_logs_task` (`task_id`),
  KEY `idx_ai_token_usage_logs_scene` (`scene`),
  KEY `idx_ai_token_usage_logs_request` (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI token 消耗日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `avatar_drafts`
--

DROP TABLE IF EXISTS `avatar_drafts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `avatar_drafts` (
  `draft_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '草稿ID，数字人草稿全局唯一主键',
  `user_id` bigint unsigned NOT NULL COMMENT '所属用户ID',
  `scene_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数字人场景编码，如 talk/sales/product/model',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '草稿标题，用于草稿箱列表展示',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT '草稿状态，如 draft/rewritten/video_generating/completed/failed',
  `current_step_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '当前流程步骤编码，用于前端恢复当前所处模块',
  `progress` int DEFAULT NULL COMMENT '当前流程进度，建议范围 0-100',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0未删除，1已删除',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`draft_id`),
  KEY `idx_avatar_drafts_user_scene_updated` (`user_id`,`scene_code`,`updated_at`),
  KEY `idx_avatar_drafts_user_updated` (`user_id`,`updated_at`),
  KEY `idx_avatar_drafts_scene_status` (`scene_code`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字人草稿主表，负责统一记录用户草稿索引信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `background_assets`
--

DROP TABLE IF EXISTS `background_assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `background_assets` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `media_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `asset_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `thumbnail_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `sort_order` int NOT NULL DEFAULT '0',
  `is_deleted` tinyint NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_background_assets_user_id` (`user_id`),
  KEY `idx_background_assets_media_type` (`media_type`),
  KEY `idx_background_assets_source_type` (`source_type`),
  KEY `idx_background_assets_status` (`status`),
  KEY `idx_background_assets_is_deleted` (`is_deleted`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bilibili_up_info`
--

DROP TABLE IF EXISTS `bilibili_up_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bilibili_up_info` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `follower_count` bigint DEFAULT NULL COMMENT '粉丝数',
  `following_count` bigint DEFAULT NULL COMMENT '关注数',
  `content_count` bigint DEFAULT NULL COMMENT '作品数',
  `description` longtext COMMENT '用户描述',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_bilibili_vi_user_123456` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='B站UP主信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bilibili_video`
--

DROP TABLE IF EXISTS `bilibili_video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bilibili_video` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `video_id` varchar(64) NOT NULL COMMENT '视频ID (aid)',
  `bvid` varchar(64) DEFAULT NULL COMMENT '视频ID (bvid)',
  `video_type` varchar(16) NOT NULL COMMENT '视频类型',
  `title` varchar(500) DEFAULT NULL COMMENT '视频标题',
  `desc` longtext COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) DEFAULT NULL COMMENT '视频点赞数',
  `video_play_count` varchar(16) DEFAULT NULL COMMENT '视频播放数量',
  `video_danmaku` varchar(16) DEFAULT NULL COMMENT '视频弹幕数量',
  `video_comment` varchar(16) DEFAULT NULL COMMENT '视频评论数量',
  `video_url` varchar(512) DEFAULT NULL COMMENT '视频详情URL',
  `video_cover_url` varchar(512) DEFAULT NULL COMMENT '视频封面图 URL',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  `duration` varchar(16) DEFAULT NULL COMMENT '视频时长',
  PRIMARY KEY (`id`),
  KEY `idx_bilibili_vi_video_i_31c36e` (`video_id`),
  KEY `idx_bilibili_vi_create__73e0ec` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='B站视频';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bilibili_video_comment`
--

DROP TABLE IF EXISTS `bilibili_video_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bilibili_video_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `video_id` varchar(64) NOT NULL COMMENT '视频ID',
  `content` longtext COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) NOT NULL COMMENT '评论回复数',
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(255) NOT NULL DEFAULT '0' COMMENT '点赞数',
  PRIMARY KEY (`id`),
  KEY `idx_bilibili_vi_comment_41c34e` (`comment_id`),
  KEY `idx_bilibili_vi_video_i_f22873` (`video_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='B 站视频评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `brand_products`
--

DROP TABLE IF EXISTS `brand_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brand_products` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned NOT NULL COMMENT '归属系统用户ID',
  `brand_name` varchar(64) NOT NULL COMMENT '品牌名称',
  `product_name` varchar(128) NOT NULL COMMENT '产品/生产线名称',
  `positioning` text COMMENT '产品定位',
  `target_audience` text COMMENT '目标人群',
  `scenarios` text COMMENT '适用场景',
  `tone_voice` varchar(255) DEFAULT NULL COMMENT '整体调性',
  `forbidden_phrases` json DEFAULT NULL COMMENT '禁用表达/风险词',
  `cover_url` varchar(512) DEFAULT NULL COMMENT '档案封面图片URL',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_brand_products_user_brand` (`user_id`,`brand_name`),
  KEY `idx_brand_products_product_name` (`product_name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='品牌研究域-品牌产品档案表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `brand_selling_points`
--

DROP TABLE IF EXISTS `brand_selling_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brand_selling_points` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `product_id` bigint unsigned NOT NULL COMMENT '所属产品ID',
  `title` varchar(255) NOT NULL COMMENT '卖点标题',
  `description` text COMMENT '卖点详细描述',
  `type` varchar(32) NOT NULL DEFAULT 'optional' COMMENT '卖点类型：required/optional/forbidden',
  `weight` int NOT NULL DEFAULT '5' COMMENT '权重/评分 (0-10)',
  `source` varchar(32) NOT NULL DEFAULT 'manual' COMMENT '来源：manual/ai/external',
  `status` varchar(32) NOT NULL DEFAULT 'confirmed' COMMENT '状态：draft/confirmed/pending_confirm',
  `platforms` json DEFAULT NULL COMMENT '适用平台数组',
  `applicable_scenarios` json DEFAULT NULL COMMENT '适用场景数组',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_brand_selling_points_product_type` (`product_id`,`type`),
  KEY `idx_brand_selling_points_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='品牌研究域-营销卖点库';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `brand_visual_assets`
--

DROP TABLE IF EXISTS `brand_visual_assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brand_visual_assets` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `product_id` bigint unsigned NOT NULL COMMENT '所属产品ID',
  `asset_type` varchar(32) NOT NULL COMMENT '素材类型：brand_logo/product_ui/promo_img/video_asset',
  `asset_url` varchar(512) NOT NULL COMMENT '素材资源URL',
  `thumbnail_url` varchar(512) DEFAULT NULL COMMENT '缩略图URL',
  `tags` json DEFAULT NULL COMMENT '标签数组',
  `platforms` json DEFAULT NULL COMMENT '适用平台数组',
  `applicable_scenarios` json DEFAULT NULL COMMENT '适用场景数组',
  `usable_for_cover` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否可用作封面',
  `usable_for_video` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否可用作视频素材',
  `extra_data` json DEFAULT NULL COMMENT '其他元数据',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_brand_visual_assets_product_asset_type` (`product_id`,`asset_type`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='品牌研究域-视觉素材库';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crawler_cookie_account_bindings`
--

DROP TABLE IF EXISTS `crawler_cookie_account_bindings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crawler_cookie_account_bindings` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_user_id` bigint unsigned NOT NULL COMMENT '主程序用户ID',
  `platform_code` varchar(32) NOT NULL COMMENT '主程序平台编码，例如 douyin',
  `platform_account_id` bigint unsigned DEFAULT NULL COMMENT 'platform_accounts.id，可为空',
  `crawler_cookie_account_id` bigint unsigned NOT NULL COMMENT 'crawler_cookies_account.id',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '绑定状态：active/disabled',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否默认使用',
  `priority` int NOT NULL DEFAULT '100' COMMENT '优先级，数值越小越优先',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ccab_user_platform_crawler` (`owner_user_id`,`platform_code`,`crawler_cookie_account_id`),
  KEY `idx_ccab_user_platform_status` (`owner_user_id`,`platform_code`,`status`,`is_default`,`priority`),
  KEY `idx_ccab_platform_account` (`platform_account_id`),
  KEY `idx_ccab_crawler_cookie_account` (`crawler_cookie_account_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='主程序用户与爬虫 Cookie 账号绑定表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `crawler_cookies_account`
--

DROP TABLE IF EXISTS `crawler_cookies_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crawler_cookies_account` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `account_name` varchar(64) NOT NULL DEFAULT '' COMMENT '账号名称',
  `platform_name` varchar(64) NOT NULL DEFAULT '' COMMENT '平台名称 (xhs | dy | ks | wb | bili | tieba)',
  `cookies` text COMMENT '对应自媒体平台登录成功后的cookies',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '该条记录的创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '该条记录的更新时间',
  `invalid_timestamp` bigint unsigned NOT NULL DEFAULT '0' COMMENT '账号失效时间戳',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '账号状态枚举值(0：有效，-1：无效)',
  PRIMARY KEY (`id`),
  KEY `idx_crawler_cookies_account_01` (`update_time`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='爬虫采集账号表（cookies）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `creation_drafts`
--

DROP TABLE IF EXISTS `creation_drafts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `creation_drafts` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '主键，业务草稿ID（如 draft_xxx）',
  `user_id` bigint NOT NULL COMMENT '所属用户ID',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '草稿标题，常取自内容标题',
  `source_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '01 输入：社媒内容页/作品链接',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台标识，如 dy/xhs/bilibili/ks',
  `content_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '平台侧内容ID，可与 content_info 内冗余字段对应',
  `content_info` json NOT NULL COMMENT '01 DownloadServer 解析结果：标题/描述/作者/封面与音视频URL等',
  `transcript` json NOT NULL COMMENT '01 原素材 ASR：{text, segments[{start,end秒},text], content_id}；非数字人成片口播时间轴',
  `extracted_copy` text COLLATE utf8mb4_unicode_ci COMMENT '01 LLM 整理后的原始口播/文案正文',
  `rewrite_instruction` text COLLATE utf8mb4_unicode_ci COMMENT '02 改写附加说明/模板指令',
  `rewritten_copy` text COLLATE utf8mb4_unicode_ci COMMENT '02 改写后的正文，供TTS与数字人',
  `voice_params` json NOT NULL COMMENT '03 口播/TTS：音色、语速、各阶段音频URL(local/source/minio等)、record_id',
  `digital_human_params` json NOT NULL COMMENT '04 数字人：模板/场景、任务状态、模板或成片 video/image URL（含公网签名链）',
  `clip_params` json NOT NULL COMMENT '05 剪辑与成片选项：subtitle_mode、bgm、音量等；路径乙不在此持久化成片SRT',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '草稿状态：draft/extracted/rewritten 等',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间（UTC 或会话时区，以库配置为准）',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_creation_drafts_user_id` (`user_id`),
  KEY `idx_creation_drafts_status` (`status`),
  KEY `idx_creation_drafts_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='创作草稿：01链接与元数据、原片ASR转录、改写文案、口播与数字人成片参数、剪辑策略；成片口播SRT可走路径乙不落库';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `douyin_aweme`
--

DROP TABLE IF EXISTS `douyin_aweme`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `douyin_aweme` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `sec_uid` varchar(128) DEFAULT NULL COMMENT '用户sec_uid',
  `short_user_id` varchar(64) DEFAULT NULL COMMENT '用户短ID',
  `user_unique_id` varchar(64) DEFAULT NULL COMMENT '用户唯一ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `user_signature` varchar(500) DEFAULT NULL COMMENT '用户签名',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `aweme_id` varchar(64) NOT NULL COMMENT '视频ID',
  `aweme_type` varchar(16) NOT NULL COMMENT '视频类型',
  `title` varchar(1024) DEFAULT NULL COMMENT '视频标题',
  `desc` longtext COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) DEFAULT NULL COMMENT '视频点赞数',
  `video_play_count` varchar(16) DEFAULT NULL COMMENT '视频播放/浏览数',
  `comment_count` varchar(16) DEFAULT NULL COMMENT '视频评论数',
  `share_count` varchar(16) DEFAULT NULL COMMENT '视频分享数',
  `collected_count` varchar(16) DEFAULT NULL COMMENT '视频收藏数',
  `aweme_url` varchar(255) DEFAULT NULL COMMENT '视频详情页URL',
  `cover_url` longtext COMMENT '视频封面图URL或图文图片URL列表',
  `video_download_url` varchar(1024) DEFAULT NULL COMMENT '视频下载地址',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  `is_ai_generated` tinyint(1) NOT NULL DEFAULT '0' COMMENT '作者是否声明视频为AI生成',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_aweme_id` (`aweme_id`),
  KEY `idx_douyin_awem_aweme_i_6f7bc6` (`aweme_id`),
  KEY `idx_douyin_awem_create__299dfe` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=664 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='抖音视频';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `douyin_aweme_comment`
--

DROP TABLE IF EXISTS `douyin_aweme_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `douyin_aweme_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `sec_uid` varchar(128) DEFAULT NULL COMMENT '用户sec_uid',
  `short_user_id` varchar(64) DEFAULT NULL COMMENT '用户短ID',
  `user_unique_id` varchar(64) DEFAULT NULL COMMENT '用户唯一ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `user_signature` varchar(500) DEFAULT NULL COMMENT '用户签名',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `aweme_id` varchar(64) NOT NULL COMMENT '视频ID',
  `content` longtext COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) NOT NULL COMMENT '评论回复数',
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(255) NOT NULL DEFAULT '0' COMMENT '点赞数',
  `pictures` varchar(500) NOT NULL DEFAULT '' COMMENT '评论图片列表',
  `reply_to_reply_id` varchar(64) DEFAULT NULL COMMENT '目标评论ID',
  PRIMARY KEY (`id`),
  KEY `idx_douyin_awem_comment_fcd7e4` (`comment_id`),
  KEY `idx_douyin_awem_aweme_i_c50049` (`aweme_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10136 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='抖音视频评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `douyin_hot_rank_items`
--

DROP TABLE IF EXISTS `douyin_hot_rank_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `douyin_hot_rank_items` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `platform` varchar(32) NOT NULL DEFAULT 'douyin' COMMENT '平台来源',
  `board_type` varchar(32) NOT NULL COMMENT '榜单类型',
  `board_name` varchar(64) DEFAULT NULL COMMENT '榜单名称',
  `snapshot_no` varchar(64) NOT NULL COMMENT '榜单快照编号',
  `snapshot_time` datetime NOT NULL COMMENT '榜单抓取时间',
  `rank` int NOT NULL COMMENT '排名',
  `title` varchar(255) NOT NULL COMMENT '热榜标题',
  `word` varchar(255) DEFAULT NULL COMMENT '热词',
  `hot_value` bigint NOT NULL DEFAULT '0' COMMENT '热度值',
  `content_url` varchar(1024) DEFAULT NULL COMMENT '链接',
  `cover_url` varchar(1024) DEFAULT NULL COMMENT '封面',
  `aweme_id` varchar(64) DEFAULT NULL COMMENT '关联视频ID',
  `event_time` datetime DEFAULT NULL COMMENT '事件发生时间',
  `video_count` int NOT NULL DEFAULT '0' COMMENT '相关视频数',
  `discuss_video_count` int NOT NULL DEFAULT '0' COMMENT '讨论视频数',
  `article_detail_count` int NOT NULL DEFAULT '0' COMMENT '文章详情数',
  `room_count` int NOT NULL DEFAULT '0' COMMENT '直播间数量',
  `label` int DEFAULT NULL COMMENT '标签',
  `label_url` varchar(1024) DEFAULT NULL COMMENT '图标',
  `sentence_id` varchar(64) DEFAULT NULL COMMENT '话题标识',
  `sentence_tag` int DEFAULT NULL COMMENT '标签编号',
  `raw_json` json DEFAULT NULL COMMENT '原始JSON',
  `crawled_at` datetime DEFAULT NULL COMMENT '采集时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_douyin_hot_rank_snapshot_rank` (`platform`,`board_type`,`snapshot_no`,`rank`),
  KEY `idx_douyin_hot_rank_items_snapshot_time` (`snapshot_time`),
  KEY `idx_douyin_hot_rank_items_hot_value` (`hot_value`)
) ENGINE=InnoDB AUTO_INCREMENT=1830 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='抖音热榜快照表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dy_creator`
--

DROP TABLE IF EXISTS `dy_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dy_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(128) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext COMMENT '用户描述',
  `gender` varchar(2) DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) DEFAULT NULL COMMENT '粉丝数',
  `interaction` varchar(16) DEFAULT NULL COMMENT '获赞数',
  `videos_count` varchar(16) DEFAULT NULL COMMENT '作品数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='抖音博主信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `email_verification_tokens`
--

DROP TABLE IF EXISTS `email_verification_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `email_verification_tokens` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联用户 ID',
  `token` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '验证令牌',
  `token_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '令牌类型: email_verify, password_reset',
  `expires_at` timestamp(6) NOT NULL COMMENT '过期时间',
  `used_at` timestamp(6) NULL DEFAULT NULL COMMENT '使用时间',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_token_type` (`token_type`),
  KEY `idx_expires` (`expires_at`),
  CONSTRAINT `email_verification_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮箱验证/密码重置令牌';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_login_logs`
--

DROP TABLE IF EXISTS `iam_login_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_login_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned DEFAULT NULL COMMENT '用户ID，对应iam_users.id；失败场景可为空',
  `identity_id` bigint unsigned DEFAULT NULL COMMENT '认证标识ID，对应iam_user_identities.id；失败场景可为空',
  `login_type` varchar(32) NOT NULL COMMENT '登录方式：phone/email/wechat/username/password',
  `login_identifier` varchar(128) DEFAULT NULL COMMENT '登录标识快照，如手机号、邮箱、openid、用户名',
  `event_type` varchar(32) NOT NULL COMMENT '事件类型：login_success/login_failed/logout/refresh',
  `result_status` varchar(32) NOT NULL COMMENT '结果状态：success/failed',
  `fail_reason` varchar(255) DEFAULT NULL COMMENT '失败原因',
  `ip_address` varchar(64) DEFAULT NULL COMMENT 'IP地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT 'IP归属地',
  `device_type` varchar(32) DEFAULT NULL COMMENT '设备类型',
  `os_name` varchar(64) DEFAULT NULL COMMENT '操作系统名称',
  `browser_name` varchar(64) DEFAULT NULL COMMENT '浏览器名称',
  `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理',
  `trace_id` varchar(128) DEFAULT NULL COMMENT '请求链路追踪ID',
  `extra_data` json DEFAULT NULL COMMENT '扩展数据',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  PRIMARY KEY (`id`),
  KEY `idx_iam_login_logs_user_id_created_at` (`user_id`,`created_at`),
  KEY `idx_iam_login_logs_identity_id` (`identity_id`),
  KEY `idx_iam_login_logs_event_result` (`event_type`,`result_status`),
  KEY `idx_iam_login_logs_identifier` (`login_identifier`),
  KEY `idx_iam_login_logs_trace_id` (`trace_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-登录日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_operation_logs`
--

DROP TABLE IF EXISTS `iam_operation_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_operation_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned DEFAULT NULL COMMENT '操作人ID，对应iam_users.id',
  `session_id` varchar(128) DEFAULT NULL COMMENT '会话ID快照',
  `module_code` varchar(64) NOT NULL COMMENT '模块编码，如review/platform_account/workflow/user',
  `action_code` varchar(64) NOT NULL COMMENT '动作编码，如create/update/delete/approve/publish',
  `target_type` varchar(64) DEFAULT NULL COMMENT '操作对象类型，如task/user/role/platform_account',
  `target_id` varchar(128) DEFAULT NULL COMMENT '操作对象ID',
  `target_name` varchar(255) DEFAULT NULL COMMENT '操作对象名称快照',
  `request_method` varchar(16) DEFAULT NULL COMMENT 'HTTP请求方法',
  `request_path` varchar(255) DEFAULT NULL COMMENT 'HTTP请求路径',
  `request_ip` varchar(64) DEFAULT NULL COMMENT '请求IP地址',
  `request_payload` json DEFAULT NULL COMMENT '请求体快照，建议脱敏',
  `response_payload` json DEFAULT NULL COMMENT '响应体快照，建议脱敏',
  `operation_status` varchar(32) NOT NULL DEFAULT 'success' COMMENT '操作状态：success/failed',
  `error_message` varchar(500) DEFAULT NULL COMMENT '错误信息',
  `trace_id` varchar(128) DEFAULT NULL COMMENT '链路追踪ID',
  `operated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作发生时间',
  `extra_data` json DEFAULT NULL COMMENT '扩展数据',
  PRIMARY KEY (`id`),
  KEY `idx_iam_operation_logs_user_id_operated_at` (`user_id`,`operated_at`),
  KEY `idx_iam_operation_logs_module_action` (`module_code`,`action_code`),
  KEY `idx_iam_operation_logs_target` (`target_type`,`target_id`),
  KEY `idx_iam_operation_logs_trace_id` (`trace_id`),
  KEY `idx_iam_operation_logs_status` (`operation_status`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-操作审计日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_permissions`
--

DROP TABLE IF EXISTS `iam_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_permissions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `permission_code` varchar(128) NOT NULL COMMENT '权限编码，唯一，如task:create',
  `permission_name` varchar(128) NOT NULL COMMENT '权限名称',
  `module_code` varchar(64) NOT NULL COMMENT '模块编码，如task/review/workflow/user',
  `action_code` varchar(64) NOT NULL COMMENT '动作编码，如create/view/update/delete/approve',
  `permission_type` varchar(32) NOT NULL DEFAULT 'api' COMMENT '权限类型：menu/api/button/data',
  `parent_id` bigint unsigned DEFAULT NULL COMMENT '父权限ID',
  `path` varchar(255) DEFAULT NULL COMMENT '权限资源路径或标识',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '权限状态：active/disabled',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序值',
  `description` varchar(500) DEFAULT NULL COMMENT '权限描述',
  `is_builtin` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否系统内置：0否，1是',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_permissions_code` (`permission_code`),
  KEY `idx_iam_permissions_module_action` (`module_code`,`action_code`),
  KEY `idx_iam_permissions_parent_id` (`parent_id`),
  KEY `idx_iam_permissions_status_type` (`status`,`permission_type`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_role_permissions`
--

DROP TABLE IF EXISTS `iam_role_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_role_permissions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_id` bigint unsigned NOT NULL COMMENT '角色ID，对应iam_roles.id',
  `permission_id` bigint unsigned NOT NULL COMMENT '权限ID，对应iam_permissions.id',
  `granted_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '授权人ID',
  `granted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '关联状态：active/disabled',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_role_permissions_role_perm` (`role_id`,`permission_id`),
  KEY `idx_iam_role_permissions_permission_id` (`permission_id`),
  KEY `idx_iam_role_permissions_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-角色权限关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_roles`
--

DROP TABLE IF EXISTS `iam_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_roles` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_code` varchar(64) NOT NULL COMMENT '角色编码，唯一，如super_admin',
  `role_name` varchar(64) NOT NULL COMMENT '角色名称',
  `role_type` varchar(32) NOT NULL DEFAULT 'system' COMMENT '角色类型：system/business/custom',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '角色状态：active/disabled',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序值，越小越靠前',
  `description` varchar(500) DEFAULT NULL COMMENT '角色描述',
  `is_builtin` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否系统内置：0否，1是',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_roles_role_code` (`role_code`),
  KEY `idx_iam_roles_status_type` (`status`,`role_type`),
  KEY `idx_iam_roles_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_sessions`
--

DROP TABLE IF EXISTS `iam_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_sessions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `session_id` varchar(128) NOT NULL COMMENT '会话ID，唯一标识',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID，对应iam_users.id',
  `identity_id` bigint unsigned NOT NULL COMMENT '认证标识ID，对应iam_user_identities.id',
  `login_type` varchar(32) NOT NULL COMMENT '登录方式：phone/email/wechat/username/password',
  `access_token_digest` varchar(128) DEFAULT NULL COMMENT '访问令牌摘要，不存明文',
  `refresh_token_digest` varchar(128) DEFAULT NULL COMMENT '刷新令牌摘要，不存明文',
  `device_type` varchar(32) NOT NULL DEFAULT 'web' COMMENT '设备类型：web/mobile/miniapp',
  `device_id` varchar(128) DEFAULT NULL COMMENT '设备标识',
  `client_version` varchar(64) DEFAULT NULL COMMENT '客户端版本',
  `os_name` varchar(64) DEFAULT NULL COMMENT '操作系统名称',
  `browser_name` varchar(64) DEFAULT NULL COMMENT '浏览器名称',
  `ip_address` varchar(64) DEFAULT NULL COMMENT '登录IP地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT 'IP归属地',
  `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理',
  `login_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  `last_active_at` datetime DEFAULT NULL COMMENT '最近活跃时间',
  `expired_at` datetime DEFAULT NULL COMMENT '会话过期时间',
  `logout_at` datetime DEFAULT NULL COMMENT '退出时间',
  `session_status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '会话状态：active/expired/revoked/logout',
  `revoke_reason` varchar(255) DEFAULT NULL COMMENT '会话失效原因',
  `extra_data` json DEFAULT NULL COMMENT '扩展数据',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_sessions_session_id` (`session_id`),
  KEY `idx_iam_sessions_user_id` (`user_id`),
  KEY `idx_iam_sessions_identity_id` (`identity_id`),
  KEY `idx_iam_sessions_status_expired` (`session_status`,`expired_at`),
  KEY `idx_iam_sessions_last_active_at` (`last_active_at`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-登录会话表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_user_identities`
--

DROP TABLE IF EXISTS `iam_user_identities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_user_identities` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID，对应iam_users.id',
  `identity_type` varchar(32) NOT NULL COMMENT '认证类型：phone/email/wechat/username/password',
  `identity_key` varchar(128) NOT NULL COMMENT '登录标识，如手机号、邮箱、openid、用户名',
  `identity_value` varchar(255) DEFAULT NULL COMMENT '扩展值，如unionid或平台侧唯一值',
  `credential_hash` varchar(255) DEFAULT NULL COMMENT '凭证哈希，如密码哈希',
  `credential_salt` varchar(128) DEFAULT NULL COMMENT '凭证盐值',
  `verify_status` varchar(32) NOT NULL DEFAULT 'verified' COMMENT '认证状态：verified/unverified/pending',
  `is_primary` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否主认证方式：0否，1是',
  `is_enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用：0否，1是',
  `bound_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `last_used_at` datetime DEFAULT NULL COMMENT '最近使用时间',
  `expired_at` datetime DEFAULT NULL COMMENT '过期时间',
  `extra_data` json DEFAULT NULL COMMENT '扩展数据，如微信昵称、头像、第三方回包',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_user_identities_type_key` (`identity_type`,`identity_key`),
  KEY `idx_iam_user_identities_user_id` (`user_id`),
  KEY `idx_iam_user_identities_user_primary` (`user_id`,`is_primary`),
  KEY `idx_iam_user_identities_status` (`verify_status`,`is_enabled`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-用户认证标识表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_user_roles`
--

DROP TABLE IF EXISTS `iam_user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_user_roles` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID，对应iam_users.id',
  `role_id` bigint unsigned NOT NULL COMMENT '角色ID，对应iam_roles.id',
  `assigned_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '分配人ID',
  `assigned_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
  `expired_at` datetime DEFAULT NULL COMMENT '失效时间',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '关联状态：active/disabled',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_user_roles_user_role` (`user_id`,`role_id`),
  KEY `idx_iam_user_roles_role_id` (`role_id`),
  KEY `idx_iam_user_roles_status` (`status`),
  KEY `idx_iam_user_roles_expired_at` (`expired_at`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-用户角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iam_users`
--

DROP TABLE IF EXISTS `iam_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `iam_users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_no` varchar(64) NOT NULL COMMENT '用户编号，业务唯一标识',
  `username` varchar(64) DEFAULT NULL COMMENT '系统用户名，可为空',
  `nickname` varchar(64) NOT NULL DEFAULT '' COMMENT '昵称',
  `real_name` varchar(64) DEFAULT NULL COMMENT '真实姓名',
  `avatar_url` varchar(255) DEFAULT NULL COMMENT '头像URL',
  `gender` tinyint unsigned NOT NULL DEFAULT '0' COMMENT '性别：0未知，1男，2女',
  `phone` varchar(32) DEFAULT NULL COMMENT '主手机号，冗余展示字段',
  `email` varchar(128) DEFAULT NULL COMMENT '主邮箱，冗余展示字段',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '用户状态：active/disabled/locked/pending',
  `user_type` varchar(32) NOT NULL DEFAULT 'normal' COMMENT '用户类型：normal/admin/designer/reviewer',
  `last_login_at` datetime DEFAULT NULL COMMENT '最近登录时间',
  `last_login_ip` varchar(64) DEFAULT NULL COMMENT '最近登录IP',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '创建人ID',
  `updated_by` bigint unsigned NOT NULL DEFAULT '0' COMMENT '更新人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_iam_users_user_no` (`user_no`),
  UNIQUE KEY `uk_iam_users_username` (`username`),
  KEY `idx_iam_users_phone` (`phone`),
  KEY `idx_iam_users_email` (`email`),
  KEY `idx_iam_users_status_type` (`status`,`user_type`),
  KEY `idx_iam_users_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='身份权限域-用户主体表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `insight_modes`
--

DROP TABLE IF EXISTS `insight_modes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insight_modes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mode_key` varchar(50) NOT NULL COMMENT '模式标识 (如 summarize, analyze)',
  `is_active` tinyint DEFAULT '1' COMMENT '是否启用',
  `sort_order` int DEFAULT '0' COMMENT '显示排序',
  `label_zh` varchar(100) NOT NULL COMMENT '中文名称',
  `label_en` varchar(100) NOT NULL COMMENT '英文名称',
  `description_zh` varchar(500) DEFAULT NULL COMMENT '中文描述',
  `description_en` varchar(500) DEFAULT NULL COMMENT '英文描述',
  `prefill_zh` varchar(200) DEFAULT NULL COMMENT '中文输入预填充',
  `prefill_en` varchar(200) DEFAULT NULL COMMENT '英文输入预填充',
  `icon` varchar(50) DEFAULT 'smart_toy' COMMENT 'Material Symbols 图标名',
  `color` varchar(20) DEFAULT 'cyan' COMMENT '颜色主题 (cyan/orange/pink/purple)',
  `keywords_zh` text COMMENT '中文关键词 (逗号分隔)',
  `keywords_en` text COMMENT '英文关键词 (逗号分隔)',
  `system_prompt` text NOT NULL COMMENT '模式专属提示词',
  `is_system` tinyint DEFAULT '0' COMMENT '系统内置 (1=不可删除)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mode_key` (`mode_key`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='分析模式配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kuaishou_creator`
--

DROP TABLE IF EXISTS `kuaishou_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kuaishou_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext COMMENT '用户描述',
  `gender` varchar(2) DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) DEFAULT NULL COMMENT '粉丝数',
  `videos_count` varchar(16) DEFAULT NULL COMMENT '作品数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='快手博主';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kuaishou_video`
--

DROP TABLE IF EXISTS `kuaishou_video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kuaishou_video` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `video_id` varchar(64) NOT NULL COMMENT '视频ID',
  `video_type` varchar(16) NOT NULL COMMENT '视频类型',
  `title` varchar(500) DEFAULT NULL COMMENT '视频标题',
  `desc` longtext COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) DEFAULT NULL COMMENT '视频点赞数',
  `viewd_count` varchar(16) DEFAULT NULL COMMENT '视频浏览数量',
  `video_url` varchar(512) DEFAULT NULL COMMENT '视频详情URL',
  `video_cover_url` text COMMENT '视频封面图 URL',
  `video_play_url` text COMMENT '视频播放 URL',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`),
  KEY `idx_kuaishou_vi_video_i_c5c6a6` (`video_id`),
  KEY `idx_kuaishou_vi_create__a10dee` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='快手视频';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kuaishou_video_comment`
--

DROP TABLE IF EXISTS `kuaishou_video_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kuaishou_video_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `video_id` varchar(64) NOT NULL COMMENT '视频ID',
  `content` longtext COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) NOT NULL COMMENT '评论回复数',
  `like_count` varchar(255) NOT NULL DEFAULT '0' COMMENT '点赞数',
  PRIMARY KEY (`id`),
  KEY `idx_kuaishou_vi_comment_ed48fa` (`comment_id`),
  KEY `idx_kuaishou_vi_video_i_e50914` (`video_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='快手视频评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `llm_configs`
--

DROP TABLE IF EXISTS `llm_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `llm_configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置名称，如 default, reasoning, fast',
  `provider` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商: openai / anthropic / deepseek / ollama',
  `is_active` tinyint DEFAULT '0' COMMENT '是否为当前激活配置: 0=否, 1=是',
  `api_key` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API Key',
  `base_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API 基础 URL',
  `model_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `enable_thinking` tinyint DEFAULT '0' COMMENT '启用思考模式: 0=否, 1=是',
  `thinking_budget_tokens` int DEFAULT '4096' COMMENT 'Anthropic Extended Thinking token 预算',
  `reasoning_effort` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'high' COMMENT 'OpenAI GPT-5 推理强度: none/low/medium/high/xhigh',
  `support_multimodal` tinyint DEFAULT '0' COMMENT '是否支持多模态（图片理解）: 0=否, 1=是',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '配置描述/备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_name` (`config_name`),
  KEY `idx_provider` (`provider`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM 配置管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `oauth_states`
--

DROP TABLE IF EXISTS `oauth_states`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `oauth_states` (
  `state` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'OAuth state token',
  `provider` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'github / google',
  `expires_at` timestamp(6) NOT NULL COMMENT '过期时间',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`state`),
  KEY `idx_expires` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OAuth CSRF state 存储';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_account_auth_logs`
--

DROP TABLE IF EXISTS `platform_account_auth_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_account_auth_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` bigint unsigned NOT NULL COMMENT '账号ID',
  `event_type` varchar(32) NOT NULL COMMENT '事件类型：bind, refresh, expire, revoke',
  `event_status` varchar(32) NOT NULL COMMENT '状态：success, failed',
  `fail_reason` varchar(500) DEFAULT NULL COMMENT '失败原因',
  `ip_address` varchar(64) DEFAULT NULL COMMENT '授权IP',
  `extra_data` json DEFAULT NULL COMMENT '扩展数据',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '事件时间',
  PRIMARY KEY (`id`),
  KEY `idx_platform_account_auth_logs_account_event` (`account_id`,`event_type`),
  KEY `idx_platform_account_auth_logs_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='平台账号管理域-授权历史日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_account_contents`
--

DROP TABLE IF EXISTS `platform_account_contents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_account_contents` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `owner_user_id` bigint NOT NULL,
  `account_id` bigint NOT NULL,
  `platform_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sec_user_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `dy_aweme_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `xhs_note_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bili_video_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ks_video_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cover_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content_url` varchar(2048) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `author_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `aweme_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `view_count` int NOT NULL DEFAULT '0',
  `liked_count` int NOT NULL DEFAULT '0',
  `comment_count` int NOT NULL DEFAULT '0',
  `share_count` int NOT NULL DEFAULT '0',
  `published_at` datetime DEFAULT NULL,
  `last_synced_at` datetime DEFAULT NULL,
  `extra_data` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pac_owner_account_platform_content` (`owner_user_id`,`account_id`,`platform_code`,`content_id`),
  KEY `idx_pac_owner_user_id` (`owner_user_id`),
  KEY `idx_pac_account_id` (`account_id`),
  KEY `idx_pac_platform_code` (`platform_code`),
  KEY `idx_pac_sec_user_id` (`sec_user_id`),
  KEY `idx_pac_content_status` (`content_status`),
  KEY `idx_pac_content_type` (`content_type`),
  KEY `idx_pac_published_at` (`published_at`),
  KEY `idx_pac_dy_aweme_id` (`dy_aweme_id`),
  KEY `idx_pac_xhs_note_id` (`xhs_note_id`),
  KEY `idx_pac_bili_video_id` (`bili_video_id`),
  KEY `idx_pac_ks_video_id` (`ks_video_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_account_sessions`
--

DROP TABLE IF EXISTS `platform_account_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_account_sessions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` bigint unsigned NOT NULL COMMENT '账号ID，对应 platform_accounts.id',
  `cookies` json DEFAULT NULL COMMENT '浏览器 Cookie 数组快照',
  `local_storage` json DEFAULT NULL COMMENT '浏览器 LocalStorage 键值对快照',
  `session_token` text COMMENT 'Token 或 API 密钥',
  `user_agent` varchar(512) DEFAULT NULL COMMENT '捕获该 Session 时使用的 User-Agent',
  `device_info` json DEFAULT NULL COMMENT '设备指纹信息',
  `expires_at` datetime DEFAULT NULL COMMENT 'Session 理论失效时间',
  `last_sync_at` datetime DEFAULT NULL COMMENT '最近同步时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `auth_type` varchar(32) NOT NULL DEFAULT 'cookie' COMMENT '授权类型：cookie/qrcode/phone',
  `cookie_blob` longtext COMMENT '加密后的Cookie密文（主字段）',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT '授权状态：active/expired/invalid/revoked',
  `session_status` varchar(32) NOT NULL DEFAULT 'active' COMMENT 'Normalized session status: active/invalid/expired/account_mismatch/revoked',
  `cookie_hash` varchar(128) DEFAULT NULL COMMENT 'Cookie hash',
  `storage_hash` varchar(128) DEFAULT NULL COMMENT 'Local storage hash',
  `source_type` varchar(32) DEFAULT NULL COMMENT 'Session source type',
  `source_client_id` varchar(128) DEFAULT NULL COMMENT 'Session source client id',
  `validated_identity` varchar(255) DEFAULT NULL COMMENT 'Last validated identity value',
  `last_validation_error` varchar(500) DEFAULT NULL COMMENT 'Last validation error',
  `last_validated_at` datetime DEFAULT NULL COMMENT '最近有效性校验时间',
  `last_refresh_at` datetime DEFAULT NULL COMMENT '最近刷新时间',
  `encrypt_key_id` varchar(64) DEFAULT NULL COMMENT '加密密钥ID（KMS或本地密钥版本）',
  `cookie_version` int unsigned NOT NULL DEFAULT '1' COMMENT 'Cookie版本号（便于轮换）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform_account_sessions_account` (`account_id`),
  KEY `idx_pas_status` (`status`),
  KEY `idx_pas_account_status` (`account_id`,`status`),
  KEY `idx_pas_last_validated_at` (`last_validated_at`),
  KEY `idx_pas_session_status` (`session_status`),
  KEY `idx_pas_source` (`source_type`,`source_client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='平台账号管理域-平台授权会话表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_accounts`
--

DROP TABLE IF EXISTS `platform_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_accounts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_user_id` bigint unsigned NOT NULL COMMENT '归属系统用户ID，对应 iam_users.id',
  `platform_code` varchar(32) NOT NULL COMMENT '平台编码：douyin, xiaohongshu, bilibili, etc.',
  `account_name` varchar(128) NOT NULL COMMENT '账号名称/登录ID',
  `account_pwd_encrypted` varchar(512) DEFAULT NULL COMMENT '加密后的密码',
  `nickname` varchar(128) DEFAULT NULL COMMENT '平台侧昵称',
  `avatar_url` varchar(512) DEFAULT NULL COMMENT '平台侧头像URL',
  `platform_uid` varchar(128) DEFAULT NULL COMMENT '平台内部唯一标识',
  `identity_type` varchar(32) DEFAULT NULL COMMENT 'Primary identity type',
  `identity_value` varchar(255) DEFAULT NULL COMMENT 'Primary identity value',
  `sec_user_id` varchar(255) DEFAULT NULL COMMENT 'Stable sec_user_id',
  `identity_fallback` varchar(128) DEFAULT NULL COMMENT 'uid_tt等兜底身份键',
  `identity_source` varchar(32) DEFAULT NULL COMMENT 'platform_uid/uid_tt/account_name',
  `auth_status` varchar(32) NOT NULL DEFAULT 'need_reauth' COMMENT '授权状态：authorized, expired, need_reauth',
  `account_status` varchar(32) NOT NULL DEFAULT 'needs_rebind' COMMENT 'Account status: active/expired/account_mismatch/needs_rebind/disabled',
  `last_identity_verified_at` datetime DEFAULT NULL COMMENT 'Last identity verified time',
  `last_identity_error` varchar(500) DEFAULT NULL COMMENT 'Last identity validation error',
  `account_type` varchar(32) NOT NULL DEFAULT 'personal' COMMENT '账号类型：personal, business',
  `tags` json DEFAULT NULL COMMENT '账号标签',
  `remark` varchar(500) DEFAULT NULL COMMENT '用户备注',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标记：0否，1是',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform_accounts_owner_platform_uid` (`owner_user_id`,`platform_code`,`platform_uid`),
  UNIQUE KEY `uk_owner_platform_sec_user_id` (`owner_user_id`,`platform_code`,`sec_user_id`),
  KEY `idx_platform_accounts_owner_platform` (`owner_user_id`,`platform_code`),
  KEY `idx_platform_accounts_platform_uid` (`platform_uid`),
  KEY `idx_platform_accounts_status` (`auth_status`),
  KEY `idx_platform_accounts_owner_platform_name` (`owner_user_id`,`platform_code`,`account_name`),
  KEY `idx_platform_accounts_sec_user_id` (`sec_user_id`),
  KEY `idx_platform_accounts_identity_type_value` (`identity_type`,`identity_value`),
  KEY `idx_platform_accounts_account_status` (`account_status`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='平台账号管理域-平台账号主表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_cookie_bridge_bindings`
--

DROP TABLE IF EXISTS `platform_cookie_bridge_bindings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_cookie_bridge_bindings` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `owner_user_id` bigint unsigned NOT NULL COMMENT 'Main app user id',
  `platform_code` varchar(32) NOT NULL COMMENT 'Main app platform code, e.g. douyin',
  `bridge_client_id` varchar(128) NOT NULL COMMENT 'CookieBridge client_id',
  `platform_account_id` bigint unsigned DEFAULT NULL COMMENT 'platform_accounts.id',
  `crawler_cookie_account_id` bigint unsigned DEFAULT NULL COMMENT 'crawler_cookies_account.id',
  `status` varchar(32) NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Default binding for this user/platform',
  `last_reported_identity` varchar(255) DEFAULT NULL COMMENT 'Last reported identity value',
  `last_reported_nickname` varchar(255) DEFAULT NULL COMMENT 'Last reported nickname',
  `last_cookie_hash` varchar(128) DEFAULT NULL COMMENT 'Last reported cookie hash',
  `last_sync_at` datetime DEFAULT NULL COMMENT 'Last CookieBridge sync time',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pcbb_user_platform_client` (`owner_user_id`,`platform_code`,`bridge_client_id`),
  KEY `idx_pcbb_user_platform_status` (`owner_user_id`,`platform_code`,`status`,`is_default`),
  KEY `idx_pcbb_platform_account` (`platform_account_id`),
  KEY `idx_pcbb_crawler_cookie_account` (`crawler_cookie_account_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Main user to CookieBridge client binding';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `platform_cookies`
--

DROP TABLE IF EXISTS `platform_cookies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platform_cookies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `platform` varchar(20) NOT NULL COMMENT '平台标识: xhs/dy/bili/ks',
  `cookies` text NOT NULL COMMENT 'Cookie 字符串',
  `status` tinyint DEFAULT '0' COMMENT '状态: 0=有效, 1=过期, 2=禁用',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform` (`platform`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='平台 Cookies 管理';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `publish_plan_items`
--

DROP TABLE IF EXISTS `publish_plan_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publish_plan_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
  `request_group_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '同一次发布请求的分组 ID',
  `owner_user_id` bigint NOT NULL COMMENT '所属用户 ID',
  `draft_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联的草稿 ID',
  `task_ref` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '业务侧任务引用 ID',
  `platform_type` int NOT NULL COMMENT '平台类型编号',
  `platform_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台编码，如 douyin/xiaohongshu',
  `platform_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台展示名称',
  `account_id` bigint NOT NULL COMMENT '发布账号 ID，对应 platform_accounts.id',
  `account_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发布账号名称或昵称',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发布标题',
  `video_url` varchar(2048) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布视频地址',
  `cover_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '封面地址',
  `topics` json NOT NULL COMMENT '话题标签列表',
  `publish_mode` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发布模式：headed/headless',
  `publish_time_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发布时间类型：now/schedule',
  `scheduled_at` datetime DEFAULT NULL COMMENT '计划发布时间',
  `submitted_at` datetime DEFAULT NULL COMMENT '提交到次级发布程序的时间',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发布记录状态：submitted/scheduled/failed',
  `status_message` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '状态说明或下游返回摘要',
  `downstream_status_code` int DEFAULT NULL COMMENT '下游发布接口状态码',
  `downstream_payload` json DEFAULT NULL COMMENT '发送给下游发布程序的请求体',
  `downstream_response` json DEFAULT NULL COMMENT '下游发布程序返回的响应体',
  `extra_data` json DEFAULT NULL COMMENT '扩展信息',
  `failure_reason` text COLLATE utf8mb4_unicode_ci COMMENT '失败原因详情',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_publish_plan_items_owner_user_id` (`owner_user_id`),
  KEY `idx_publish_plan_items_request_group_id` (`request_group_id`),
  KEY `idx_publish_plan_items_draft_id` (`draft_id`),
  KEY `idx_publish_plan_items_task_ref` (`task_ref`),
  KEY `idx_publish_plan_items_platform_type` (`platform_type`),
  KEY `idx_publish_plan_items_platform_code` (`platform_code`),
  KEY `idx_publish_plan_items_account_id` (`account_id`),
  KEY `idx_publish_plan_items_publish_time_type` (`publish_time_type`),
  KEY `idx_publish_plan_items_scheduled_at` (`scheduled_at`),
  KEY `idx_publish_plan_items_submitted_at` (`submitted_at`),
  KEY `idx_publish_plan_items_status` (`status`),
  KEY `idx_publish_plan_items_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发布计划明细表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `schema_migrations`
--

DROP TABLE IF EXISTS `schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schema_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `version` int NOT NULL COMMENT '迁移版本号',
  `description` varchar(255) NOT NULL COMMENT '迁移描述',
  `filename` varchar(255) NOT NULL COMMENT '迁移文件名',
  `checksum` varchar(64) DEFAULT NULL COMMENT '文件校验和 (SHA-256)',
  `executed_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `execution_time_ms` int DEFAULT NULL COMMENT '执行耗时 (毫秒)',
  `success` tinyint NOT NULL DEFAULT '1' COMMENT '是否成功',
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`),
  KEY `idx_version` (`version`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据库迁移记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasks` (
  `id` varchar(64) NOT NULL COMMENT '任务唯一ID',
  `user_id` bigint unsigned NOT NULL COMMENT '归属用户ID',
  `platform` varchar(32) NOT NULL COMMENT '平台',
  `task_type` varchar(64) NOT NULL COMMENT '任务类型',
  `state` varchar(32) NOT NULL DEFAULT 'pending' COMMENT '状态',
  `source_type` varchar(32) NOT NULL COMMENT '来源类型',
  `source_value` varchar(512) DEFAULT NULL COMMENT '来源值',
  `title` varchar(255) DEFAULT NULL COMMENT '任务标题',
  `config` json DEFAULT NULL COMMENT '配置',
  `result_count` int DEFAULT '0' COMMENT '结果数',
  `error_message` varchar(512) DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tasks_user_id` (`user_id`),
  KEY `idx_tasks_state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tieba_comment`
--

DROP TABLE IF EXISTS `tieba_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tieba_comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `comment_id` varchar(255) NOT NULL COMMENT '评论ID',
  `parent_comment_id` varchar(255) DEFAULT '' COMMENT '父评论ID',
  `content` text NOT NULL COMMENT '评论内容',
  `user_link` varchar(255) DEFAULT '' COMMENT '用户主页链接',
  `user_nickname` varchar(255) DEFAULT '' COMMENT '用户昵称',
  `user_avatar` varchar(255) DEFAULT '' COMMENT '用户头像地址',
  `tieba_id` varchar(255) DEFAULT '' COMMENT '贴吧ID',
  `tieba_name` varchar(255) NOT NULL COMMENT '贴吧名称',
  `tieba_link` varchar(255) NOT NULL COMMENT '贴吧链接',
  `publish_time` varchar(255) DEFAULT '' COMMENT '发布时间',
  `ip_location` varchar(255) DEFAULT '' COMMENT 'IP地理位置',
  `sub_comment_count` int DEFAULT '0' COMMENT '子评论数',
  `note_id` varchar(255) NOT NULL COMMENT '帖子ID',
  `note_url` varchar(255) NOT NULL COMMENT '帖子链接',
  `add_ts` bigint NOT NULL COMMENT '添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '最后修改时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_tieba_comment_comment_id` (`note_id`),
  KEY `idx_tieba_comment_note_id` (`note_id`),
  KEY `idx_tieba_comment_publish_time` (`publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='贴吧评论表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tieba_creator`
--

DROP TABLE IF EXISTS `tieba_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tieba_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `user_name` varchar(64) NOT NULL COMMENT '用户名',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `gender` varchar(2) DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) DEFAULT NULL COMMENT '粉丝数',
  `registration_duration` varchar(16) DEFAULT NULL COMMENT '吧龄',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='贴吧创作者';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tieba_note`
--

DROP TABLE IF EXISTS `tieba_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tieba_note` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `note_id` varchar(644) NOT NULL COMMENT '帖子ID',
  `title` varchar(255) NOT NULL COMMENT '帖子标题',
  `desc` text COMMENT '帖子描述',
  `note_url` varchar(255) NOT NULL COMMENT '帖子链接',
  `publish_time` varchar(255) NOT NULL COMMENT '发布时间',
  `user_link` varchar(255) DEFAULT '' COMMENT '用户主页链接',
  `user_nickname` varchar(255) DEFAULT '' COMMENT '用户昵称',
  `user_avatar` varchar(255) DEFAULT '' COMMENT '用户头像地址',
  `tieba_id` varchar(255) DEFAULT '' COMMENT '贴吧ID',
  `tieba_name` varchar(255) NOT NULL COMMENT '贴吧名称',
  `tieba_link` varchar(255) NOT NULL COMMENT '贴吧链接',
  `total_replay_num` int DEFAULT '0' COMMENT '帖子回复总数',
  `total_replay_page` int DEFAULT '0' COMMENT '帖子回复总页数',
  `ip_location` varchar(255) DEFAULT '' COMMENT 'IP地理位置',
  `add_ts` bigint NOT NULL COMMENT '添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '最后修改时间戳',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`),
  KEY `idx_tieba_note_note_id` (`note_id`),
  KEY `idx_tieba_note_publish_time` (`publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='贴吧帖子表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_content_relations`
--

DROP TABLE IF EXISTS `user_content_relations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_content_relations` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL COMMENT '归属用户ID',
  `platform` varchar(16) NOT NULL COMMENT '平台标识 (dy, xhs, bili, ks, wb, tieba, zhihu)',
  `dy_aweme_id` varchar(64) DEFAULT NULL COMMENT '抖音视频ID',
  `xhs_note_id` varchar(64) DEFAULT NULL COMMENT '小红书笔记ID',
  `wb_note_id` varchar(64) DEFAULT NULL COMMENT '微博帖子ID',
  `tieba_note_id` varchar(64) DEFAULT NULL COMMENT '贴吧帖子ID',
  `bili_video_id` varchar(64) DEFAULT NULL COMMENT 'B站视频ID',
  `ks_video_id` varchar(64) DEFAULT NULL COMMENT '快手视频ID',
  `zhihu_content_id` varchar(64) DEFAULT NULL COMMENT '知乎内容ID',
  `task_id` varchar(64) DEFAULT NULL COMMENT '来源任务ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_content` (`user_id`,`platform`,`dy_aweme_id`,`xhs_note_id`,`wb_note_id`,`tieba_note_id`,`bili_video_id`,`ks_video_id`,`zhihu_content_id`),
  KEY `idx_user_platform` (`user_id`,`platform`)
) ENGINE=InnoDB AUTO_INCREMENT=107 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户内容关联链表 (V4.2)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_oauth_accounts`
--

DROP TABLE IF EXISTS `user_oauth_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_oauth_accounts` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联用户 ID',
  `provider` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'OAuth 提供商: github, google',
  `provider_user_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商用户 ID',
  `provider_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '提供商邮箱',
  `access_token` text COLLATE utf8mb4_unicode_ci COMMENT 'Access Token (加密存储)',
  `refresh_token` text COLLATE utf8mb4_unicode_ci COMMENT 'Refresh Token (加密存储)',
  `token_expires_at` timestamp(6) NULL DEFAULT NULL COMMENT 'Token 过期时间',
  `raw_data` json DEFAULT NULL COMMENT '原始用户数据',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_provider_user` (`provider`,`provider_user_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `user_oauth_accounts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户 OAuth 关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_refresh_tokens`
--

DROP TABLE IF EXISTS `user_refresh_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_refresh_tokens` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联用户 ID',
  `token_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Refresh Token 哈希',
  `device_info` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备信息',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP 地址',
  `expires_at` timestamp(6) NOT NULL COMMENT '过期时间',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token_hash` (`token_hash`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires` (`expires_at`),
  CONSTRAINT `user_refresh_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='JWT Refresh Token 白名单';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户 ID (UUID)',
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱地址',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '密码哈希 (bcrypt)，OAuth 用户可为空',
  `display_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '显示名称',
  `avatar_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像 URL',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '状态: 0=待验证, 1=正常, 2=禁用',
  `email_verified_at` timestamp(6) NULL DEFAULT NULL COMMENT '邮箱验证时间',
  `created_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` timestamp(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_status` (`status`),
  KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户主表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voice_asset`
--

DROP TABLE IF EXISTS `voice_asset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voice_asset` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `voice_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '业务唯一编码，便于接口和前端引用',
  `voice_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '音色名称，前端展示用',
  `source_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '声音来源类型：system_builtin=系统内置，user_clone=用户复刻，ai_design=AI设计，user_upload=用户上传',
  `owner_user_id` bigint DEFAULT NULL COMMENT '所属用户ID；系统内置音色为空，用户私有音色必须有值',
  `provider` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '服务提供商，例如 aliyun、dashscope',
  `model_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色对应的模型名，例如 cosyvoice-v3.5-plus',
  `target_model` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '后续语音合成必须匹配的目标模型',
  `third_party_voice_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '第三方平台返回的 voice_id，可直接用于TTS调用',
  `voice_gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色性别：male、female、neutral',
  `voice_language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色语言：zh、en 等',
  `voice_style` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色风格标签，例如 沉稳、活泼、新闻播报',
  `voice_desc` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色描述，用于运营配置或前端展示',
  `voice_prompt` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI声音设计时使用的提示词描述',
  `preview_text` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成试听音频时使用的文本',
  `preview_audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '试听音频URL',
  `sample_audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户参考音频URL/复刻原始音频URL',
  `sample_audio_duration` decimal(6,2) DEFAULT NULL COMMENT '参考音频时长，单位秒',
  `cover_image_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音色封面图URL，可为空',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'enabled' COMMENT '状态：enabled=启用，disabled=停用，deploying=生成中，failed=失败',
  `is_public` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否公开给所有用户：1=公开，0=私有',
  `sort_no` int NOT NULL DEFAULT '0' COMMENT '排序值，越小越靠前',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `ext_json` json DEFAULT NULL COMMENT '扩展字段，预留给未来能力',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间，NULL表示未删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_voice_asset_voice_code` (`voice_code`),
  KEY `idx_voice_asset_owner_user_id` (`owner_user_id`),
  KEY `idx_voice_asset_source_type` (`source_type`),
  KEY `idx_voice_asset_status` (`status`),
  KEY `idx_voice_asset_is_public` (`is_public`),
  KEY `idx_voice_asset_third_party_voice_id` (`third_party_voice_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='声音资产表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `voice_generation_record`
--

DROP TABLE IF EXISTS `voice_generation_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `voice_generation_record` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `record_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '业务唯一编码，便于对外查询',
  `owner_user_id` bigint DEFAULT NULL COMMENT '发起生成的用户ID',
  `draft_id` bigint DEFAULT NULL COMMENT '关联创作草稿ID，可为空',
  `voice_asset_id` bigint DEFAULT NULL COMMENT '关联声音资产ID，可为空；如果直接传 voice_id 也允许不关联',
  `provider` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '服务提供商，例如 aliyun、dashscope',
  `model_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '本次TTS使用的模型名',
  `third_party_voice_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '本次调用使用的第三方音色ID',
  `input_text` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '本次合成的文案内容',
  `style` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '本次合成时传入的风格参数',
  `speed` decimal(4,2) DEFAULT NULL COMMENT '语速参数，例如 0.80、1.00、1.20',
  `volume` decimal(4,2) DEFAULT NULL COMMENT '音量参数，可选',
  `pitch` decimal(4,2) DEFAULT NULL COMMENT '音高参数，可选',
  `audio_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成成功后的音频URL',
  `audio_duration` decimal(8,2) DEFAULT NULL COMMENT '生成音频时长，单位秒',
  `audio_format` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '音频格式，例如 mp3、wav',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'processing' COMMENT '生成状态：processing=处理中，success=成功，failed=失败',
  `request_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '第三方服务返回的请求ID',
  `error_code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '失败错误码',
  `error_message` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '失败错误信息',
  `raw_response` json DEFAULT NULL COMMENT '第三方原始响应，便于排查',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_voice_generation_record_code` (`record_code`),
  KEY `idx_voice_generation_owner_user_id` (`owner_user_id`),
  KEY `idx_voice_generation_draft_id` (`draft_id`),
  KEY `idx_voice_generation_voice_asset_id` (`voice_asset_id`),
  KEY `idx_voice_generation_status` (`status`),
  KEY `idx_voice_generation_request_id` (`request_id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语音合成记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `weibo_creator`
--

DROP TABLE IF EXISTS `weibo_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weibo_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext COMMENT '用户描述',
  `gender` varchar(2) DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) DEFAULT NULL COMMENT '粉丝数',
  `tag_list` longtext COMMENT '标签列表',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='微博博主';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `weibo_note`
--

DROP TABLE IF EXISTS `weibo_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weibo_note` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `gender` varchar(12) DEFAULT NULL COMMENT '用户性别',
  `profile_url` varchar(255) DEFAULT NULL COMMENT '用户主页地址',
  `ip_location` varchar(32) DEFAULT '发布微博的地理信息',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `note_id` varchar(64) NOT NULL COMMENT '帖子ID',
  `content` longtext COMMENT '帖子正文内容',
  `create_time` bigint NOT NULL COMMENT '帖子发布时间戳',
  `create_date_time` varchar(32) NOT NULL COMMENT '帖子发布日期时间',
  `liked_count` varchar(16) DEFAULT NULL COMMENT '帖子点赞数',
  `comments_count` varchar(16) DEFAULT NULL COMMENT '帖子评论数量',
  `shared_count` varchar(16) DEFAULT NULL COMMENT '帖子转发数量',
  `note_url` varchar(512) DEFAULT NULL COMMENT '帖子详情URL',
  `image_list` longtext COMMENT '封面图片列表',
  `video_url` longtext COMMENT '视频地址',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`),
  KEY `idx_weibo_note_note_id_f95b1a` (`note_id`),
  KEY `idx_weibo_note_create__692709` (`create_time`),
  KEY `idx_weibo_note_create__d05ed2` (`create_date_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='微博帖子';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `weibo_note_comment`
--

DROP TABLE IF EXISTS `weibo_note_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weibo_note_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `gender` varchar(12) DEFAULT NULL COMMENT '用户性别',
  `profile_url` varchar(255) DEFAULT NULL COMMENT '用户主页地址',
  `ip_location` varchar(32) DEFAULT '发布微博的地理信息',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `note_id` varchar(64) NOT NULL COMMENT '帖子ID',
  `content` longtext COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `create_date_time` varchar(32) NOT NULL COMMENT '评论日期时间',
  `sub_comment_count` varchar(16) NOT NULL COMMENT '评论回复数',
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(255) NOT NULL DEFAULT '0' COMMENT '点赞数',
  PRIMARY KEY (`id`),
  KEY `idx_weibo_note__comment_c7611c` (`comment_id`),
  KEY `idx_weibo_note__note_id_24f108` (`note_id`),
  KEY `idx_weibo_note__create__667fe3` (`create_date_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='微博帖子评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xhs_creator`
--

DROP TABLE IF EXISTS `xhs_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `xhs_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext COMMENT '用户描述',
  `gender` varchar(2) DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) DEFAULT NULL COMMENT '粉丝数',
  `interaction` varchar(16) DEFAULT NULL COMMENT '获赞和收藏数',
  `tag_list` longtext COMMENT '标签列表',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小红书博主';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xhs_note`
--

DROP TABLE IF EXISTS `xhs_note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `xhs_note` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `note_id` varchar(64) NOT NULL COMMENT '笔记ID',
  `type` varchar(16) DEFAULT NULL COMMENT '笔记类型(normal | video)',
  `title` varchar(255) DEFAULT NULL COMMENT '笔记标题',
  `desc` longtext COMMENT '笔记描述',
  `video_url` longtext COMMENT '视频地址',
  `time` bigint NOT NULL COMMENT '笔记发布时间戳',
  `last_update_time` bigint NOT NULL COMMENT '笔记最后更新时间戳',
  `liked_count` varchar(16) DEFAULT NULL COMMENT '笔记点赞数',
  `collected_count` varchar(16) DEFAULT NULL COMMENT '笔记收藏数',
  `comment_count` varchar(16) DEFAULT NULL COMMENT '笔记评论数',
  `share_count` varchar(16) DEFAULT NULL COMMENT '笔记分享数',
  `image_list` longtext COMMENT '笔记封面图片列表',
  `tag_list` longtext COMMENT '标签列表',
  `note_url` varchar(255) DEFAULT NULL COMMENT '笔记详情页的URL',
  `source_keyword` varchar(255) DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`),
  KEY `idx_xhs_note_note_id_209457` (`note_id`),
  KEY `idx_xhs_note_time_eaa910` (`time`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小红书笔记';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `xhs_note_comment`
--

DROP TABLE IF EXISTS `xhs_note_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `xhs_note_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `note_id` varchar(64) NOT NULL COMMENT '笔记ID',
  `content` longtext NOT NULL COMMENT '评论内容',
  `sub_comment_count` varchar(64) NOT NULL COMMENT '子评论数量',
  `pictures` varchar(512) DEFAULT NULL,
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(255) NOT NULL DEFAULT '0' COMMENT '点赞数',
  `note_url` varchar(255) NOT NULL DEFAULT '' COMMENT '所属的笔记链接',
  `target_comment_id` varchar(64) DEFAULT NULL COMMENT '目标评论ID',
  PRIMARY KEY (`id`),
  KEY `idx_xhs_note_co_comment_8e8349` (`comment_id`),
  KEY `idx_xhs_note_co_create__204f8d` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小红书笔记评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zhihu_comment`
--

DROP TABLE IF EXISTS `zhihu_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zhihu_comment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `comment_id` varchar(64) NOT NULL COMMENT '评论ID',
  `parent_comment_id` varchar(64) DEFAULT NULL COMMENT '父评论ID',
  `content` text NOT NULL COMMENT '评论内容',
  `publish_time` varchar(32) NOT NULL COMMENT '发布时间',
  `ip_location` varchar(64) DEFAULT NULL COMMENT 'IP地理位置',
  `sub_comment_count` int NOT NULL DEFAULT '0' COMMENT '子评论数',
  `like_count` int NOT NULL DEFAULT '0' COMMENT '点赞数',
  `dislike_count` int NOT NULL DEFAULT '0' COMMENT '踩数',
  `content_id` varchar(64) NOT NULL COMMENT '内容ID',
  `content_type` varchar(16) NOT NULL COMMENT '内容类型(article | answer | zvideo)',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) NOT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_zhihu_comment_comment_id` (`comment_id`),
  KEY `idx_zhihu_comment_content_id` (`content_id`),
  KEY `idx_zhihu_comment_publish_time` (`publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知乎评论';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zhihu_content`
--

DROP TABLE IF EXISTS `zhihu_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zhihu_content` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `content_id` varchar(64) NOT NULL COMMENT '内容ID',
  `content_type` varchar(16) NOT NULL COMMENT '内容类型(article | answer | zvideo)',
  `content_text` longtext COMMENT '内容文本, 如果是视频类型这里为空',
  `content_url` varchar(255) NOT NULL COMMENT '内容落地链接',
  `question_id` varchar(64) DEFAULT NULL COMMENT '问题ID, type为answer时有值',
  `title` varchar(255) NOT NULL COMMENT '内容标题',
  `desc` longtext COMMENT '内容描述',
  `created_time` varchar(32) NOT NULL COMMENT '创建时间',
  `updated_time` varchar(32) NOT NULL COMMENT '更新时间',
  `voteup_count` int NOT NULL DEFAULT '0' COMMENT '赞同人数',
  `comment_count` int NOT NULL DEFAULT '0' COMMENT '评论数量',
  `source_keyword` varchar(64) DEFAULT NULL COMMENT '来源关键词',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) NOT NULL COMMENT '用户头像地址',
  `user_url_token` varchar(255) NOT NULL COMMENT '用户url_token',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_zhihu_content_content_id` (`content_id`),
  KEY `idx_zhihu_content_created_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知乎内容（回答、文章、视频）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zhihu_creator`
--

DROP TABLE IF EXISTS `zhihu_creator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zhihu_creator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) NOT NULL COMMENT '用户头像地址',
  `url_token` varchar(64) NOT NULL COMMENT '用户URL Token',
  `gender` varchar(16) DEFAULT NULL COMMENT '用户性别',
  `ip_location` varchar(64) DEFAULT NULL COMMENT 'IP地理位置',
  `follows` int NOT NULL DEFAULT '0' COMMENT '关注数',
  `fans` int NOT NULL DEFAULT '0' COMMENT '粉丝数',
  `anwser_count` int NOT NULL DEFAULT '0' COMMENT '回答数',
  `video_count` int NOT NULL DEFAULT '0' COMMENT '视频数',
  `question_count` int NOT NULL DEFAULT '0' COMMENT '问题数',
  `article_count` int NOT NULL DEFAULT '0' COMMENT '文章数',
  `column_count` int NOT NULL DEFAULT '0' COMMENT '专栏数',
  `get_voteup_count` int NOT NULL DEFAULT '0' COMMENT '获得的赞同数',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_zhihu_creator_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知乎创作者';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'ai_content_automation'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-06 12:06:36
