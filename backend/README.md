# ledger-guard 后端（P0 核心记账）

对应开发计划 **第 1–11 天后端任务**的完整交付。这些任务只依赖后端自身产出的接口约定，
不依赖前端页面或集成测试的前置交付；第 12 天的「修复 P0 联调问题」需要等联调缺陷清单，故未包含。

## 交付范围与计划对照

| 天 | 计划任务 | 落地位置 |
|---|---|---|
| 1 | 梳理实体、状态和 API 草案 | `app/domain/entities.py`、`app/domain/enums.py`、`/docs` OpenAPI |
| 2 | 初始化 FastAPI、数据库连接与迁移 | `app/main.py`、`app/infrastructure/db.py`、`alembic/` |
| 3 | 交易/分类/规则模型；整数分、软删除 | `app/infrastructure/models.py`、`alembic/versions/0001_*` |
| 4 | 快捷录入与交易列表 API | `POST /transactions`、`GET /transactions` |
| 5 | 交易 API 完成 + OpenAPI 草案 | `PATCH/DELETE /transactions/{id}`、自动生成的 Swagger、静态草案 `../api/openapi.yaml` |
| 6 | 导入写入、幂等去重 | `POST /imports/csv`、`(source, external_id)` 唯一约束 |
| 7 | 分类规则匹配、待分类收件箱 | `app/domain/services/categorization.py`、`GET /transactions/inbox` |
| 8 | 退款关联与转账排除 | `app/domain/services/refunds.py`、统计口径 |
| 9 | 月度统计 API | `GET /stats/summary`、`GET /stats/monthly`、`GET /stats/categories` |
| 10 | 预算双阈值与预警事件 | `app/domain/services/budget.py`、`/budget`、`/alerts` |
| 11 | 软删除、日志脱敏、领域层依赖检查 | `deleted_at`、`app/domain/redaction.py`、`tools/domain_purity.py` |

## 架构（六边形）

```
app/
  domain/        纯领域：实体、枚举、金额、分类/退款/统计/预算/账单解析（CSV+XLSX，禁止 import 框架）
  application/   用例编排：只依赖 domain 端口
  infrastructure/ SQLAlchemy 模型、仓储、工作单元、播种、日志脱敏
  interfaces/    FastAPI 路由、Pydantic DTO、统一错误处理
alembic/         数据库迁移
tools/           领域层依赖检查等开发期工具
tests/           单元 + API 测试与坏账单 fixture
```

依赖方向：`interfaces -> application -> domain`，`infrastructure` 实现 `domain/ports`。

## 快速开始

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt

# 1) 配置：复制 .env.example 为 .env（应用与 compose 都会加载；已导出的环境变量优先）
copy .env.example .env
# 修改其中的 POSTGRES_PASSWORD，并同步修改 DATABASE_URL

# 2) 启动开发数据库（PostgreSQL 16 + pgvector，端口仅绑 127.0.0.1）
docker compose up -d db

# 3) 建表（二选一；0001 初始结构 → 0002 金额 BIGINT → 0003 预警事件失效标记 → 0004 前端契约字段）
alembic upgrade head
# 或本地临时建表：在 .env 里设 CREATE_SCHEMA_ON_STARTUP=true

# 4) 启动（未配置 API_TOKEN 时请只绑定回环地址）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- OpenAPI 文档：<http://localhost:8000/docs>；不启动服务也能看的静态草案：`../api/openapi.yaml`（第 5 天交付）
- 静态草案由 `app.openapi()` 导出，接口改动后需重新生成（文件头有命令）
- 健康检查：`GET /api/v1/health`、`GET /api/v1/health/ready`（均免鉴权）

> 本地 Python 3.14 无 `psycopg` 预编译包时，测试可直接用 SQLite 内存库跑通（见 `tests/conftest.py`）。
> 生产按 SRS 使用 Python 3.12/3.13 + PostgreSQL 16。

## 安全

- **鉴权**：在 `.env` 设置 `API_TOKEN` 后，除 `/health*` 外所有接口都要求
  `Authorization: Bearer <token>`（常量时间比较，失败返回 401）；未设置时保持免鉴权模式，
  启动日志会告警，此时**只能绑定 `127.0.0.1`**，不得直接暴露到局域网/公网。
