"""前端联调前使用的模拟数据（结构与正式接口一致，可直接被 DTO 校验）。"""

MOCK_TRANSACTIONS = [
    {
        "id": 1001,
        "external_id": "202609150001",
        "source": "ALIPAY",
        "amount_cents": 3500,
        "direction": "EXPENSE",
        "counterparty": "星巴克咖啡",
        "item_name": "拿铁咖啡",
        "transacted_at": "2026-09-15T09:12:00",
        "status": "交易成功",
        "category_id": 12,
        "deleted_at": None,
    },
    {
        "id": 1002,
        "external_id": "202609150002",
        "source": "WECHAT",
        "amount_cents": 2880,
        "direction": "EXPENSE",
        "counterparty": "滴滴出行",
        "item_name": "快车车费",
        "transacted_at": "2026-09-15T19:40:00",
        "status": "支付成功",
        "category_id": 7,
        "deleted_at": None,
    },
    {
        "id": 1003,
        "external_id": "202609160003",
        "source": "ALIPAY",
        "amount_cents": 50000,
        "direction": "TRANSFER",
        "counterparty": "本人银行卡",
        "item_name": "转账到银行卡",
        "transacted_at": "2026-09-16T10:05:00",
        "status": "交易成功",
        "category_id": None,
        "deleted_at": None,
    },
    {
        "id": 1004,
        "external_id": "202609170004",
        "source": "WECHAT",
        "amount_cents": 1990,
        "direction": "EXPENSE",
        "counterparty": "便利店",
        "item_name": "待分类杂项",
        "transacted_at": "2026-09-17T12:30:00",
        "status": "支付成功",
        "category_id": None,  # 未分类，进入待分类收件箱
        "deleted_at": None,
    },
    {
        "id": 1005,
        "external_id": "202609180005",
        "source": "ALIPAY",
        "amount_cents": 6600,
        "direction": "INCOME",
        "counterparty": "退款商户",
        "item_name": "商品退款",
        "transacted_at": "2026-09-18T15:00:00",
        "status": "退款成功",
        "category_id": None,
        "deleted_at": None,
    },
]

MOCK_PAGE = {
    "items": MOCK_TRANSACTIONS,
    "total": len(MOCK_TRANSACTIONS),
    "page": 1,
    "page_size": 20,
}

# 合法的快捷录入样例
MOCK_QUICK_ENTRY = {
    "source": "WECHAT",
    "amount_cents": 1234,
    "direction": "EXPENSE",
    "counterparty": "测试商户",
    "item_name": "测试商品",
    "transacted_at": "2026-09-20T08:30:00",
    "category_id": None,
}
