-- ============================================================================
-- Align ContentRemixAgent with main auth/cookies domain
-- Target DB snapshot: ai_content_automation_2026-04-17_221702.sql
--
-- Purpose:
-- 1) Remove ContentRemixAgent's own user/cookies tables.
-- 2) Keep AI/chat tables (llm_configs, insight_modes, agent_*).
-- 3) Convert agent_* user_id from VARCHAR(36) to BIGINT UNSIGNED
--    to align with main project iam_users.id.
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- A. Drop ContentRemixAgent user/auth tables (main project IAM is authoritative)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `email_verification_tokens`;
DROP TABLE IF EXISTS `user_oauth_accounts`;
DROP TABLE IF EXISTS `user_refresh_tokens`;
DROP TABLE IF EXISTS `users`;

-- ----------------------------------------------------------------------------
-- B. Drop ContentRemixAgent cookies table (main project platform account domain
--    is authoritative: platform_accounts + platform_account_sessions)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `platform_cookies`;

-- ----------------------------------------------------------------------------
-- C. Convert agent_* user_id to BIGINT UNSIGNED (idempotent)
-- ----------------------------------------------------------------------------
DELIMITER //

DROP PROCEDURE IF EXISTS migrate_agent_user_id_to_bigint//
CREATE PROCEDURE migrate_agent_user_id_to_bigint(
    IN p_table_name VARCHAR(64)
)
BEGIN
    DECLARE v_col_type VARCHAR(128) DEFAULT NULL;
    DECLARE v_has_idx INT DEFAULT 0;

    -- Check current user_id type
    SELECT DATA_TYPE
      INTO v_col_type
      FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = p_table_name
       AND COLUMN_NAME = 'user_id'
     LIMIT 1;

    -- Only migrate when user_id is a character type
    IF v_col_type IN ('varchar', 'char', 'text', 'mediumtext', 'longtext') THEN
        -- Add temp bigint column if absent
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` ',
            'ADD COLUMN IF NOT EXISTS `user_id_new` BIGINT UNSIGNED NULL COMMENT ''关联 iam_users.id'''
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        -- Copy convertible numeric values, non-numeric become NULL
        SET @sql = CONCAT(
            'UPDATE `', p_table_name, '` ',
            'SET `user_id_new` = CASE ',
            'WHEN `user_id` REGEXP ''^[0-9]+$'' THEN CAST(`user_id` AS UNSIGNED) ',
            'ELSE NULL END'
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        -- Drop old index if exists
        SELECT COUNT(*)
          INTO v_has_idx
          FROM information_schema.STATISTICS
         WHERE TABLE_SCHEMA = DATABASE()
           AND TABLE_NAME = p_table_name
           AND INDEX_NAME = 'idx_user_id';

        IF v_has_idx > 0 THEN
            SET @sql = CONCAT('ALTER TABLE `', p_table_name, '` DROP INDEX `idx_user_id`');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
        END IF;

        -- Replace old column
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` ',
            'DROP COLUMN `user_id`, ',
            'CHANGE COLUMN `user_id_new` `user_id` BIGINT UNSIGNED NULL COMMENT ''关联 iam_users.id'''
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        -- Recreate index
        SET @sql = CONCAT('ALTER TABLE `', p_table_name, '` ADD INDEX `idx_user_id` (`user_id`)');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//

DELIMITER ;

CALL migrate_agent_user_id_to_bigint('agent_sessions');
CALL migrate_agent_user_id_to_bigint('agent_checkpoints');
CALL migrate_agent_user_id_to_bigint('agent_store');

DROP PROCEDURE IF EXISTS migrate_agent_user_id_to_bigint;

-- ----------------------------------------------------------------------------
-- D. Ensure chat/AI core tables exist (safe no-op when already present)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `llm_configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置名称，如 default, reasoning, fast',
  `provider` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商: openai / anthropic / deepseek / ollama',
  `is_active` tinyint DEFAULT '0' COMMENT '是否为当前激活配置: 0=否, 1=是',
  `api_key` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API Key',
  `base_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API 基础 URL',
  `model_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `enable_thinking` tinyint DEFAULT '0' COMMENT '启用思考模式: 0=否, 1=是',
  `thinking_budget_tokens` int DEFAULT '4096' COMMENT 'Anthropic Extended Thinking token 预算',
  `reasoning_effort` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'high' COMMENT 'OpenAI 推理强度',
  `support_multimodal` tinyint DEFAULT '0' COMMENT '是否支持多模态（图片理解）: 0=否, 1=是',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '配置描述/备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_name` (`config_name`),
  KEY `idx_provider` (`provider`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM 配置管理表';

CREATE TABLE IF NOT EXISTS `insight_modes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mode_key` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模式标识 (如 summarize, analyze)',
  `is_active` tinyint DEFAULT '1' COMMENT '是否启用',
  `sort_order` int DEFAULT '0' COMMENT '显示排序',
  `label_zh` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '中文名称',
  `label_en` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '英文名称',
  `description_zh` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '中文描述',
  `description_en` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '英文描述',
  `prefill_zh` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '中文输入预填充',
  `prefill_en` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '英文输入预填充',
  `icon` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'smart_toy' COMMENT 'Material Symbols 图标名',
  `color` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'cyan' COMMENT '颜色主题',
  `keywords_zh` text COLLATE utf8mb4_unicode_ci COMMENT '中文关键词',
  `keywords_en` text COLLATE utf8mb4_unicode_ci COMMENT '英文关键词',
  `system_prompt` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模式专属提示词',
  `is_system` tinyint DEFAULT '0' COMMENT '系统内置 (1=不可删除)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mode_key` (`mode_key`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分析模式配置表';

SET FOREIGN_KEY_CHECKS = 1;

