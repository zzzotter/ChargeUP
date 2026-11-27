/** 展示字典：文案、配色与分类清单（不含数据） */
import type { Category, TxSource, TxStatus } from "@/lib/api/types";

export const SOURCE_LABEL: Record<TxSource, string> = {
  ALIPAY: "支付宝",
  WECHAT: "微信",
  SCREENSHOT: "截图",
  MANUAL: "手动",
};

export const STATUS_META: Record<TxStatus, { label: string; tone: "default" | "warn" | "mint" }> = {
  classified: { label: "已分类", tone: "default" },
  uncategorized: { label: "待归类", tone: "warn" },
  refund: { label: "退款关联", tone: "mint" },
  duplicate: { label: "疑似重复", tone: "warn" },
};

export const CATEGORIES: Category[] = [
  { id: "food", name: "餐饮", tone: "coral" },
  { id: "transport", name: "交通", tone: "mint" },
  { id: "shopping", name: "购物", tone: "lilac" },
  { id: "home", name: "居住", tone: "clay" },
  { id: "fun", name: "娱乐", tone: "default" },
];

export function categoryName(id: string | null): string | null {
  if (!id) return null;
  return CATEGORIES.find((item) => item.id === id)?.name ?? null;
}

/** 本地演示的「今天」，第 5 天之后由服务端时钟决定 */
export const DEMO_TODAY = "2026-11-26";
export const CURRENT_MONTH = "2026-11";
