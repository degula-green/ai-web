# Backend Scripts

这里存放主后端的辅助脚本，不是正式业务入口。

## 当前文件

- `verify_auth_db.py`
  校验认证相关数据是否正确落库。
- `test_platform_auth.py`
  平台授权链路的手动验证脚本。
- `test_platform_auth_v2.py`
  平台授权链路的第二版手动验证脚本。
- `sql/`
  一次性或补充型 SQL 脚本。

## 约定

- 保留有明确用途的排障脚本。
- 没有说明、没有引用、无法复现价值的脚本应优先清理。
- 新增脚本时请在本 README 补一行用途说明。
