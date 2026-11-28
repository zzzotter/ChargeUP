/**
 * 开发桩的服务端存储（仅被 app/api/dev/* 引用）
 * 后端 FastAPI 就绪后，整块删除。
 */
import type {
  AlertEvent,
  AlertLevel,
  BatchClassifyInput,
  BatchClassifyResult,
  Budget,
  CategoryRule,
  CategorySlice,
  CategoryTone,
  CategoryType,
  CategoryWithCount,
  CsvPreview,
  ImportCommitRow,
  ImportRecord,
  ImportResult,
  ImportSource,
  InboxResult,
  LedgerFilters,
  MonthSummary,
  NewTransactionInput,
  Page,
  RuleTestResult,
  Transaction,
  TransactionPatch,
  TrendPoint,
  TxPage,
  TxQuery,
} from "@/lib/api/types";
import { SEED_TRANSACTIONS } from "@/lib/fixtures";

export class StoreError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details?: Array<{ field: string; reason: string }>,
  ) {
    super(message);
    this.name = "StoreError";
  }
}

/** 进程内「数据库」：重启服务即回到种子数据 */
const DB: Transaction[] = [...SEED_TRANSACTIONS];

type CategoryRecord = {
  id: string;
  name: string;
  type: CategoryType;
  tone: CategoryTone;
  isBuiltin: boolean;
};

const CATEGORIES: CategoryRecord[] = [
  { id: "food", name: "餐饮", type: "EXPENSE", tone: "coral", isBuiltin: true },
  { id: "transport", name: "交通", type: "EXPENSE", tone: "mint", isBuiltin: true },
  { id: "shopping", name: "购物", type: "EXPENSE", tone: "lilac", isBuiltin: true },
  { id: "home", name: "居住", type: "EXPENSE", tone: "default", isBuiltin: true },
  { id: "fun", name: "娱乐", type: "EXPENSE", tone: "default", isBuiltin: true },
  { id: "salary", name: "工资", type: "INCOME", tone: "mint", isBuiltin: true },
];

type RuleRecord = {
  id: string;
  keyword: string;
  categoryId: string;
  source: "USER" | "BUILTIN";
};

/** 内置词库；用户规则优先于它（§F-P0-04） */
const RULES: RuleRecord[] = [
  { id: "r1", keyword: "星巴克", categoryId: "food", source: "BUILTIN" },
  { id: "r2", keyword: "瑞幸", categoryId: "food", source: "BUILTIN" },
  { id: "r3", keyword: "外卖", categoryId: "food", source: "BUILTIN" },
  { id: "r4", keyword: "盒马", categoryId: "food", source: "BUILTIN" },
  { id: "r5", keyword: "滴滴", categoryId: "transport", source: "BUILTIN" },
  { id: "r6", keyword: "地铁", categoryId: "transport", source: "BUILTIN" },
  { id: "r7", keyword: "优衣库", categoryId: "shopping", source: "BUILTIN" },
  { id: "r8", keyword: "京东", categoryId: "shopping", source: "BUILTIN" },
  { id: "r9", keyword: "房租", categoryId: "home", source: "BUILTIN" },
  { id: "r10", keyword: "工资", categoryId: "salary", source: "BUILTIN" },
];

/** 调试用：让下一次「列表」请求返回 500，便于验证前端错误态 */
let armedFailures = 0;

export function armFailure() {
  armedFailures += 1;
}

export function consumeFailure(): boolean {
  if (armedFailures <= 0) return false;
  armedFailures -= 1;
  return true;
}

const TONES: CategoryTone[] = ["coral", "mint", "lilac", "default"];

function orderedRules(): RuleRecord[] {
  const user = RULES.filter((rule) => rule.source === "USER");
  const builtin = RULES.filter((rule) => rule.source === "BUILTIN");
  return [...user, ...builtin];
}

function categoryOf(id: string | null): CategoryRecord | undefined {
  return id ? CATEGORIES.find((item) => item.id === id) : undefined;
}

function assertCategory(id: string): CategoryRecord {
  const found = categoryOf(id);
  if (!found) throw new StoreError(404, "NOT_FOUND", "分类不存在");
  return found;
}

function toCategoryWithCount(record: CategoryRecord): CategoryWithCount {
  return {
    id: record.id,
    name: record.name,
    type: record.type,
    tone: record.tone,
    isBuiltin: record.isBuiltin,
    ruleCount: RULES.filter((rule) => rule.categoryId === record.id).length,
    transactionCount: DB.filter((tx) => tx.categoryId === record.id && !tx.deletedAt).length,
  };
}