- **文档**：配置令牌后 `/docs`、`/redoc`、`/openapi.json` 默认关闭（404）；
  若显式 `DOCS_ENABLED=true`，这些路径同样要求 Bearer 令牌（401）。
- **健康检查**：只返回存活/就绪信息，不暴露鉴权开关；时区同时给出配置值
  `timezone` 与实际生效值 `timezone_effective`、`timezone_fallback`。
- **金额上限**：单笔金额上限 100 亿元（`10^12` 分），超出返回 422；数据库列已升级为 `BIGINT`。
- **全角输入**：金额解析前做 NFKC 归一化，`１２３．４５`、`￥１，２３４．５６` 均可直接录入。
- **错误结构**：所有错误统一为 `{code, message, details.request_id}`，响应头 `X-Request-ID` 可追溯；
  500 不返回堆栈。
- **数据库与凭据**：compose 的用户名/密码/库名全部来自 `backend/.env`，
  端口映射为 `127.0.0.1:5432:5432`，不会把数据库暴露到局域网。
- **脱敏**：拒识原文、日志中的长单号/手机号会先遮蔽再输出。

## 测试

```bash
pytest                                   # 全部用例
python scripts/check_domain_purity.py    # 领域层依赖门禁
```

测试覆盖：金额分转换与溢出/上限/全角、规则优先级、退款识别（含误配回归）、统计口径、
预算阈值幂等与事件失效/再激活、CSV/XLSX 头部跳过/GBK/空行/缺列/乱码/拒识计数、导入幂等、
显式来源、软删除、LIKE 转义、`.env` 加载、鉴权、文档保护、并发单号/预算冲突、
改方向后分类一致性、统一错误结构与中文文案、上传限额、日志脱敏、领域层纯度。

## API 一览（前缀 `/api/v1`，字段 lowerCamelCase，金额整数分）

