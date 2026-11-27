# 集成测试工程（第 2–5 天交付，已用真实账单校准）

本工程覆盖分工表第 2–5 天任务，所有金额全程使用整数分、不引入 float。已用真实导出文件完成格式校准，解析计数与账单头部统计完全一致。

## 一、对应任务与交付物

| 天 | 分工表任务 | 本工程交付 |
| --- | --- | --- |
| 2 | 初始化测试结构、整理样例 | 完整目录、`pyproject.toml`、`requirements.txt`、`.gitignore`、`conftest.py`、真实样例受保护目录 |
| 3 | 格式分析、构造正常与异常 fixture | `docs/csv-format-analysis.md`；8 个合成 fixture（支付宝 CSV + 微信 xlsx，含正常/空行/缺列/乱码） |
| 4 | 契约测试与模拟数据 | `contracts/schemas.py`（Pydantic v2）、`mock_data.py`、`tests/contracts/` |
| 5 | 解析器：编码、跳头、清洗 | `parser/`（table_source/encoding/money/base/alipay/wechat/service），独立于入库 API |

## 二、目录结构

```
ledger-guard-integration/
├── pyproject.toml
├── requirements.txt
├── .gitignore                       # 真实账单不入库
├── docs/csv-format-analysis.md      # 真实格式校准结论
├── scripts/generate_fixtures.py     # 可复现生成 CSV/xlsx fixture
├── data/
│   ├── real_samples/                # 真实账单（gitignore，仅本地校准）
│   └── fixtures/                    # 脱敏合成 fixture
├── src/ledger_guard/
│   ├── parser/                      # 表格适配、编码、元转分、解析器
│   └── contracts/                   # DTO、模拟数据
└── tests/                           # 36 个测试
```

## 三、运行方式

```bash
pip install -r requirements.txt
python3 scripts/generate_fixtures.py   # 可选，已随仓库提供
python3 -m pytest
```

当前结果：**36 passed**。

## 四、关键设计与底线

1. **整数分零浮点**：`money.py` 用 Decimal 精确转换，拒绝浮点入参与 >2 位小数；契约金额字段为 int 并在前置校验拒绝 float。
2. **CSV/xlsx 双格式适配**：`table_source.py` 把两类文件统一为字符串行表；xlsx 的 float 金额经 Decimal 还原、datetime 统一格式化，核心解析逻辑与格式解耦。
3. **按列名定位、不写死索引**：表头自动定位，真实列名/列序变化只改平台配置。
4. **坏账单不崩溃**：空行跳过、缺列/非法数据按行拒识、0 元单列、乱码 replace 兜底、无表头抛 `ParseError`。
5. **隐私隔离**：真实账单仅放 `real_samples/`（gitignore），测试统一用虚构脱敏数据。

## 五、真实校准结论与待团队确认项

1. **微信实际导出为 xlsx 而非 CSV**，SRS F-P0-01 措辞需更新或在导入说明中明确支持 xlsx；
2. 真实账单含 **0.00 元记录**，现单列 `zero_amount`、默认不计金额统计，是否保留待确认；
3. “不计收支/中性”现映射为 `TRANSFER` 以排除支出，是否新增 `NON_CASH` 枚举待确认；
4. 真实文件解析计数与头部统计一致：支付宝支出25/不计收支7，微信支出45/收入6/中性3。

## 六、后续衔接

- 第 6 天：对接导入 API，补重复导入幂等等测试；
- 第 8 天：退款配对（金额相反、7 天内）与转账排除业务回归；
- 后端 OpenAPI 就绪后，契约测试可直接替换为对真实接口的校验。