/* ------------------------------------------------------------------ 交易 */

function matches(tx: Transaction, filters: LedgerFilters) {
  const keyword = filters.keyword.trim().toLowerCase();
  const direction = filters.direction ?? "ALL";
  if (tx.deletedAt) return false;
  if (filters.month && !tx.occurredAt.startsWith(filters.month)) return false;
  if (filters.source !== "ALL" && tx.source !== filters.source) return false;
  if (direction !== "ALL" && tx.direction !== direction) return false;
  if (filters.categoryId === "NONE" && tx.categoryId !== null) return false;
  if (filters.categoryId !== "ALL" && filters.categoryId !== "NONE" && tx.categoryId !== filters.categoryId)
    return false;
  if (keyword && !tx.merchant.toLowerCase().includes(keyword)) return false;
  return true;
}

export function queryTransactions(query: TxQuery): TxPage {
  const filtered = DB.filter((tx) => matches(tx, query)).sort((a, b) =>
    b.occurredAt.localeCompare(a.occurredAt),
  );

  const total = filtered.length;
  const lastPage = Math.max(1, Math.ceil(total / query.pageSize));
  const page = Math.min(Math.max(1, query.page), lastPage);
  const start = (page - 1) * query.pageSize;

  return {
    items: filtered.slice(start, start + query.pageSize),
    page,
    pageSize: query.pageSize,
    total,
  };
}

/**
 * 某月支出的统一口径：只算 EXPENSE，剔除转账，扣回已关联的退款（§F-P0-03）。
 * 趋势图、分类分布、本月概览都复用它，保证三处数字一致。
 */
function monthExpense(month: string): number {
  return DB.filter((tx) => !tx.deletedAt && tx.occurredAt.startsWith(month)).reduce((sum, tx) => {
    if (tx.direction === "EXPENSE") return sum + tx.amount;
    if (tx.direction === "INCOME" && tx.refundOfTransactionId) {
      const original = DB.find((item) => item.id === tx.refundOfTransactionId && !item.deletedAt);
      if (original) return sum - tx.amount;
    }
    return sum;
  }, 0);
}

function monthKeys(endMonth: string, count: number): string[] {
  const [year, month] = endMonth.split("-").map(Number);
  const keys: string[] = [];
  for (let index = count - 1; index >= 0; index -= 1) {
    const date = new Date(Date.UTC(year, month - 1 - index, 1));
    keys.push(`${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`);
  }
  return keys;
}

export function summarizeMonth(month: string): MonthSummary {
  // 事件是「读到时懒评估」的：后端就绪后应改为在写入路径触发
  if (month) evaluateBudget(month);
  const rows = DB.filter((tx) => !tx.deletedAt && (!month || tx.occurredAt.startsWith(month)));
  const summary = rows.reduce<Omit<MonthSummary, "totalExpense" | "excludedTransferCount" | "excludedRefundCount">>(
    (acc, tx) => {
      if (tx.direction === "INCOME") {
        const original = tx.refundOfTransactionId
          ? DB.find((item) => item.id === tx.refundOfTransactionId && !item.deletedAt)
          : undefined;
        if (!original) acc.totalIncome += tx.amount;
      }
      if (tx.categoryId === null && tx.direction !== "TRANSFER") acc.uncategorized += 1;
      if (tx.status === "duplicate") acc.duplicate += 1;
      return acc;
    },
    { totalIncome: 0, uncategorized: 0, duplicate: 0 },
  );

  return {
    ...summary,
    totalExpense: monthExpense(month),
    excludedTransferCount: rows.filter((tx) => tx.direction === "TRANSFER").length,
    excludedRefundCount: rows.filter((tx) => {
      if (tx.direction !== "INCOME" || !tx.refundOfTransactionId) return false;
      return DB.some((item) => item.id === tx.refundOfTransactionId && !item.deletedAt);
    }).length,
  };
}

export function monthlyTrend(month: string, months: number): TrendPoint[] {  const end = month || new Date().toISOString().slice(0, 7);
  return monthKeys(end, Math.min(Math.max(months, 1), 12)).map((key) => ({
    month: key,
    expense: monthExpense(key),
  }));
}

