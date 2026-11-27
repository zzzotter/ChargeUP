/**
 * 前后端共享的数据契约（对应设计基线 §7.3 / §7.4）
 * 后端 FastAPI 的响应结构需要与此一致，字段名为 lowerCamelCase。
 */

export type TxSource = "ALIPAY" | "WECHAT" | "SCREENSHOT" | "MANUAL";
export type TxDirection = "EXPENSE" | "INCOME" | "TRANSFER";
export type TxStatus = "classified" | "uncategorized" | "refund" | "duplicate";
export type CategoryTone = "coral" | "mint" | "lilac" | "clay" | "default";
export type CategoryType = "EXPENSE" | "INCOME";
/** 规则来源：用户规则优先于内置词库（§F-P0-04） */
export type RuleSource = "USER" | "BUILTIN";
export type MatchedBy = "RULE" | "BUILTIN" | null;

export type Category = {
  id: string;
  name: string;
  tone: CategoryTone;
};

/** GET /categories 的返回项 */
export type CategoryWithCount = {
  id: string;
  name: string;
  type: CategoryType;
  tone: CategoryTone;
  isBuiltin: boolean;
  ruleCount: number;
  transactionCount: number;
};

export type CategoryRule = {
  id: string;
  keyword: string;
  categoryId: string;
  source: RuleSource;
};

export type Transaction = {
  id: string;
  /** ISO 8601 带时区，如 2026-11-24T18:20:11+08:00 */
  occurredAt: string;
  merchant: string;
  /** null 表示未分类（进收件箱） */
  categoryId: string | null;
  source: TxSource;
  /** 整数「分」，非负；方向由 direction 决定 */
  amount: number;
  direction: TxDirection;
  status: TxStatus;
  note?: string;
  /** 退款行指向被退的原始交易（金额相反、7 天内） */
  refundOfTransactionId?: string | null;
  /** 软删除标记；有值即视为已移入回收 */
  deletedAt?: string | null;
  /** 最近一次编辑时间 */
  updatedAt?: string | null;
};

/** 编辑交易时允许修改的字段（来源、external_id、方向为转账时不可改） */
export type TransactionPatch = {
  merchant?: string;
  amount?: number;
  categoryId?: string | null;
  occurredAt?: string;
  note?: string | null;
  direction?: "EXPENSE" | "INCOME";
};

/** 账本筛选条件，直接映射到 URL 查询参数 */
export type LedgerFilters = {
  /** "YYYY-MM"；空字符串表示不限月份 */
  month: string;
  source: TxSource | "ALL";
  /** "ALL" | 分类 id | "NONE"（未分类） */
  categoryId: string | "ALL" | "NONE";
  keyword: string;
  /** 方向筛选；TRANSFER 单列，默认不参与支出统计 */
  direction: TxDirection | "ALL";
};

export type TxQuery = LedgerFilters & { page: number; pageSize: number };

export type Page<T> = {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
};

export type TxPage = Page<Transaction>;

export type MonthSummary = {
  totalExpense: number;
  totalIncome: number;
  uncategorized: number;
  duplicate: number;
  /** 统计时被剔除的转账笔数与退款笔数（§F-P0-03） */
  excludedTransferCount: number;
  excludedRefundCount: number;
};

export type NewTransactionInput = {
  merchant: string;
  amount: number;
  direction: "EXPENSE" | "INCOME";
  occurredAt: string;
  categoryId: string | null;
  note?: string | null;
};

export type CategorySuggestion = {
  categoryId: string | null;
  matchedBy: MatchedBy;
  keyword: string | null;
};

/** POST /category-rules/test 的返回（干跑，不写库） */
export type RuleTestResult = CategorySuggestion & {
  categoryName: string | null;
  /** 命中规则来源，便于说明「用户规则优先」 */
  source: RuleSource | null;
};

export type InboxResult = {
  items: Transaction[];
  total: number;
};

/** GET /stats/monthly —— 趋势图数据 */
export type TrendPoint = {
  /** "YYYY-MM" */
  month: string;
  expense: number;
};

/** GET /stats/categories —— 分类支出分布（已剔除转账、扣回退款） */
export type CategorySlice = {
  categoryId: string | null;
  name: string;
  amount: number;
  /** 0..1，前端自行格式化为百分比 */
  ratio: number;
};

/** 月度预算与双阈值（阈值是比例，0.8 = 80%） */
export type Budget = {
  amount: number;
  warnThreshold: number;
  alertThreshold: number;
};

export type AlertLevel = "WARN" | "ALERT";

/** 跨阈值事件：同一 period + level 只允许一条（§F-P0-06） */
export type AlertEvent = {
  id: string;
  level: AlertLevel;
  /** "YYYY-MM" */
  period: string;
  /** 触发时的阈值比例，如 0.8 */
  threshold: number;
  /** 触发时的支出（分） */
  actual: number;
  /** 触发时的预算（分） */
  budget: number;
  createdAt: string;
  read: boolean;
};

export type BatchClassifyInput = {
  ids: string[];
  categoryId: string;
  /** 同时为该商户沉淀一条用户规则 */
  createRule?: { keyword: string };
};

export type BatchClassifyResult = {
  updated: number;
  rule: CategoryRule | null;
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Array<{ field: string; reason: string }>;
};
