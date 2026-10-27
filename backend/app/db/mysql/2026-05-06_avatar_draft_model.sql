-- 模特数字人草稿分表
CREATE TABLE IF NOT EXISTS avatar_draft_model (
    draft_id VARCHAR(64) PRIMARY KEY COMMENT '模特数字人草稿ID，对应 avatar_drafts.draft_id',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
    title VARCHAR(255) NULL COMMENT '草稿标题',
    product_keyword VARCHAR(255) NULL COMMENT '产品搜索关键词',
    selected_product_id VARCHAR(64) NULL COMMENT '已选择的产品ID',
    selected_product_profile JSON NOT NULL COMMENT '已选择产品资料快照',
    product_assets JSON NOT NULL COMMENT '当前产品素材列表快照',
    selected_white_image_id VARCHAR(64) NULL COMMENT '已选白底图素材ID',
    selected_wear_image_id VARCHAR(64) NULL COMMENT '已选佩戴图素材ID',
    model_image_url VARCHAR(2048) NULL COMMENT '模特数字人图片地址',
    scene_image_url VARCHAR(2048) NULL COMMENT '场景参考图地址',
    image_count INT NOT NULL DEFAULT 8 COMMENT '需要生成的展示图数量',
    aspect_ratio VARCHAR(32) NOT NULL DEFAULT '3:4' COMMENT '展示图比例',
    extra_requirements TEXT NULL COMMENT '补充要求',
    gallery_task_id VARCHAR(64) NULL COMMENT '图组生成任务ID',
    gallery_task_status VARCHAR(32) NULL COMMENT '图组生成任务状态',
    gallery_images JSON NOT NULL COMMENT '已持久化的图组结果列表',
    status VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '模特草稿状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY idx_avatar_draft_model_user_updated (user_id, updated_at),
    KEY idx_avatar_draft_model_user_status (user_id, status),
    KEY idx_avatar_draft_model_product (selected_product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模特数字人草稿分表';

-- 将历史 creation_drafts 中的模特数字人草稿回填到模特分表
INSERT INTO avatar_draft_model (
    draft_id,
    user_id,
    title,
    product_keyword,
    selected_product_id,
    selected_product_profile,
    product_assets,
    selected_white_image_id,
    selected_wear_image_id,
    model_image_url,
    scene_image_url,
    image_count,
    aspect_ratio,
    extra_requirements,
    gallery_task_id,
    gallery_task_status,
    gallery_images,
    status,
    created_at,
    updated_at
)
SELECT
    cd.id AS draft_id,
    cd.user_id,
    cd.title,
    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(cd.content_info, '$.product_keyword')), '') AS product_keyword,
    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.selected_product_id')), '') AS selected_product_id,
    COALESCE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.selected_product_profile'), JSON_OBJECT()) AS selected_product_profile,
    COALESCE(
        JSON_EXTRACT(cd.digital_human_params, '$.model_scene.product_assets'),
        JSON_EXTRACT(cd.content_info, '$.product_assets'),
        JSON_ARRAY()
    ) AS product_assets,
    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.selected_white_image_id')), '') AS selected_white_image_id,
    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.selected_wear_image_id')), '') AS selected_wear_image_id,
    NULLIF(
        COALESCE(
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.model_image_url')),
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.image_url'))
        ),
        ''
    ) AS model_image_url,
    NULLIF(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.scene_image_url')), '') AS scene_image_url,
    COALESCE(CAST(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.image_count')) AS UNSIGNED), 8) AS image_count,
    COALESCE(JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.aspect_ratio')), '3:4') AS aspect_ratio,
    NULLIF(
        COALESCE(
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.extra_requirements')),
            cd.rewrite_instruction
        ),
        ''
    ) AS extra_requirements,
    NULLIF(
        COALESCE(
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.gallery_task_id')),
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.task_id'))
        ),
        ''
    ) AS gallery_task_id,
    NULLIF(
        COALESCE(
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.gallery_task_status')),
            JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.task_status'))
        ),
        ''
    ) AS gallery_task_status,
    COALESCE(JSON_EXTRACT(cd.digital_human_params, '$.model_scene.gallery_images'), JSON_ARRAY()) AS gallery_images,
    COALESCE(cd.status, 'draft') AS status,
    cd.created_at,
    cd.updated_at
FROM creation_drafts cd
WHERE
    JSON_UNQUOTE(JSON_EXTRACT(cd.digital_human_params, '$.video_purpose')) = '模特数字人'
    OR JSON_EXTRACT(cd.digital_human_params, '$.model_scene') IS NOT NULL
    OR cd.status = 'gallery_generated'
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    product_keyword = VALUES(product_keyword),
    selected_product_id = VALUES(selected_product_id),
    selected_product_profile = VALUES(selected_product_profile),
    product_assets = VALUES(product_assets),
    selected_white_image_id = VALUES(selected_white_image_id),
    selected_wear_image_id = VALUES(selected_wear_image_id),
    model_image_url = VALUES(model_image_url),
    scene_image_url = VALUES(scene_image_url),
    image_count = VALUES(image_count),
    aspect_ratio = VALUES(aspect_ratio),
    extra_requirements = VALUES(extra_requirements),
    gallery_task_id = VALUES(gallery_task_id),
    gallery_task_status = VALUES(gallery_task_status),
    gallery_images = VALUES(gallery_images),
    status = VALUES(status),
    updated_at = VALUES(updated_at);