export function categoryBreakdown(month: string): CategorySlice[] {
  const totals = new Map<string | null, number>();

  for (const tx of DB) {
    if (tx.deletedAt) continue;
    if (month && !tx.occurredAt.startsWith(month)) continue;

    if (tx.direction === "EXPENSE") {
      totals.set(tx.categoryId, (totals.get(tx.categoryId) ?? 0) + tx.amount);
    } else if (tx.direction === "INCOME" && tx.refundOfTransactionId) {
      const original = DB.find((item) => item.id === tx.refundOfTransactionId && !item.deletedAt);
      if (original) {
        totals.set(original.categoryId, (totals.get(original.categoryId) ?? 0) - tx.amount);
      }
    }
  }

  const rows = [...totals.entries()]
    .filter(([, amount]) => amount > 0)
    .map(([categoryId, amount]) => ({
      categoryId,
      name: categoryOf(categoryId)?.name ?? "未分类",
      amount,
    }))
    .sort((a, b) => b.amount - a.amount);

  const total = rows.reduce((sum, row) => sum + row.amount, 0);
  return rows.map((row) => ({ ...row, ratio: total > 0 ? row.amount / total : 0 }));
}

export function insertTransaction(input: NewTransactionInput): Transaction {
  const created: Transaction = {
    id: `m${Date.now()}`,
    occurredAt: input.occurredAt,
    merchant: input.merchant.trim(),
    categoryId: input.categoryId,
    source: "MANUAL",
    amount: input.amount,
    direction: input.direction,
    status: input.categoryId ? "classified" : "uncategorized",
    note: input.note?.trim() ? input.note.trim() : undefined,
    externalId: null,
    refundOfTransactionId: null,
    deletedAt: null,
    updatedAt: null,
  };
  DB.unshift(created);
  return created;
}

/* ------------------------------------------------------- 单条交易：查/改/软删 */

export function getTransaction(id: string): Transaction {
  const tx = DB.find((item) => item.id === id && !item.deletedAt);
  if (!tx) throw new StoreError(404, "NOT_FOUND", "记录不存在或已移入回收");
  return tx;
}

const ISO_WITH_TZ = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)$/;

export function updateTransaction(id: string, patch: TransactionPatch): Transaction {
  const tx = getTransaction(id);
  const details: Array<{ field: string; reason: string }> = [];

  if (patch.merchant !== undefined) {
    if (!patch.merchant.trim()) details.push({ field: "merchant", reason: "不能为空" });
    else if (patch.merchant.trim().length > 60) details.push({ field: "merchant", reason: "不能超过 60 字" });
  }
  if (patch.amount !== undefined) {
    if (!Number.isInteger(patch.amount) || patch.amount <= 0)
      details.push({ field: "amount", reason: "必须是大于 0 的整数「分」" });
  }
  if (patch.occurredAt !== undefined && !ISO_WITH_TZ.test(patch.occurredAt)) {
    details.push({ field: "occurredAt", reason: "需为带时区的 ISO 8601 时间" });
  }
  if (patch.categoryId !== undefined && patch.categoryId !== null) {
    if (!CATEGORIES.some((item) => item.id === patch.categoryId)) {
      details.push({ field: "categoryId", reason: "分类不存在" });
    }
  }
  if (patch.note !== undefined && patch.note !== null && patch.note.length > 200) {
    details.push({ field: "note", reason: "备注不能超过 200 字" });
  }
  if (patch.direction !== undefined && tx.direction === "TRANSFER") {
    details.push({ field: "direction", reason: "转账记录的方向不可修改" });
  }

  if (details.length > 0) {
    throw new StoreError(422, "VALIDATION_ERROR", "字段校验失败", details);
  }

  if (patch.merchant !== undefined) tx.merchant = patch.merchant.trim();
  if (patch.amount !== undefined) tx.amount = patch.amount;
  if (patch.occurredAt !== undefined) tx.occurredAt = patch.occurredAt;
  if (patch.note !== undefined) tx.note = patch.note?.trim() ? patch.note.trim() : undefined;
  if (patch.direction !== undefined && tx.direction !== "TRANSFER") tx.direction = patch.direction;
  if (patch.categoryId !== undefined) {
    tx.categoryId = patch.categoryId;
    tx.status = patch.categoryId ? "classified" : "uncategorized";
  }

  tx.updatedAt = new Date().toISOString();
  return tx;
}

/** 软删除：只写 deletedAt，DELETE 硬删由后端拦截（§5.2） */
export function softDeleteTransaction(id: string): void {
  const tx = getTransaction(id);
  tx.deletedAt = new Date().toISOString();
  tx.updatedAt = tx.deletedAt;
}

/* ------------------------------------------------------------------ 分类 */

