# ledger-guard 第 11 天集成检查工程

对应分工表第 11 天：加入软删除、日志脱敏和领域层依赖检查用例。当前 **9 passed**。

## 目录

```
ledger-guard-day11/
├── pyproject.toml
├── conftest.py                 # 自动定位并连接 ChargeUP/backend，提供内存 TestClient
├── docs/day11-checklist.md     # 检查项/预期/结果清单
└── tests/
    ├── test_soft_delete.py     # 软删除、硬删除 405、恢复、统计排除
    ├── test_redaction.py       # 单号/手机号脱敏、日志过滤器
    └── test_domain_purity.py   # 领域层框架依赖检查
```

## 运行

```bash
python3 -m pytest
```

conftest 会把同仓 `ChargeUP/backend` 加入路径，使用 SQLite 内存库运行，无需 PostgreSQL，也不修改后端任何文件。本工程不含真实账单，可直接上传。
