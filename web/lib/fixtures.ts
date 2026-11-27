/**
 * 开发桩的种子数据（后端就绪后随 app/api/dev 一起删除）
 * 金额一律为整数「分」。
 */
import type { Transaction, TxDirection, TxSource, TxStatus } from "@/lib/api/types";

/** 手写的 8 条明细，覆盖各种状态 */
const CURATED: Transaction[] = [
  { id: "t1", occurredAt: "2026-11-24T18:20:11+08:00", merchant: "星巴克（国贸店）", categoryId: "food", source: "ALIPAY", amount: 3800, direction: "EXPENSE", status: "classified", note: "加班咖啡" },
  { id: "t2", occurredAt: "2026-11-24T12:05:44+08:00", merchant: "滴滴出行", categoryId: "transport", source: "WECHAT", amount: 2640, direction: "EXPENSE", status: "duplicate" },
  { id: "t3", occurredAt: "2026-11-23T21:10:02+08:00", merchant: "退款 · 退货", categoryId: "food", source: "ALIPAY", amount: 12900, direction: "INCOME", status: "refund" },
  { id: "t4", occurredAt: "2026-11-23T09:32:18+08:00", merchant: "未识别商户 8821", categoryId: null, source: "SCREENSHOT", amount: 19800, direction: "EXPENSE", status: "uncategorized" },
  { id: "t5", occurredAt: "2026-11-22T20:14:31+08:00", merchant: "优衣库", categoryId: "shopping", source: "WECHAT", amount: 29900, direction: "EXPENSE", status: "classified" },
  { id: "t6", occurredAt: "2026-11-22T08:45:03+08:00", merchant: "地铁通勤", categoryId: "transport", source: "ALIPAY", amount: 600, direction: "EXPENSE", status: "classified" },
  { id: "t7", occurredAt: "2026-11-21T19:02:47+08:00", merchant: "未识别商户 4471", categoryId: null, source: "MANUAL", amount: 5200, direction: "EXPENSE", status: "uncategorized" },
  { id: "t8", occurredAt: "2026-11-21T13:26:09+08:00", merchant: "美团外卖", categoryId: "food", source: "WECHAT", amount: 4280, direction: "EXPENSE", status: "classified" },
  // 转账：计入流水但不参与支出统计（§F-P0-03）
  { id: "t9", occurredAt: "2026-11-16T09:10:00+08:00", merchant: "转账 · 还信用卡", categoryId: "home", source: "ALIPAY", amount: 300000, direction: "TRANSFER", status: "classified" },
  { id: "t10", occurredAt: "2026-11-25T22:05:00+08:00", merchant: "转账 · 余额宝", categoryId: "home", source: "WECHAT", amount: 100000, direction: "TRANSFER", status: "classified" },
];

