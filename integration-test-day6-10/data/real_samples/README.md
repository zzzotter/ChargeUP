# 真实账单放置区（本目录文件不入库）

官方导出的原始账单已归档于此，仅用于本地格式校准：

- 支付宝：`alipay_原始.csv`（GBK/GB18030，表头第 24 行）
- 微信：`wechat_原始.xlsx`（Excel 格式，表头第 18 行）

注意：

1. 本目录已被 `.gitignore` 排除，真实账单不会进入版本库；
2. 不要把真实账单复制到 `data/fixtures/`，测试统一使用脱敏合成 fixture；
3. 校准结论见 `docs/csv-format-analysis.md`。
