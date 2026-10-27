-- =============================================================================
-- creation_drafts：表注释 + 各列 COMMENT（仅元数据）
-- =============================================================================
-- 执行前务必：SHOW CREATE TABLE creation_drafts;
-- 若 JSON 列实际为 NULL 或缺省值与下述不一致，请先按现表修正 MODIFY 子句。
-- 时间列建议：从 SHOW CREATE TABLE 复制原 `created_at` / `updated_at` 整段定义，
--             仅在末尾追加 COMMENT '...' 再执行（见文件末尾模板）。
-- =============================================================================

ALTER TABLE creation_drafts
  COMMENT = '创作草稿：01链接与元数据、原片ASR转录、改写文案、口播与数字人成片参数、剪辑策略；成片口播SRT可走路径乙不落库';

ALTER TABLE creation_drafts
  MODIFY COLUMN id VARCHAR(64) NOT NULL COMMENT '主键，业务草稿ID（如 draft_xxx）';

ALTER TABLE creation_drafts
  MODIFY COLUMN user_id BIGINT NOT NULL COMMENT '所属用户ID';

ALTER TABLE creation_drafts
  MODIFY COLUMN title VARCHAR(255) NULL COMMENT '草稿标题，常取自内容标题';

ALTER TABLE creation_drafts
  MODIFY COLUMN source_url VARCHAR(1024) NULL COMMENT '01 输入：社媒内容页/作品链接';

ALTER TABLE creation_drafts
  MODIFY COLUMN platform VARCHAR(64) NULL COMMENT '平台标识，如 dy/xhs/bilibili/ks';

ALTER TABLE creation_drafts
  MODIFY COLUMN content_id VARCHAR(255) NULL COMMENT '平台侧内容ID，可与 content_info 内冗余字段对应';

ALTER TABLE creation_drafts
  MODIFY COLUMN content_info JSON NOT NULL COMMENT '01 DownloadServer 解析结果：标题/描述/作者/封面与音视频URL等';

ALTER TABLE creation_drafts
  MODIFY COLUMN transcript JSON NOT NULL COMMENT '01 原素材 ASR：{text, segments[{start,end秒},text], content_id}；非数字人成片口播时间轴';

ALTER TABLE creation_drafts
  MODIFY COLUMN extracted_copy TEXT NULL COMMENT '01 LLM 整理后的原始口播/文案正文';

ALTER TABLE creation_drafts
  MODIFY COLUMN rewrite_instruction TEXT NULL COMMENT '02 改写附加说明/模板指令';

ALTER TABLE creation_drafts
  MODIFY COLUMN rewritten_copy TEXT NULL COMMENT '02 改写后的正文，供TTS与数字人';

ALTER TABLE creation_drafts
  MODIFY COLUMN voice_params JSON NOT NULL COMMENT '03 口播/TTS：音色、语速、各阶段音频URL(local/source/minio等)、record_id';

ALTER TABLE creation_drafts
  MODIFY COLUMN digital_human_params JSON NOT NULL COMMENT '04 数字人：模板/场景、任务状态、模板或成片 video/image URL（含公网签名链）';

ALTER TABLE creation_drafts
  MODIFY COLUMN clip_params JSON NOT NULL COMMENT '05 剪辑与成片选项：subtitle_mode、bgm、音量等；路径乙不在此持久化成片SRT';

ALTER TABLE creation_drafts
  MODIFY COLUMN status VARCHAR(32) NOT NULL COMMENT '草稿状态：draft/extracted/rewritten 等';

-- -----------------------------------------------------------------------------
-- 时间列：请用 SHOW CREATE TABLE creation_drafts; 中的原样定义替换下面两行占位，
-- 仅在每行末尾加上 COMMENT（避免误改 DEFAULT / ON UPDATE）。
-- 示例（勿直接执行，需替换为你的实际类型与默认值）：
--
-- ALTER TABLE creation_drafts
--   MODIFY COLUMN created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间';
-- ALTER TABLE creation_drafts
--   MODIFY COLUMN updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '最后更新时间';
-- -----------------------------------------------------------------------------
