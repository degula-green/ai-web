from sqlalchemy import Column, String, BigInteger, DateTime, func, Index, UniqueConstraint
from app.db.base import Base

class UserContentRelation(Base):
    """
    用户内容关联链表 (V4.2)
    存储用户与各个平台视频/内容的绑定关系，去中心化 ID 设计。
    """
    __tablename__ = "user_content_relations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="归属用户ID")
    platform = Column(String(16), nullable=False, comment="平台标识 (dy, xhs, bili, ks, wb, tieba, zhihu)")
    
    # 显式 ID 字段 - 根据平台不同填入对应列
    dy_aweme_id = Column(String(64), nullable=True, comment="抖音视频ID")
    xhs_note_id = Column(String(64), nullable=True, comment="小红书笔记ID")
    wb_note_id = Column(String(64), nullable=True, comment="微博帖子ID")
    tieba_note_id = Column(String(64), nullable=True, comment="贴吧帖子ID")
    bili_video_id = Column(String(64), nullable=True, comment="B站视频ID")
    ks_video_id = Column(String(64), nullable=True, comment="快手视频ID")
    zhihu_content_id = Column(String(64), nullable=True, comment="知乎内容ID")
    
    task_id = Column(String(64), nullable=True, comment="来源任务ID")
    created_at = Column(DateTime, server_default=func.now())

    # 索引与约束
    __table_args__ = (
        Index('idx_user_platform', 'user_id', 'platform'),
        UniqueConstraint(
            'user_id', 'platform', 
            'dy_aweme_id', 'xhs_note_id', 'wb_note_id', 
            'tieba_note_id', 'bili_video_id', 'ks_video_id', 'zhihu_content_id',
            name='uk_user_content'
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "dy_aweme_id": self.dy_aweme_id,
            "xhs_note_id": self.xhs_note_id,
            "wb_note_id": self.wb_note_id,
            "tieba_note_id": self.tieba_note_id,
            "bili_video_id": self.bili_video_id,
            "ks_video_id": self.ks_video_id,
            "zhihu_content_id": self.zhihu_content_id,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
