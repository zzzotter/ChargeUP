# -*- coding: utf-8 -*-
"""生成贴近真实格式的合成测试 fixture。

支付宝：GB18030 CSV，表头第 24 行，13 列，收支 支出/收入/不计收支，含 0 元。
微信：openpyxl 生成 xlsx，表头第 18 行，11 列，收支 支出/收入/"/"，含退款对。
坏账单：空行、缺列、乱码（乱码仅 CSV 概念，xlsx 用缺列/空行覆盖）。
所有商户、单号均为虚构脱敏数据。运行：python3 scripts/generate_fixtures.py
"""
import csv
import io
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"

ALIPAY_HEADER = [
    "交易时间", "交易分类", "交易对方", "对方账号", "商品说明", "收/支",
    "金额", "收/付款方式", "交易状态", "交易订单号", "商家订单号", "备注", "",
]
WECHAT_HEADER = [
    "交易时间", "交易类型", "交易对方", "商品", "收/支", "金额(元)",
    "支付方式", "当前状态", "交易单号", "商户单号", "备注",
]


def a_row(no, t, cat, party, item, direction, amount, status="交易成功"):
    return [
        t, cat, party, "***", item, direction, amount, "花呗",
        status, f"AO{no}", f"MO{no}", "", "",
    ]


def w_row(no, t, ptype, party, item, direction, amount, pay, status):
    return [t, ptype, party, item, direction, amount, pay, status,
            f"WO{no}", f"WM{no}", "/"]


# 支付宝 10 行：EXPENSE4 / INCOME1 / TRANSFER5（含2条0元）
ALIPAY_ROWS = [
    a_row(1, "2026-11-01 09:10:00", "餐饮美食", "星巴克", "拿铁", "支出", "35.00"),
    a_row(2, "2026-11-01 19:40:00", "交通出行", "滴滴出行", "快车", "支出", "28.80"),
    a_row(3, "2026-11-02 12:00:00", "日用百货", "便利店", "午餐", "支出", "15.00"),
    a_row(4, "2026-11-03 18:00:00", "餐饮美食", "滨寿司", "寿司", "支出", "65.00"),
    a_row(5, "2026-11-04 10:00:00", "其他", "朋友", "转账进来", "收入", "100.00"),
    a_row(6, "2026-11-05 08:00:00", "信用借还", "花呗", "免押下单", "不计收支", "0.00"),
    a_row(7, "2026-11-05 09:00:00", "信用借还", "花呗", "解冻", "不计收支", "0.00"),
    a_row(8, "2026-11-06 13:30:00", "账户存取", "本人", "充值", "不计收支", "200.00"),
    a_row(9, "2026-11-06 13:50:00", "信用借还", "花呗", "自动还款", "不计收支", "315.61"),
    a_row(10, "2026-11-07 15:00:00", "退款", "便利店", "退款-押金", "不计收支", "0.01"),
]

# 微信 8 行：EXPENSE3 / INCOME3 / TRANSFER2
WECHAT_ROWS = [
    w_row(1, "2026-11-01 23:25:00", "商户消费", "拼多多", "先用后付", "支出", 296.67, "零钱", "支付成功"),
    w_row(2, "2026-11-02 13:17:00", "商户消费", "美团", "外卖", "支出", 34.80, "零钱", "支付成功"),
    w_row(3, "2026-11-03 20:19:00", "转账", "朋友", "微信转账", "收入", 49, "/", "已存入零钱"),
    w_row(4, "2026-11-04 18:29:00", "微信红包", "家人", "/", "收入", 200, "/", "已存入零钱"),
    w_row(5, "2026-11-05 18:25:00", "商户消费", "库迪咖啡", "拿铁", "支出", 10.90, "零钱", "支付成功"),
    w_row(6, "2026-11-06 17:50:00", "益禾堂-退款", "益禾堂", "退款", "收入", 12.90, "零钱", "已全额退款"),
    w_row(7, "2026-11-07 20:36:00", "零钱提现", "农业银行", "/", "/", 800.80, "农业银行储蓄卡", "提现已到账"),
    w_row(8, "2026-11-08 17:38:00", "零钱充值", "农业银行", "/", "/", 200, "农业银行储蓄卡", "充值完成"),
]


def csv_text(header, rows, prefix):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for i in range(1, prefix):
        w.writerow([f"--说明第{i}行--"])
    w.writerow(header)
    for r in rows:
        if not r:
            buf.write("\n")
        else:
            w.writerow(r)
    return buf.getvalue()


def write_csv(path, text, garbled=False):
    data = text.encode("gb18030")
    if garbled:
        # 在数据末尾追加无效字节，避免破坏表头；用于验证解码 replace 容错
        data = data + b"\n\xff\n"
    Path(path).write_bytes(data)


def write_xlsx(path, rows, prefix, header, missing_at=None, blank_at=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    for i in range(1, prefix):
        ws.append([f"说明第{i}行"])
    ws.append(header)
    for idx, r in enumerate(rows):
        if blank_at and idx in blank_at:
            ws.append([])
        if missing_at and idx in missing_at:
            ws.append(r[:2])  # 只保留前两列 -> 缺列
        else:
            ws.append(r)
    wb.save(path)


def main():
    out_a = FIX / "alipay"
    out_w = FIX / "wechat"
    out_a.mkdir(parents=True, exist_ok=True)
    out_w.mkdir(parents=True, exist_ok=True)

    # 支付宝 CSV
    write_csv(out_a / "alipay_normal.csv",
              csv_text(ALIPAY_HEADER, ALIPAY_ROWS, 24))
    write_csv(out_a / "alipay_empty_rows.csv",
              csv_text(ALIPAY_HEADER, [ALIPAY_ROWS[0], [], ALIPAY_ROWS[1]], 24))
    write_csv(out_a / "alipay_missing_cols.csv",
              csv_text(ALIPAY_HEADER, [ALIPAY_ROWS[0], ALIPAY_ROWS[1][:3], ALIPAY_ROWS[1]], 24))
    write_csv(out_a / "alipay_garbled.csv",
              csv_text(ALIPAY_HEADER, ALIPAY_ROWS[:4], 24), garbled=True)

    # 微信 xlsx
    write_xlsx(out_w / "wechat_normal.xlsx", WECHAT_ROWS, 18, WECHAT_HEADER)
    write_xlsx(out_w / "wechat_empty_rows.xlsx",
               [WECHAT_ROWS[0], WECHAT_ROWS[1]], 18, WECHAT_HEADER, blank_at={1})
    write_xlsx(out_w / "wechat_missing_cols.xlsx",
               [WECHAT_ROWS[0], WECHAT_ROWS[1], WECHAT_ROWS[2]], 18, WECHAT_HEADER,
               missing_at={1})

    # 微信旧版 CSV（含乱码），验证编码层对微信 CSV 同样适用
    write_csv(out_w / "wechat_garbled.csv",
              csv_text(WECHAT_HEADER, WECHAT_ROWS[:4], 16), garbled=True)

    for p in sorted(FIX.rglob("*")):
        if p.is_file():
            print("written:", p.relative_to(FIX))


if __name__ == "__main__":
    main()
