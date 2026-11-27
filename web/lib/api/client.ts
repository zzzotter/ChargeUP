import type {
  AlertEvent,
  ApiErrorBody,
  BatchClassifyInput,
  BatchClassifyResult,
  Budget,
  CategoryRule,
  CategorySlice,
  CategorySuggestion,
  CategoryType,
  CategoryWithCount,
  InboxResult,
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

/**
 * 唯一的 HTTP 出口（对应设计基线 §7.2）。
 * - 配了 NEXT_PUBLIC_API_BASE 就直连 FastAPI；否则落到同仓的开发桩 /api/dev。
 * - 页面只依赖这里的函数，切换后端不改调用方。
 */
const RAW_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "").trim();
export const API_BASE = RAW_BASE ? RAW_BASE.replace(/\/+$/, "") : "/api/dev";
export const USING_DEV_STUB = RAW_BASE === "";

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: Array<{ field: string; reason: string }>;

  constructor(
    message: string,
    code: string,
    status: number,
    details?: Array<{ field: string; reason: string }>,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const REQUEST_TIMEOUT_MS = 8000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });

    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
      throw new ApiError(
        body?.message ?? `请求失败（HTTP ${response.status}）`,
        body?.code ?? "HTTP_ERROR",
        response.status,
        body?.details,
      );
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("请求超时（8s），请稍后重试", "TIMEOUT", 0);
    }
    throw new ApiError("网络异常，请确认后端已启动", "NETWORK_ERROR", 0);
  } finally {
    clearTimeout(timer);
  }
}

export function listTransactions(query: TxQuery): Promise<TxPage> {
  const params = new URLSearchParams({
    page: String(query.page),
    pageSize: String(query.pageSize),
    source: query.source,
    categoryId: query.categoryId,
  });
  if (query.month) params.set("month", query.month);
  if (query.direction && query.direction !== "ALL") params.set("direction", query.direction);
  if (query.keyword.trim()) params.set("q", query.keyword.trim());

  return request<TxPage>(`/transactions?${params.toString()}`);
}

export function getMonthSummary(month: string): Promise<MonthSummary> {
  const params = new URLSearchParams();
  if (month) params.set("month", month);
  return request<MonthSummary>(`/stats/summary?${params.toString()}`);
}

export function getMonthlyTrend(month: string, months = 6): Promise<TrendPoint[]> {
  const params = new URLSearchParams({ months: String(months) });
  if (month) params.set("month", month);
  return request<TrendPoint[]>(`/stats/monthly?${params.toString()}`);
}

export function getCategoryBreakdown(month: string): Promise<CategorySlice[]> {
  const params = new URLSearchParams();
  if (month) params.set("month", month);
  return request<CategorySlice[]>(`/stats/categories?${params.toString()}`);
}

/* -------------------------------------------------------------- 预算与预警 */

export function getBudget(): Promise<Budget> {
  return request<Budget>("/budget");
}

export function saveBudget(input: Partial<Budget>): Promise<Budget> {
  return request<Budget>("/budget", { method: "PUT", body: JSON.stringify(input) });
}

export function listAlerts(query: { month?: string; page?: number; pageSize?: number } = {}): Promise<
  Page<AlertEvent>
> {
  const params = new URLSearchParams({
    page: String(query.page ?? 1),
    pageSize: String(query.pageSize ?? 20),
  });
  if (query.month) params.set("month", query.month);
  return request<Page<AlertEvent>>(`/alerts?${params.toString()}`);
}

export function markAlertRead(id: string): Promise<AlertEvent> {
  return request<AlertEvent>(`/alerts/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ read: true }),
  });
}

export function suggestCategory(merchant: string): Promise<CategorySuggestion> {
  return request<CategorySuggestion>(`/categories/suggest?name=${encodeURIComponent(merchant)}`);
}

export function createTransaction(input: NewTransactionInput): Promise<Transaction> {
  return request<Transaction>("/transactions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getTransaction(id: string): Promise<Transaction> {
  return request<Transaction>(`/transactions/${id}`);
}

export function updateTransaction(id: string, patch: TransactionPatch): Promise<Transaction> {
  return request<Transaction>(`/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

/** 软删除：后端只写 deleted_at */
export function deleteTransaction(id: string): Promise<void> {
  return request<void>(`/transactions/${id}`, { method: "DELETE" });
}

/* -------------------------------------------------------------- 分类与规则 */

export function listCategories(type?: CategoryType): Promise<CategoryWithCount[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  const query = params.toString();
  return request<CategoryWithCount[]>(`/categories${query ? `?${query}` : ""}`);
}

export function createCategory(input: { name: string; type: CategoryType }): Promise<CategoryWithCount> {
  return request<CategoryWithCount>("/categories", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function renameCategory(id: string, name: string): Promise<CategoryWithCount> {
  return request<CategoryWithCount>(`/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function deleteCategory(id: string): Promise<void> {
  return request<void>(`/categories/${id}`, { method: "DELETE" });
}

export function listRules(): Promise<CategoryRule[]> {
  return request<CategoryRule[]>("/category-rules");
}

export function createRule(input: { keyword: string; categoryId: string }): Promise<CategoryRule> {
  return request<CategoryRule>("/category-rules", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deleteRule(id: string): Promise<void> {
  return request<void>(`/category-rules/${id}`, { method: "DELETE" });
}

export function testRule(name: string): Promise<RuleTestResult> {
  return request<RuleTestResult>("/category-rules/test", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

/* ------------------------------------------------------------------ 收件箱 */

export function listInbox(): Promise<InboxResult> {
  return request<InboxResult>("/transactions/inbox");
}

export function batchClassify(input: BatchClassifyInput): Promise<BatchClassifyResult> {
  return request<BatchClassifyResult>("/transactions/batch-classify", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