export function listCategories(type?: CategoryType | null): CategoryWithCount[] {
  return CATEGORIES.filter((item) => (type ? item.type === type : true)).map(toCategoryWithCount);
}

export function createCategory(input: { name: string; type: CategoryType }): CategoryWithCount {
  const name = input.name.trim();
  if (!name) throw new StoreError(422, "VALIDATION_ERROR", "分类名称不能为空");
  if (name.length > 12) throw new StoreError(422, "VALIDATION_ERROR", "分类名称不能超过 12 字");
  if (input.type !== "EXPENSE" && input.type !== "INCOME")
    throw new StoreError(422, "VALIDATION_ERROR", "type 必须是 EXPENSE 或 INCOME");
  if (CATEGORIES.some((item) => item.type === input.type && item.name === name))
    throw new StoreError(409, "DUPLICATE_RESOURCE", "同类型下已存在同名分类");

  const record: CategoryRecord = {
    id: `c${Date.now()}`,
    name,
    type: input.type,
    tone: TONES[CATEGORIES.length % TONES.length],
    isBuiltin: false,
  };
  CATEGORIES.push(record);
  return toCategoryWithCount(record);
}

export function renameCategory(id: string, name: string): CategoryWithCount {
  const record = assertCategory(id);
  const next = name.trim();
  if (!next) throw new StoreError(422, "VALIDATION_ERROR", "分类名称不能为空");
  if (next.length > 12) throw new StoreError(422, "VALIDATION_ERROR", "分类名称不能超过 12 字");
  if (CATEGORIES.some((item) => item.type === record.type && item.id !== id && item.name === next))
    throw new StoreError(409, "DUPLICATE_RESOURCE", "同类型下已存在同名分类");

  record.name = next;
  return toCategoryWithCount(record);
}

export function deleteCategory(id: string): void {
  const record = assertCategory(id);
  if (record.isBuiltin) throw new StoreError(409, "CATEGORY_IS_BUILTIN", "内置分类不可删除");
  const used = DB.some((tx) => tx.categoryId === id && !tx.deletedAt);
  if (used) throw new StoreError(409, "CATEGORY_IN_USE", "该分类下仍有交易，请先迁移或改为其他分类");

  for (let index = RULES.length - 1; index >= 0; index -= 1) {
    if (RULES[index].categoryId === id) RULES.splice(index, 1);
  }
  CATEGORIES.splice(CATEGORIES.indexOf(record), 1);
}

/* ------------------------------------------------------------------ 规则 */

export function listRules(): CategoryRule[] {
  return orderedRules().map((rule) => ({ ...rule }));
}

export function createRule(input: { keyword: string; categoryId: string }): CategoryRule {
  const keyword = input.keyword.trim();
  if (!keyword) throw new StoreError(422, "VALIDATION_ERROR", "关键词不能为空");
  if (keyword.length > 20) throw new StoreError(422, "VALIDATION_ERROR", "关键词不能超过 20 字");
  assertCategory(input.categoryId);
  if (RULES.some((rule) => rule.keyword.toLowerCase() === keyword.toLowerCase()))
    throw new StoreError(409, "DUPLICATE_RESOURCE", "该关键词已存在规则");

  const rule: RuleRecord = {
    id: `r${Date.now()}`,
    keyword,
    categoryId: input.categoryId,
    source: "USER",
  };
  RULES.unshift(rule);
  return { ...rule };
}

export function deleteRule(id: string): void {
  const record = RULES.find((rule) => rule.id === id);
  if (!record) throw new StoreError(404, "NOT_FOUND", "规则不存在");
  if (record.source === "BUILTIN") throw new StoreError(409, "RULE_IS_BUILTIN", "内置词库规则不可删除");
  RULES.splice(RULES.indexOf(record), 1);
}

/** 干跑：返回命中的规则与分类，不写库 */
export function testRule(name: string): RuleTestResult {
  const hit = orderedRules().find((rule) => name.includes(rule.keyword));
  if (!hit) return { categoryId: null, matchedBy: null, keyword: null, categoryName: null, source: null };
  return {
    categoryId: hit.categoryId,
    matchedBy: hit.source === "USER" ? "RULE" : "BUILTIN",
    keyword: hit.keyword,
    categoryName: categoryOf(hit.categoryId)?.name ?? null,
    source: hit.source,
  };
}

/* ------------------------------------------------------------------ 预算与预警 */

const DEFAULT_BUDGET: Budget = { amount: 420000, warnThreshold: 0.8, alertThreshold: 1 };
let BUDGET: Budget = { ...DEFAULT_BUDGET };

