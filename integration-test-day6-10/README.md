# ledger-guard 集成测试工程（第 6–10 天，测试先行，独立工程）

本工程只包含分工表第 6–10 天集成任务，与第 2–5 天工程分开维护。金额全程整数分、不引入 float。当前 `pytest`：**37 passed**。

> 说明：领域规则依赖解析器的数据结构，因此本工程内保留了一份 `parser/` 作为运行依赖；正式合并时以主仓库中的解析器为准，本包不重复定义其行为，也不含解析器自身的单元测试。

## 一、对应任务与交付物

| 天 | 集成任务 | 本工程交付 |
| --- | --- | --- |
| 6 | 重复导入、缺列/空行/乱码 | `domain/importer.py` + `gateway/`（端口 + Mock/Http 适配器） |
| 7 | 规则优先级、未匹配归箱 | `domain/classification.py` |
| 8 | 退款、转账、坏账单回归 | `domain/refund.py` |
| 9 | 统计口径、对账样例 | `domain/stats.py` |
| 10 | 80%/100% 阈值、重复触发 | `domain/budget.py` |

## 二、目录结构

```
ledger-guard-day6-10/
├── pyproject.toml / requirements.txt / .gitignore
├── docs/
│   ├── csv-format-analysis.md
│   └── integration-test-plan-6-10.md
├── data/
│   ├── real_samples/                # 真实账单（gitignore，不入库）
│   └── fixtures/                    # 脱敏合成 fixture（导入测试用）
├── src/ledger_guard/
│   ├── parser/                      # 运行依赖（来自第2-5天成果）
│   ├── domain/                      # 纯领域规则
│   ├── gateway/                     # 端口 + Mock/Http 适配器
│   └── contracts/                   # 含扩展 DTO
└── tests/
    ├── domain/                      # 第6-10天规则测试
    └── contracts/                   # 契约 DTO 测试
```

## 三、运行方式

```bash
pip install -r requirements.txt
python3 -m pytest
```

## 四、关键设计与底线

1. **整数分零浮点**：领域与 DTO 全程拒绝 float，阈值用整数交叉相乘比较。
2. **六边形分层**：domain 为纯函数不依赖框架；通过 gateway 端口隔离数据库，Mock 与 Http 适配器可互换，测试断言不返工。
3. **坏账单不崩溃**：导入侧对拒识/0 元/重复分别计数，不产生脏数据。

## 五、待团队确认项

1. 第 6–10 天 DTO 字段/枚举为建议值；统计退款是否冲减支出口径待冻结；
2. 沿用未决项：0 元记录去留、是否新增 NON_CASH 枚举。

