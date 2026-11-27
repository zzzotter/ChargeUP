"""内置默认分类与商户词库（分类优先级中的第二档）。"""

from __future__ import annotations

from app.domain.enums import CategoryType

# (分类名, 类型)
DEFAULT_CATEGORIES: tuple[tuple[str, CategoryType], ...] = (
    ("餐饮", CategoryType.EXPENSE),
    ("交通", CategoryType.EXPENSE),
    ("购物", CategoryType.EXPENSE),
    ("娱乐", CategoryType.EXPENSE),
    ("医疗", CategoryType.EXPENSE),
    ("居住", CategoryType.EXPENSE),
    ("其他支出", CategoryType.EXPENSE),
    ("工资", CategoryType.INCOME),
    ("退款", CategoryType.INCOME),
    ("其他收入", CategoryType.INCOME),
)

# (关键词, 目标分类名)
BUILTIN_KEYWORDS: tuple[tuple[str, str], ...] = (
    # 餐饮
    ("星巴克", "餐饮"),
    ("瑞幸", "餐饮"),
    ("麦当劳", "餐饮"),
    ("肯德基", "餐饮"),
    ("海底捞", "餐饮"),
    ("美团", "餐饮"),
    ("饿了么", "餐饮"),
    ("便利店", "餐饮"),
    ("餐厅", "餐饮"),
    # 交通
    ("滴滴", "交通"),
    ("地铁", "交通"),
    ("公交", "交通"),
    ("加油", "交通"),
    ("中石化", "交通"),
    ("停车", "交通"),
    ("12306", "交通"),
    ("高铁", "交通"),
    # 购物
    ("淘宝", "购物"),
    ("天猫", "购物"),
    ("京东", "购物"),
    ("拼多多", "购物"),
    ("优衣库", "购物"),
    ("超市", "购物"),
    # 娱乐
    ("电影", "娱乐"),
    ("网易云", "娱乐"),
    ("腾讯视频", "娱乐"),
    ("steam", "娱乐"),
    # 医疗
    ("药店", "医疗"),
    ("医院", "医疗"),
    # 居住
    ("房租", "居住"),
    ("物业", "居住"),
    ("电费", "居住"),
    ("水费", "居住"),
    ("燃气", "居住"),
    # 收入
    ("工资", "工资"),
    ("薪水", "工资"),
    ("奖金", "工资"),
    ("退款", "退款"),
)
