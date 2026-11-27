"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { LedgerFilterBar } from "@/components/ledger/filter-bar";
import { TransactionTable, type LoadStatus } from "@/components/ledger/transaction-table";
import { ButtonLink, Card, CardHeader, DevNote, Divider, PageHeader } from "@/components/ui";
import { ApiError, getMonthSummary, listTransactions, USING_DEV_STUB } from "@/lib/api/client";
import type { LedgerFilters, MonthSummary, TxDirection, TxPage, TxSource } from "@/lib/api/types";
import { CURRENT_MONTH } from "@/lib/dict";
import { formatCents } from "@/lib/format";

const PAGE_SIZE = 10;
const ALL_MONTHS = "all";
const VALID_SOURCES: Array<TxSource | "ALL"> = ["ALL", "ALIPAY", "WECHAT", "SCREENSHOT", "MANUAL"];
const VALID_DIRECTIONS: Array<TxDirection | "ALL"> = ["ALL", "EXPENSE", "INCOME", "TRANSFER"];

type UrlPatch = Partial<Record<"month" | "source" | "direction" | "category" | "q" | "page", string | null>>;

export function LedgerView() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const monthParam = searchParams.get("month");
  const sourceParam = searchParams.get("source") as (TxSource | "ALL") | null;
  const directionParam = searchParams.get("direction") as (TxDirection | "ALL") | null;
  const filters: LedgerFilters = {
    month: monthParam === ALL_MONTHS ? "" : (monthParam ?? CURRENT_MONTH),
    source: sourceParam && VALID_SOURCES.includes(sourceParam) ? sourceParam : "ALL",
    categoryId: searchParams.get("category") ?? "ALL",
    keyword: searchParams.get("q") ?? "",
    direction:
      directionParam && VALID_DIRECTIONS.includes(directionParam) ? directionParam : "ALL",
  };
  const page = Math.max(1, Number(searchParams.get("page") ?? 1) || 1);

  const [status, setStatus] = useState<LoadStatus>("loading");
  const [data, setData] = useState<TxPage | null>(null);
  const [summary, setSummary] = useState<MonthSummary | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  /** 所有筛选与分页都写进 URL，刷新/分享可复现 */
  const applyUrl = useCallback(
    (patch: UrlPatch, resetPage = true) => {
      const next = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(patch)) {
        if (value === null || value === "") next.delete(key);
        else next.set(key, value);
      }
      if (resetPage) next.delete("page");
      const query = next.toString();
      router.replace(query ? `/ledger?${query}` : "/ledger", { scroll: false });
    },
    [router, searchParams],
  );

  const handleFilterChange = useCallback(
    (patch: Partial<LedgerFilters>) => {
      const urlPatch: UrlPatch = {};
      if (patch.month !== undefined) urlPatch.month = patch.month || ALL_MONTHS;
      if (patch.source !== undefined) urlPatch.source = patch.source === "ALL" ? null : patch.source;
      if (patch.direction !== undefined)
        urlPatch.direction = patch.direction === "ALL" ? null : patch.direction;
      if (patch.categoryId !== undefined)
        urlPatch.category = patch.categoryId === "ALL" ? null : patch.categoryId;
      if (patch.keyword !== undefined) urlPatch.q = patch.keyword.trim() || null;
      applyUrl(urlPatch);
    },
    [applyUrl],
  );

  const { month, source, categoryId, keyword, direction } = filters;

  useEffect(() => {
    let alive = true;
    setStatus("loading");

    listTransactions({ month, source, categoryId, keyword, direction, page, pageSize: PAGE_SIZE })
      .then((result) => {
        if (!alive) return;
        setData(result);
        setErrorText(null);
        setStatus("ready");
        // 页码越界时服务端会收敛到最后一页，这里同步回 URL
        if (result.page !== page) applyUrl({ page: String(result.page) }, false);
      })
      .catch((error: unknown) => {
        if (!alive) return;
        setStatus("error");
        setErrorText(error instanceof ApiError ? error.message : "未知错误");
      });

    getMonthSummary(month)
      .then((result) => {
        if (alive) setSummary(result);
      })
      .catch(() => {
        /* 概览失败不阻塞列表 */
      });

    return () => {
      alive = false;
    };
  }, [month, source, categoryId, keyword, direction, page, reloadKey, applyUrl]);

  const hasFilters =
    source !== "ALL" || categoryId !== "ALL" || keyword.trim() !== "" || direction !== "ALL";

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="账本"
        subtitle={
          status === "ready" && data
            ? `${month || "全部月份"} · ${data.total} 条`
            : status === "error"
              ? "加载失败"
              : "加载中…"
        }
        action={<ButtonLink href="/import">导入账单</ButtonLink>}
      />

      <LedgerFilterBar value={filters} onChange={handleFilterChange} onReset={() => router.replace("/ledger", { scroll: false })} />

      <div className="grid items-start gap-3 lg:grid-cols-[1fr_168px]">
        <TransactionTable
          page={data}
          status={status}
          hasFilters={hasFilters}
          errorDetail={errorText}
          excluded={
            summary
              ? { transfers: summary.excludedTransferCount, refunds: summary.excludedRefundCount }
              : undefined
          }
          onRetry={() => setReloadKey((key) => key + 1)}
          onPageChange={(next) => applyUrl({ page: next > 1 ? String(next) : null }, false)}
          onClearFilters={() => router.replace("/ledger", { scroll: false })}
        />
        <MonthSummary summary={summary} month={month} />
      </div>

      <DevNote>
        数据来自 <code className="font-mono">{USING_DEV_STUB ? "/api/dev（开发桩）" : process.env.NEXT_PUBLIC_API_BASE}</code>
        ：筛选与分页已写入 URL（可直接复制地址分享），请求走 <code className="font-mono">lib/api/client.ts</code>。
        后端就绪后在 <code className="font-mono">.env.local</code> 里设置{" "}
        <code className="font-mono">NEXT_PUBLIC_API_BASE</code> 即可切换，无需改页面。
        {USING_DEV_STUB ? (
          <button
            type="button"
            onClick={async () => {
              await fetch("/api/dev/fail", { method: "POST" });
              setReloadKey((key) => key + 1);
            }}
            className="ml-1 underline decoration-dotted underline-offset-2 hover:text-ink-2"
          >
            模拟一次 500
          </button>
        ) : null}
      </DevNote>
    </div>
  );
}

function MonthSummary({ summary, month }: { summary: MonthSummary | null; month: string }) {
  const rows = [
    { label: "支出", value: summary ? formatCents(summary.totalExpense) : "—", tone: "" },
    {
      label: "收入",
      value: summary ? formatCents(summary.totalIncome) : "—",
      tone: "text-mint-ink",
    },
  ];

  return (
    <Card className="lg:sticky lg:top-4">
      <CardHeader title="本月概览" hint={month || "全部"} />
      <div className="flex flex-col gap-2 px-4 pb-3.5 text-[10px]">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between">
            <span className="text-ink-3">{row.label}</span>
            <span className={`nums font-semibold ${row.tone}`}>{row.value}</span>
          </div>
        ))}
        <Divider className="my-1" />
        <div className="flex items-center justify-between">
          <span className="text-ink-3">未分类</span>
          <span className="nums font-semibold">{summary ? `${summary.uncategorized} 笔` : "—"}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-ink-3">疑似重复</span>
          <span className="nums font-semibold">{summary ? `${summary.duplicate} 笔` : "—"}</span>
        </div>
        <p className="mt-1 text-[9px] leading-relaxed text-ink-4">金额入库为整数分，展示层统一格式化</p>
      </div>
    </Card>
  );
}
