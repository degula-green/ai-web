-- Development-stage reset for platform authorization domain.
-- Clear stale auth/account data first, then apply the new model.

TRUNCATE TABLE `platform_account_auth_logs`;
TRUNCATE TABLE `platform_account_contents`;
TRUNCATE TABLE `platform_account_sessions`;
TRUNCATE TABLE `platform_cookie_bridge_bindings`;
TRUNCATE TABLE `crawler_cookie_account_bindings`;
TRUNCATE TABLE `crawler_cookies_account`;
TRUNCATE TABLE `platform_accounts`;

ALTER TABLE `platform_accounts`
    ADD COLUMN `identity_type` VARCHAR(32) NULL COMMENT 'Primary identity type' AFTER `platform_uid`,
    ADD COLUMN `identity_value` VARCHAR(255) NULL COMMENT 'Primary identity value' AFTER `identity_type`,
    ADD COLUMN `sec_user_id` VARCHAR(255) NULL COMMENT 'Stable sec_user_id' AFTER `identity_value`,
    ADD COLUMN `account_status` VARCHAR(32) NOT NULL DEFAULT 'needs_rebind' COMMENT 'Account status: active/expired/account_mismatch/needs_rebind/disabled' AFTER `auth_status`,
    ADD COLUMN `last_identity_verified_at` DATETIME NULL COMMENT 'Last identity verified time' AFTER `account_status`,
    ADD COLUMN `last_identity_error` VARCHAR(500) NULL COMMENT 'Last identity validation error' AFTER `last_identity_verified_at`;

ALTER TABLE `platform_accounts`
    ADD KEY `idx_platform_accounts_sec_user_id` (`sec_user_id`),
    ADD KEY `idx_platform_accounts_identity_type_value` (`identity_type`, `identity_value`),
    ADD KEY `idx_platform_accounts_account_status` (`account_status`),
    ADD UNIQUE KEY `uk_owner_platform_sec_user_id` (`owner_user_id`, `platform_code`, `sec_user_id`);

ALTER TABLE `platform_account_sessions`
    ADD COLUMN `session_status` VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT 'Normalized session status: active/invalid/expired/account_mismatch/revoked' AFTER `status`,
    ADD COLUMN `cookie_hash` VARCHAR(128) NULL COMMENT 'Cookie hash' AFTER `session_status`,
    ADD COLUMN `storage_hash` VARCHAR(128) NULL COMMENT 'Local storage hash' AFTER `cookie_hash`,
    ADD COLUMN `source_type` VARCHAR(32) NULL COMMENT 'Session source type' AFTER `storage_hash`,
    ADD COLUMN `source_client_id` VARCHAR(128) NULL COMMENT 'Session source client id' AFTER `source_type`,
    ADD COLUMN `validated_identity` VARCHAR(255) NULL COMMENT 'Last validated identity value' AFTER `source_client_id`,
    ADD COLUMN `last_validation_error` VARCHAR(500) NULL COMMENT 'Last validation error' AFTER `validated_identity`;

ALTER TABLE `platform_account_sessions`
    ADD KEY `idx_pas_session_status` (`session_status`),
    ADD KEY `idx_pas_source` (`source_type`, `source_client_id`);

ALTER TABLE `platform_cookie_bridge_bindings`
    ADD COLUMN `last_reported_identity` VARCHAR(255) NULL COMMENT 'Last reported identity value' AFTER `is_default`,
    ADD COLUMN `last_reported_nickname` VARCHAR(255) NULL COMMENT 'Last reported nickname' AFTER `last_reported_identity`,
    ADD COLUMN `last_cookie_hash` VARCHAR(128) NULL COMMENT 'Last reported cookie hash' AFTER `last_reported_nickname`;

-- No data backfill is needed after the development-stage reset above.
