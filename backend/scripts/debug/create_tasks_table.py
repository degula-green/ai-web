import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path to import config
sys.path.append(os.getcwd())

from app.core.config import get_settings

def create_tasks_table():
    settings = get_settings()
    engine = create_engine(settings.mysql.sqlalchemy_url)
    
    sql = """
    CREATE TABLE IF NOT EXISTS `tasks` (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Tasks table created successfully.")

if __name__ == "__main__":
    create_tasks_table()