const ALERTS: AlertEvent[] = [];

export function getBudget(): Budget {
  return { ...BUDGET };
}

export function saveBudget(input: Partial<Budget>): Budget {
  const next: Budget = {
    amount: input.amount ?? BUDGET.amount,
    warnThreshold: input.warnThreshold ?? BUDGET.warnThreshold,
    alertThreshold: input.alertThreshold ?? BUDGET.alertThreshold,
  };

  const details: Array<{ field: string; reason: string }> = [];
  if (!Number.isInteger(next.amount) || next.amount <= 0) {
    details.push({ field: "amount", reason: "预算需为大于 0 的整数「分」" });
  }
  if (!(next.warnThreshold > 0) || next.warnThreshold >= 5) {
    details.push({ field: "warnThreshold", reason: "预警线需在 1%–500% 之间" });
  }
  if (!(next.alertThreshold > next.warnThreshold)) {
    details.push({ field: "alertThreshold", reason: "告警线必须高于预警线" });
  } else if (next.alertThreshold > 5) {
    details.push({ field: "alertThreshold", reason: "告警线不能超过 500%" });
  }
  if (details.length > 0) {
    throw new StoreError(422, "VALIDATION_ERROR", "字段校验失败", details);
  }

  BUDGET = next;
  return { ...BUDGET };
}

/** 跨阈值就生成事件；同一 period + level 只生成一条（§F-P0-06） */
function evaluateBudget(month: string) {
  if (!month || BUDGET.amount <= 0) return;

  const spent = monthExpense(month);
  const ratio = spent / BUDGET.amount;
  const levels: Array<{ level: AlertLevel; threshold: number }> = [
    { level: "WARN", threshold: BUDGET.warnThreshold },
    { level: "ALERT", threshold: BUDGET.alertThreshold },
  ];

  for (const { level, threshold } of levels) {
    if (ratio < threshold) continue;
    if (ALERTS.some((item) => item.period === month && item.level === level)) continue;
    ALERTS.unshift({
      id: `a${Date.now()}${level}`,
      level,
      period: month,
      threshold,
      actual: spent,
      budget: BUDGET.amount,
      createdAt: new Date().toISOString(),
      read: false,
    });
  }
}

export function listAlerts(query: { month?: string; page: number; pageSize: number }): Page<AlertEvent> {
  const filtered = ALERTS.filter((item) => (query.month ? item.period === query.month : true)).sort(
    (a, b) => b.createdAt.localeCompare(a.createdAt),
  );
  const total = filtered.length;
  const lastPage = Math.max(1, Math.ceil(total / query.pageSize));
  const page = Math.min(Math.max(1, query.page), lastPage);
  const start = (page - 1) * query.pageSize;

  return { items: filtered.slice(start, start + query.pageSize), page, pageSize: query.pageSize, total };
}

export function markAlertRead(id: string): AlertEvent {
  const event = ALERTS.find((item) => item.id === id);
  if (!event) throw new StoreError(404, "NOT_FOUND", "预警事件不存在");
  event.read = true;
  return event;
}

/* ------------------------------------------------------------------ 收件箱 */

export function listInbox(): InboxResult {
  const items = DB.filter(
    // 转账没有消费分类，不进收件箱
    (tx) => tx.categoryId === null && tx.direction !== "TRANSFER" && !tx.deletedAt,
  ).sort((a, b) => b.occurredAt.localeCompare(a.occurredAt));
  return { items, total: items.length };
}

export function batchClassify(input: BatchClassifyInput): BatchClassifyResult {
  const category = assertCategory(input.categoryId);
  if (!Array.isArray(input.ids) || input.ids.length === 0)
    throw new StoreError(422, "VALIDATION_ERROR", "ids 不能为空");

  let updated = 0;
  for (const id of input.ids) {
    const tx = DB.find((item) => item.id === id && !item.deletedAt);
    if (!tx) continue;
    tx.categoryId = category.id;
    tx.status = "classified";
    tx.updatedAt = new Date().toISOString();
    updated += 1;
  }

  let rule: CategoryRule | null = null;
  const keyword = input.createRule?.keyword.trim();
  if (keyword) {
    const existing = RULES.find((item) => item.keyword.toLowerCase() === keyword.toLowerCase());
    if (existing) {
      existing.categoryId = category.id;
      existing.source = "USER";
      rule = { ...existing };
    } else {
      rule = createRule({ keyword, categoryId: category.id });
    }
  }

  return { updated, rule };
}