/** 批量生成的明细：让筛选与分页有足够数据（11 月 18 条 + 10 月 6 条） */
const SEEDS: Array<[string, string | null, TxSource, number, TxDirection, TxStatus, string]> = [
  ["瑞幸咖啡", "food", "WECHAT", 1990, "EXPENSE", "classified", "2026-11-20T09:12:00+08:00"],
  ["盒马鲜生", "food", "ALIPAY", 13640, "EXPENSE", "classified", "2026-11-19T18:41:00+08:00"],
  ["房租 · 11 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-11-19T09:05:00+08:00"],
  ["网易云音乐", "fun", "ALIPAY", 1500, "EXPENSE", "classified", "2026-11-18T18:48:00+08:00"],
  ["京东 · 家居", "shopping", "ALIPAY", 15800, "EXPENSE", "classified", "2026-11-17T21:40:00+08:00"],
  ["未识别商户 1029", null, "ALIPAY", 8600, "EXPENSE", "uncategorized", "2026-11-17T12:03:00+08:00"],
  ["地铁通勤", "transport", "ALIPAY", 600, "EXPENSE", "classified", "2026-11-16T08:40:00+08:00"],
  ["工资", "home", "MANUAL", 1800000, "INCOME", "classified", "2026-11-15T10:00:00+08:00"],
  ["便利店 6672", null, "WECHAT", 2450, "EXPENSE", "uncategorized", "2026-11-15T08:12:00+08:00"],
  ["滴滴出行", "transport", "WECHAT", 3120, "EXPENSE", "classified", "2026-11-14T22:31:00+08:00"],
  ["星巴克（望京店）", "food", "ALIPAY", 4200, "EXPENSE", "classified", "2026-11-13T15:22:00+08:00"],
  ["电影票 · 两张", "fun", "WECHAT", 9800, "EXPENSE", "classified", "2026-11-12T19:10:00+08:00"],
  ["未识别商户 8821", null, "SCREENSHOT", 19800, "EXPENSE", "duplicate", "2026-11-11T09:32:00+08:00"],
  ["买菜 · 菜市场", "food", "MANUAL", 6750, "EXPENSE", "classified", "2026-11-10T17:26:00+08:00"],
  ["话费充值", "home", "ALIPAY", 5000, "EXPENSE", "classified", "2026-11-09T11:02:00+08:00"],
  ["优衣库", "shopping", "WECHAT", 19900, "EXPENSE", "classified", "2026-11-08T14:35:00+08:00"],
  ["退款 · 京东", "shopping", "ALIPAY", 15800, "INCOME", "refund", "2026-11-19T10:20:00+08:00"],
  ["咖啡 · Manner", "food", "WECHAT", 2200, "EXPENSE", "classified", "2026-11-06T08:55:00+08:00"],
  ["房租 · 10 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-10-19T09:05:00+08:00"],  ["盒马鲜生", "food", "ALIPAY", 9870, "EXPENSE", "classified", "2026-10-18T18:12:00+08:00"],
  ["地铁通勤", "transport", "ALIPAY", 600, "EXPENSE", "classified", "2026-10-17T08:44:00+08:00"],
  ["未识别商户 3310", null, "SCREENSHOT", 4600, "EXPENSE", "uncategorized", "2026-10-15T21:08:00+08:00"],
  ["优衣库", "shopping", "WECHAT", 12900, "EXPENSE", "classified", "2026-10-12T15:40:00+08:00"],
  ["工资", "home", "MANUAL", 1800000, "INCOME", "classified", "2026-10-15T10:00:00+08:00"],
  // 更早 4 个月：让趋势图有 6 根柱子（第 9 天对账样例）
  ["房租 · 6 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-06-19T09:05:00+08:00"],
  ["超市采购", "food", "ALIPAY", 26800, "EXPENSE", "classified", "2026-06-12T18:20:00+08:00"],
  ["房租 · 7 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-07-19T09:05:00+08:00"],
  ["外卖 · 晚餐", "food", "WECHAT", 3850, "EXPENSE", "classified", "2026-07-08T19:40:00+08:00"],
  ["房租 · 8 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-08-19T09:05:00+08:00"],
  ["优衣库", "shopping", "WECHAT", 15900, "EXPENSE", "classified", "2026-08-05T14:10:00+08:00"],
  ["房租 · 9 月", "home", "MANUAL", 220000, "EXPENSE", "classified", "2026-09-19T09:05:00+08:00"],
  ["电影票 · 两张", "fun", "WECHAT", 7600, "EXPENSE", "classified", "2026-09-06T20:00:00+08:00"],
];

const GENERATED: Transaction[] = SEEDS.map(
  ([merchant, categoryId, source, amount, direction, status, occurredAt], index) => ({
    id: `g${index + 1}`,
    occurredAt,
    merchant,
    categoryId,
    source,
    amount,
    direction,
    status,
  }),
);

/** 种子数据：按时间倒序 */
export const SEED_TRANSACTIONS: Transaction[] = [...CURATED, ...GENERATED].sort((a, b) =>
  b.occurredAt.localeCompare(a.occurredAt),
);

/** 退款关联：退款行指向被退的原始交易（金额相反、7 天内，§F-P0-03） */
const REFUND_LINKS: Record<string, string> = {
  g17: "g5", // 退款 · 京东 → 京东 · 家居（同额、隔 2 天）
};

for (const tx of SEED_TRANSACTIONS) {
  if (REFUND_LINKS[tx.id]) tx.refundOfTransactionId = REFUND_LINKS[tx.id];
}