> 完整契约见《页面清单-用户流程-线框.docx》§7。响应中的 `id/categoryId/importId` 均为字符串；
> 路径参数仍用整数。分页统一 `{items,page,pageSize,total}`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/transactions` | 列表：`month/source/categoryId/direction/q/page/pageSize/sort`；默认 `-occurredAt` |
| POST | `/transactions` | 快捷填写/手动写入：`merchant,amount,direction,occurredAt,categoryId?,note?`；服务端 `source=MANUAL` |
| GET | `/transactions/{id}` | 详情（软删除记录需 `includeDeleted=true`） |
| PATCH | `/transactions/{id}` | 编辑；`categoryId: null` 显式清空，`recategorize` 重跑规则，三者互斥 |
| DELETE | `/transactions/{id}` | 软删除返回 204；`hard=true` 一律 405 `HARD_DELETE_FORBIDDEN` |
| POST | `/transactions/{id}/restore` | 从回收恢复 |
| GET | `/transactions/inbox` | 待分类收件箱（不含转账） |
| POST | `/transactions/batch-classify` | 批量归类，可 `createRule.keyword` 同时沉淀用户规则 |
| POST | `/transactions/reclassify` | （扩展）重跑分类规则，单次最多 500 条 |
| POST | `/transactions/duplicates/check` | （扩展）同日同额弱指纹查重，`confidence` HIGH/LOW |
| GET/POST | `/categories` | 分类列表（含 `source/ruleCount`）/ 新建（name,type,color） |
| PATCH/DELETE | `/categories/{id}` | 改名/改色/停用；被交易引用时删除返回 409 `CONFLICT` |
| GET | `/categories/suggest?name=` | 快捷填写分类建议：`categoryId/matchedBy/ruleKeyword` |
| GET/POST | `/category-rules` | 规则列表（用户优先）/ 新建 |
| DELETE | `/category-rules/{id}` | 删除用户规则；内置规则只读返回 409 |
| POST | `/category-rules/test` | 干跑：命中分类与规则来源（RULE/BUILTIN） |
| POST | `/imports/csv` | 账单导入（CSV / XLSX 按文件头自动识别）：幂等去重；返回 `ImportReport`（importId/created/duplicated/failed/durationMs） |
| POST | `/imports/screenshot-candidates` | 截图候选批量入账（source=SCREENSHOT，自动生成 `SCR-*` 单号） |
| GET | `/imports` | 导入历史分页 |
| GET | `/imports/{id}/report` | 导入报告详情 |
| GET | `/stats/summary?month=` | 仪表盘概要：净支出/收入/剔除退款数/剔除转账数/未分类数 |
| GET | `/stats/monthly?months=6` | 月度支出趋势（升序） |
| GET | `/stats/categories?month=` | 分类分布：`categoryId/name/amount/ratio` |
| GET/PUT | `/budget` | 读取/保存预算；`amount` 整数分，`warnThreshold < alertThreshold`（0~1 小数） |
| GET | `/alerts` | 预警事件分页：`level/period/read/page/pageSize` |
| PATCH | `/alerts/{id}` | 标记已读 |
| GET/PATCH | `/settings` | 时薪（整数分或 null）/ 人设 / 模块开关 |

## 关键实现约定

- **整数分**：对外字段 `amount`/`totalExpense`/`actual` 等一律为整数「分」（内部仍以 `*_cents`、`BIGINT` 存储）；
  单笔上限 100 亿元，超限或非整数输入统一 422。
- **软删除**：`deletedAt` 表达删除；默认查询过滤，`includeDeleted=true` 可审计；无物理删除接口。
- **幂等导入**：`(source, external_id)` 唯一；软删除记录仍占单号，重复导入不会复活旧流水（如需恢复应走显式接口）。
- **分类优先级**：用户规则 > 内置词库 > `null`；未命中进入收件箱。规则与分类类型（收入/支出）匹配后才参与；
  显式指定的分类同样必须与收支方向一致，否则 422。
- **统计口径**：排除 `TRANSFER`；仅「金额相反 + 7 天内 + 商户可对应或收入带退款语义」的对才剔除，
  显式 `refund_of_transaction_id` 一律采信；普通收入（如工资）不会被误判为退款。
- **预算阈值**：库内以基点（bps）存储，`8000=80%`；API 对外暴露 0~1 小数（`warnThreshold`/`alertThreshold`）。
  事件表 `(period, level)` 唯一；支出回落后写入 `revoked_at`，再次越线时清除标记重新激活并重置已读，
  因此不会重复插入事件。`/alerts` 返回 `threshold`（事件创建时阈值快照）与 `read` 状态。
- **并发写入**：`(source, external_id)` 预检查只是优化，真正兜底是唯一约束；
  `IntegrityError` 在用例层转为 409。预算 `upsert` 先查后写可能撞唯一约束，
  用保存点捕获后重读再更新，并发 PUT 全部 200、以最后一次为准。
- **方向变更**：PATCH 改 `direction` 时会校验并清空不兼容分类（转账一律无分类），
  避免「收入挂支出分类」导致统计与分类分布对不上。
- **账单解析**：CSV（utf-8/gb18030）与 XLSX（openpyxl，含数字金额/日期单元格）共用表头自适应识别
  （不写死 24/16 行）；单行异常只拒识该行；`failed` 为真实总数，
  `failures` 明细最多 50 条；显式 `source` 优先于内容探测；旧版 `.xls` 提示另存为 `.xlsx`/`.csv`。
- **上传统计**：先看 `Content-Length` 快速拒绝，再按 256KB 分块读取，超限立即中断。
- **脱敏**：拒识原文与日志都会遮蔽 11 位以上数字/长单号后再输出。

## 未决事项（UNSPECIFIED 默认决策）

1. 同一 `(source, external_id)` 的软删除记录再次导入时跳过（不复活），避免历史流水被意外改写。
2. 跨月退款对在两个月各自剔除对应一侧：当月支出扣除原支出，次月不把退款计为收入。
3. 截图 OCR 在浏览器本地完成（前端职责），后端只接收已确认的候选流水并做弱指纹查重。
4. 无法证明是退款的收入（商户不同且无退款语义）按普通收入计入 `income_cents`；
   如需人工确认，后续可扩展「疑似退款待确认」列表，而不是自动从统计中剔除。
5. 单机自托管且未配置 `API_TOKEN` 时，接口按设计不鉴权；部署时必须绑定 `127.0.0.1`
   或配置令牌，两者都不做就等同于把账本暴露给所有可达主机。
