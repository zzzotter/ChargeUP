# 第 6–10 天集成测试用例说明（测试先行版）

> 策略：先把业务规则和预期结果用可运行测试钉死，后端交付后只替换适配器、断言不变。
> 当前 `pytest` 全部通过：67 passed。

## 一、依赖分类总览

| 类别 | 含义 | 涉及内容 |
| --- | --- | --- |
| A | 纯领域规则，现在独立可跑 | 第 7/8/9/10 天规则逻辑 |
| B | 端口 + 内存 mock，后端来了换 httpx | 第 6 天导入幂等 |
| C | 必须等真实交付确认 | 真实端点/状态码、OpenAPI 一致性、真实库行为 |

## 二、逐天用例与测试文件

### 第 6 天 · 导入幂等（B 类）
测试：`tests/domain/test_import_idempotency.py`
- 首次导入全部 inserted；同一账单再次导入 inserted=0、全部 duplicated，库内条数不翻倍；
- 新旧单号混合批次分别计数；0 元 zero_skipped、拒识行 rejected。
- 切换点：`MockGateway` → `HttpGateway`（见 `gateway/http_gateway.py` 待实现方法）。

### 第 7 天 · 分类规则优先级与归箱（A 类）
测试：`tests/domain/test_classification.py`
- 按商品/对方关键词命中；大小写不敏感；
- 自定义规则优先于系统规则；同源内 priority 小者优先；
- 未命中返回 None，进入待分类收件箱。

### 第 8 天 · 退款与转账（A 类）
测试：`tests/domain/test_refund.py`
- 7 天窗口内全额/部分退款配对；超窗、退款额大于消费、名称不匹配均不配对；
- 一笔退款只配一次；转账/中性强制排除。

### 第 9 天 · 月度统计对账（A 类）
测试：`tests/domain/test_stats.py`
- 已知数据集手算复核：支出 3500、收入 5000、净结余 1500；转账与 0 元排除；
- 跨月过滤、按分类分组。

### 第 10 天 · 预算阈值与重复触发（A 类）
测试：`tests/domain/test_budget.py`
- 80% WARNING、100% CRITICAL；79.99% 不触发；
- 同等级幂等不重复告警；升级只追加新等级。

### 扩展契约 DTO
测试：`tests/contracts/test_extended_contract.py`，校验导入结果/规则/退款/统计/预算 DTO 的整数分、枚举与 extra forbid。

## 三、待团队冻结的约定（影响 C 类落地）

1. 导入结果、分类规则、统计、预算预警的字段名与枚举（当前 DTO 为建议值）；
2. 统计口径：退款是否冲减支出（默认计入收入）；
3. 沿用此前未决项：微信 xlsx 措辞、0 元记录去留、是否新增 NON_CASH 枚举。

## 四、后端交付后的执行步骤

1. 取得 base_url 与 OpenAPI，实现 `HttpGateway` 两个方法并校准端点；
2. 把导入测试的 `MockGateway` 替换为 `HttpGateway`，新增真实 HTTP 契约测试；
3. 运行全量 `pytest`：DTO 报错即后端响应不符契约，打回后端；
4. 前端交付后抓包核对请求体/响应，再按第 1 天 44 项清单做端到端验收。
