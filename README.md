# ChargeUP

智能记账与消费干预系统（ledger-guard）。前后端同仓：

```
ChargeUP/
├─ web/       Next.js 16 前端（页面、组件、API 客户端）
├─ backend/   FastAPI 后端（六边形架构，P0 核心记账）
├─ api/       OpenAPI 契约草案（第 5 天交付，前后端对接基准）
└─ docs/      页面清单、用户流程、线框等交付文档
```

## 后端（backend/）

对应开发计划第 1–11 天后端任务：交易、分类与规则、CSV 导入、退款/转账统计口径、
月度统计、预算双阈值与预警、软删除与日志脱敏。

```powershell
cd ChargeUP/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt

copy .env.example .env      # 修改 POSTGRES_PASSWORD，并同步 DATABASE_URL
docker compose up -d db     # PostgreSQL 16（仅绑定 127.0.0.1:5432）
alembic upgrade head        # 或本地临时设 CREATE_SCHEMA_ON_STARTUP=true

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- OpenAPI：<http://localhost:8000/docs>（配置 `API_TOKEN` 后默认关闭）；不启动服务也能看的静态草案见 `api/openapi.yaml`
- 健康检查：`GET /api/v1/health`
- 测试：`pytest`、`python scripts/check_domain_purity.py`
- 接口前缀 `/api/v1`，字段 lowerCamelCase，金额为整数「分」，与 `web/lib/api/types.ts` 契约一致。

## 前端（web/）

```powershell
cd ChargeUP/web
npm install        # 或 pnpm install
npm run dev
```

默认使用同仓开发桩 `/api/dev`；接入真实后端时在 `web/.env.local` 写入：

```
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1
```

页面只依赖 `web/lib/api/client.ts`，切换后端无需改调用方。