/** 分类建议：用户规则优先于内置词库 */
export function suggestFor(merchant: string): RuleTestResult {
  return testRule(merchant);
}

/* ------------------------------------------------------------------ 账单导入（CSV） */

const IMPORTS: ImportRecord[] = [];

function hasExternal(source: ImportSource, externalId: string | null | undefined): boolean {
  if (!externalId) return false;
  return DB.some((tx) => !tx.deletedAt && tx.source === source && tx.externalId === externalId);
}

/** 幂等去重：库内已存在（来源 + 交易单号）或本文件内重复 → 标记为 duplicate */
export function annotateCsvPreview(preview: CsvPreview): CsvPreview {
  const seen = new Set<string>();

  const rows = preview.rows.map((row) => {
    if (row.status === "failed" || !row.externalId) return row;
    const key = `${preview.source ?? "UNKNOWN"}:${row.externalId}`;

    if (preview.source && hasExternal(preview.source, row.externalId)) {
      return { ...row, status: "duplicate" as const, reason: "库中已存在（来源 + 交易单号）" };
    }
    if (seen.has(key)) {
      return { ...row, status: "duplicate" as const, reason: "与本文件前面的行单号重复" };
    }
    seen.add(key);
    return row;
  });

  return {
    ...preview,
    rows,
    newCount: rows.filter((row) => row.status === "new").length,
    duplicated: rows.filter((row) => row.status === "duplicate").length,
    failed: rows.filter((row) => row.status === "failed").length,
  };
}

/** 退款自动关联：金额相同、7 天内、商户名含「退款」的收入行（§F-P0-03） */
function linkRefunds(created: Transaction[]) {
  for (const tx of created) {
    if (tx.direction !== "INCOME" || !tx.merchant.includes("退款")) continue;
    const target = DB.find(
      (other) =>
        other.id !== tx.id &&
        other.direction === "EXPENSE" &&
        other.amount === tx.amount &&
        !other.refundOfTransactionId &&
        !other.deletedAt &&
        // 已被其他退款关联过的原始交易不再重复关联
        !DB.some((refund) => refund.refundOfTransactionId === other.id && !refund.deletedAt) &&
        Math.abs(Date.parse(other.occurredAt) - Date.parse(tx.occurredAt)) <= 7 * 24 * 60 * 60 * 1000,
    );
    if (target) tx.refundOfTransactionId = target.id;
  }
}

/** 确认入账：只写 new 行，命中规则的自动分类，未命中进收件箱 */
export function commitCsvImport(input: {
  fileName: string;
  source: ImportSource;
  rows: ImportCommitRow[];
  failed?: number;
  /** 预览阶段已判定为重复的行数，合并进导入记录 */
  duplicated?: number;
}): ImportResult {
  if (!input.fileName) throw new StoreError(422, "VALIDATION_ERROR", "缺少文件名");
  if (input.source !== "ALIPAY" && input.source !== "WECHAT") {
    throw new StoreError(422, "VALIDATION_ERROR", "来源必须是 ALIPAY 或 WECHAT");
  }
  if (!Array.isArray(input.rows)) {
    throw new StoreError(422, "VALIDATION_ERROR", "rows 必须是数组");
  }

  const created: Transaction[] = [];
  let duplicated = input.duplicated ?? 0;
  const base = Date.now();

  input.rows.forEach((row, index) => {
    if (hasExternal(input.source, row.externalId)) {
      duplicated += 1;
      return;
    }
    const suggestion = testRule(row.merchant);
    const tx: Transaction = {
      id: `i${base}-${index}`,
      occurredAt: row.occurredAt,
      merchant: row.merchant,
      categoryId: suggestion.categoryId,
      source: input.source,
      amount: row.amount,
      direction: row.direction,
      status: suggestion.categoryId ? "classified" : "uncategorized",
      note: row.note ?? undefined,
      externalId: row.externalId,
      refundOfTransactionId: null,
      deletedAt: null,
      updatedAt: null,
    };
    DB.push(tx);
    created.push(tx);
  });

  linkRefunds(created);

  const record: ImportResult = {
    importId: `imp${base}`,
    fileName: input.fileName,
    source: input.source,
    created: created.length,
    duplicated,
    failed: input.failed ?? 0,
    createdAt: new Date().toISOString(),
  };
  IMPORTS.unshift(record);
  return record;
}

export function listImports(): ImportRecord[] {
  return IMPORTS.slice(0, 20);
}
