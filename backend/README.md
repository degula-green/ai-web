# Backend

`backend/` 是当前主后端工作区，承载主业务接口和多个采集相关子系统。

## 目录说明

- `app/`
  主 FastAPI 应用。当前最重要的业务逻辑都在这里。
- `tests/`
  主后端的正式测试目录，默认保留。
- `scripts/`
  运维、数据校验和手动排障脚本。
  其中 `scripts/debug/` 用于收纳一次性调试脚本，避免散落在根目录。
- `agent-stack/`
  与采集、授权、数字人辅助链路相关的子系统集合。
- `runtime/`
  运行时输出目录，例如临时剪辑文件、缓存等。
- `exports/`
  导出结果或中间产物。

## 主入口

- API 启动：`app.main:app`
- 当前重点服务：
  `app/services/clip_render_service.py`
  `app/services/creation_draft_service.py`
  `app/api/v1`

## 常用命令

```powershell
uv sync
uv run python -m uvicorn app.main:app --reload
uv run pytest tests/test_health.py -q
```

## 清理约定

- `tests/` 保留，除非确认已经失效且被替代。
- `scripts/` 中以 `test_*.py` 命名的文件多数是手动验证脚本，不等同于正式自动化测试；保留前应明确用途。
- `scripts/debug/` 中的文件默认为临时排障脚本，问题解决后应及时删除或迁移到正式目录。
- `runtime/`、`.pytest_cache/`、临时导出物应定期清理，不应提交业务无关内容。
