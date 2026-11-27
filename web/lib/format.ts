const cny = new Intl.NumberFormat("zh-CN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** 分 → 「¥1,234.50」。只用于展示，禁止回写计算（§7.6） */
export function formatCents(cents: number): string {
  return `¥${cny.format(cents / 100)}`;
}

/** 「24.50」→ 2450（字符串拆分、整数运算，避免浮点误差） */
export function parseYuanToCents(input: string): number | null {
  const trimmed = input.trim();
  if (!/^\d{1,9}(\.\d{1,2})?$/.test(trimmed)) return null;
  const [yuan, fraction = ""] = trimmed.split(".");
  return Number(yuan) * 100 + Number((fraction + "00").slice(0, 2));
}

/** 2026-11-24T18:20:11+08:00 → 11-24 18:20 */
export function formatTxTime(iso: string): string {
  return iso.slice(5, 16).replace("T", " ");
}

/** 2026-11-26 → 11-26 */
export function formatShortDate(date: string): string {
  return date.slice(5);
}

/** 2026-11-24T18:20:11+08:00 → { date: "2026-11-24", time: "18:20" } */
export function splitOccurredAt(iso: string): { date: string; time: string } {
  return { date: iso.slice(0, 10), time: iso.slice(11, 16) };
}

/** { date, time } → 2026-11-24T18:20:00+08:00（提交给后端） */
export function joinOccurredAt(date: string, time: string): string {
  return `${date}T${time || "12:00"}:00+08:00`;
}
