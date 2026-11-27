"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowRight, CalendarDays, PenLine, RefreshCw, TriangleAlert } from "lucide-react";

import { CategoryDonut, sliceColor } from "@/components/charts/category-donut";
import { TrendBarChart } from "@/components/charts/trend-bar-chart";
import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  EmptyState,
  PageHeader,
  Skeleton,
  cx,
} from "@/components/ui";
import {
  ApiError,
  getBudget,
  getCategoryBreakdown,
  getMonthlyTrend,
  getMonthSummary,
  listAlerts,
  listTransactions,
} from "@/lib/api/client";
import type {
  AlertEvent,
  Budget,
  CategorySlice,
  MonthSummary,
  Transaction,
  TrendPoint,
} from "@/lib/api/types";
import { CURRENT_MONTH, categoryName } from "@/lib/dict";
import { formatCents, formatTxTime } from "@/lib/format";

type Status = "loading" | "ready" | "error";
const RECENT_LIMIT = 5;

export function DashboardView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const month = searchParams.get("month") ?? CURRENT_MONTH;

  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<MonthSummary | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [slices, setSlices] = useState<CategorySlice[]>([]);
  const [recent, setRecent] = useState<Transaction[]>([]);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [reloadKey, setReloadKey] = useState(0);

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const [nextSummary, nextTrend, nextSlices, page, nextBudget, alertPage] = await Promise.all([
        getMonthSummary(month),
        getMonthlyTrend(month, 6),
        getCategoryBreakdown(month),
        listTransactions({
          month,
          source: "ALL",
          categoryId: "ALL",
          keyword: "",
          direction: "ALL",
          page: 1,
          pageSize: RECENT_LIMIT,
        }),
        getBudget(),
        listAlerts({ month, pageSize: 10 }),
      ]);
      setSummary(nextSummary);
      setTrend(nextTrend);
      setSlices(nextSlices);
      setRecent(page.items);
      setBudget(nextBudget);
      setAlerts(alertPage.items);
      setStatus("ready");
      setError(null);
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : "加载失败");
    }
  }, [month]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  function changeMonth(next: string) {
    router.replace(next ? `/?month=${next}` : "/", { scroll: false });
  }

  const empty =
    status === "ready" &&
    (summary?.totalExpense ?? 0) === 0 &&
    (summary?.totalIncome ?? 0) === 0 &&
    recent.length === 0;

  // 环比：仅当上月有数据时给出百分比，避免 0 做的除数
  const currentExpense = trend[trend.length - 1]?.expense ?? 0;
  const previousExpense = trend[trend.length - 2]?.expense ?? 0;
  const deltaRatio = previousExpense > 0 ? (currentExpense - previousExpense) / previousExpense : null;
  const trendDelta =
    deltaRatio === null
      ? { label: "上月无数据", tone: "text-ink-4" }
      : {
          label: `较上月 ${deltaRatio >= 0 ? "+" : ""}${(deltaRatio * 100).toFixed(1)}%`,
          tone: deltaRatio > 0 ? "text-warn-ink" : "text-mint-ink",
        };

  // 预算：与预算页同一口径（支出口径见 dev-store.monthExpense）
  const budgetAmount = budget?.amount ?? 0;
  const spent = summary?.totalExpense ?? 0;
  const budgetRatio = budgetAmount > 0 ? spent / budgetAmount : 0;
  const warnLine = budget?.warnThreshold ?? 0.8;
  const alertLine = budget?.alertThreshold ?? 1;
  const budgetBarTone =
    budgetRatio >= alertLine ? "bg-alert" : budgetRatio >= warnLine ? "bg-warn" : "bg-mint";
  const unreadAlert =
    alerts.find((item) => !item.read && item.level === "ALERT") ??
    alerts.find((item) => !item.read) ??
    null;

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="仪表盘"
        subtitle={`${month} · 支出已剔除转账与退款 · 金额单位「分」`}
        action={
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] text-ink-2">
              <CalendarDays size={11} className="text-ink-4" />
              <input
                type="month"
                value={month}
                aria-label="月份"
                onChange={(event) => changeMonth(event.target.value)}
                className="w-[102px] bg-transparent text-[10px] outline-none"
              />
            </label>
            <Button variant="ghost" onClick={() => setReloadKey((key) => key + 1)}>
              <RefreshCw size={11} />
              刷新
            </Button>
            <ButtonLink href="/import/quick" variant="ghost">
              <PenLine size={11} />
              记一笔
            </ButtonLink>
            <ButtonLink href="/import">导入账单</ButtonLink>
          </div>
        }
      />

      {status === "ready" && unreadAlert ? (
        <div
          className={cx(
            "flex flex-wrap items-center gap-2 rounded-sm border px-3 py-2",
            unreadAlert.level === "ALERT"
              ? "border-alert-100 bg-alert-50"
              : "border-warn-100 bg-warn-50",
          )}
        >
          <TriangleAlert
            size={12}
            className={unreadAlert.level === "ALERT" ? "text-alert-ink" : "text-warn-ink"}
          />
          <span
            className={cx(
              "text-[10px]",
              unreadAlert.level === "ALERT" ? "text-alert-ink" : "text-warn-ink",
            )}
          >
            {unreadAlert.period} 支出已达预算的{" "}
            {Math.round((unreadAlert.actual / unreadAlert.budget) * 100)}%，跨过{" "}
            {Math.round(unreadAlert.threshold * 100)}%
            {unreadAlert.level === "ALERT" ? "告警线" : "预警线"}
          </span>
          <Link
            href="/budget"
            className={cx(
              "ml-auto text-[9.5px] underline decoration-dotted underline-offset-2",
              unreadAlert.level === "ALERT" ? "text-alert-ink" : "text-warn-ink",
            )}
          >
            查看预算
          </Link>
        </div>
      ) : null}

      {status === "error" ? (
        <Card className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <p className="text-xs font-semibold text-ink-2">仪表盘加载失败</p>
          <p className="text-[10px] text-ink-4">{error}</p>
          <Button variant="ghost" onClick={() => setReloadKey((key) => key + 1)}>
            重试
          </Button>
        </Card>
      ) : null}

      {status === "loading" ? <DashboardSkeleton /> : null}

      {empty ? (
        <Card>
          <EmptyState
            title="这个月还没有流水"
            description="导入支付宝 / 微信账单，或先记一笔；入库后这里会出现支出趋势、分类分布与预算进度。"
            action={
              <span className="flex items-center gap-2">
                <ButtonLink href="/import">去导入</ButtonLink>
                <ButtonLink href="/import/quick" variant="ghost">
                  快捷记一笔
                </ButtonLink>
              </span>
            }
          />
        </Card>
      ) : null}

      {status === "ready" && !empty && summary ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Card className="p-4">
              <p className="text-[10px] text-ink-3">本月总支出</p>
              <p className="nums mt-1 text-[22px] font-bold tracking-tight">
                {formatCents(summary.totalExpense)}
              </p>
              <p className="mt-1 text-[9px] text-ink-4">
                已剔除 {summary.excludedTransferCount} 笔转账 · {summary.excludedRefundCount} 笔退款
              </p>
            </Card>

            <Card className="p-4">
              <p className="text-[10px] text-ink-3">本月收入</p>
              <p className="nums mt-1 text-[22px] font-bold tracking-tight text-mint-ink">
                {formatCents(summary.totalIncome)}
              </p>
              <p className="mt-1 text-[9px] text-ink-4">已关联的退款不计入收入</p>
            </Card>

            <Card className="p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[10px] text-ink-3">待处理</p>
                <Link
                  href="/inbox"
                  className="text-[9px] text-ink-2 underline decoration-dotted underline-offset-2"
                >
                  去收件箱
                </Link>
              </div>
              <p className="nums mt-1 text-[22px] font-bold tracking-tight">
                {summary.uncategorized}
                <span className="ml-1 text-[11px] font-normal text-ink-3">笔待分类</span>
              </p>
              <p className="mt-1 text-[9px] text-ink-4">疑似重复 {summary.duplicate} 笔，请核对后再处理</p>
            </Card>
          </div>

          <div className="grid items-start gap-3 lg:grid-cols-[1.55fr_1fr]">
            <Card>
              <CardHeader
                title="近 6 个月支出趋势"
                hint="单系列，已剔除转账与退款"
                action={<Chip>单位：元</Chip>}
              />
              <div className="px-4 pb-3">
                <TrendBarChart data={trend} />
                <div className="mt-2 flex items-center justify-between border-t border-line-soft pt-2 text-[9.5px]">
                  <span className="text-ink-4">本月 {formatCents(summary.totalExpense)}</span>
                  <span className={cx("font-semibold", trendDelta.tone)}>{trendDelta.label}</span>
                </div>
              </div>
            </Card>

            <Card>
              <CardHeader
                title="分类支出分布"
                hint={month}
                action={<Chip>{slices.length} 个分类</Chip>}
              />
              <div className="px-4 pb-4">
                <CategoryDonut data={slices} total={summary.totalExpense} />
                <ul className="mt-2 flex flex-col gap-1.5">
                  {slices.slice(0, 5).map((slice) => (
                    <li key={slice.categoryId ?? "none"} className="flex items-center gap-2 text-[10px]">
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full"
                        style={{ background: sliceColor(slice.categoryId) }}
                      />
                      <span className="min-w-0 flex-1 truncate text-ink-2">{slice.name}</span>
                      <span className="nums text-ink-3">{formatCents(slice.amount)}</span>
                      <span className="nums w-8 text-right font-semibold">
                        {Math.round(slice.ratio * 100)}%
                      </span>
                    </li>
                  ))}
                  {slices.length === 0 ? (
                    <li className="text-[10px] text-ink-4">本月还没有支出</li>
                  ) : null}
                </ul>
              </div>
            </Card>
          </div>

          <div className="grid items-start gap-3 lg:grid-cols-[1.55fr_1fr]">
            <Card>
              <CardHeader
                title="最近流水"
                hint={`最近 ${recent.length} 条`}
                action={
                  <Link href="/ledger" className="text-[9.5px] text-ink-2 underline decoration-dotted underline-offset-2">
                    查看全部
                  </Link>
                }
              />
              <ul className="px-4 pb-2">
                {recent.length === 0 ? (
                  <li className="py-3 text-[10px] text-ink-4">本月还没有流水</li>
                ) : null}
                {recent.map((tx) => {
                  const income = tx.direction === "INCOME";
                  const transfer = tx.direction === "TRANSFER";
                  return (
                    <li key={tx.id} className="border-b border-line-soft last:border-b-0">
                      <Link
                        href={`/ledger/${tx.id}`}
                        className="flex items-center gap-2 py-2 hover:bg-canvas"
                      >
                        <span className="w-[72px] shrink-0 text-[9.5px] text-ink-3">
                          {formatTxTime(tx.occurredAt)}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-[11px] font-semibold">
                          {tx.merchant}
                        </span>
                        <span className="hidden sm:block">
                          {transfer ? (
                            <Chip tone="lilac">转账</Chip>
                          ) : (
                            <Chip>{categoryName(tx.categoryId) ?? "未分类"}</Chip>
                          )}
                        </span>
                        <span
                          className={cx(
                            "nums w-[74px] shrink-0 text-right text-[11px] font-semibold",
                            income && "text-mint-ink",
                            transfer && "text-ink-3",
                          )}
                        >
                          {transfer ? formatCents(tx.amount) : `${income ? "+" : "-"}${formatCents(tx.amount)}`}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </Card>

            <Card>
              <CardHeader
                title="预算使用"
                hint={month}
                action={
                  <Link
                    href="/budget"
                    className="text-[9.5px] text-ink-2 underline decoration-dotted underline-offset-2"
                  >
                    设置
                  </Link>
                }
              />
              <div className="px-4 pb-4">
                {budgetAmount > 0 ? (
                  <>
                    <div className="flex items-baseline gap-1.5">
                      <span className="nums text-[20px] font-bold">{formatCents(spent)}</span>
                      <span className="text-[9.5px] text-ink-4">/ {formatCents(budgetAmount)}</span>
                    </div>

                    <div className="relative mt-2 h-2 rounded-pill bg-sunken">
                      <div
                        className={cx("absolute inset-y-0 left-0 rounded-pill", budgetBarTone)}
                        style={{ width: `${Math.min(budgetRatio, 1) * 100}%` }}
                      />
                      <span
                        className="absolute -top-1 h-4 w-px bg-warn-ink/60"
                        style={{ left: `${Math.min(warnLine, 1) * 100}%` }}
                        title={`预警线 ${Math.round(warnLine * 100)}%`}
                      />
                      <span
                        className="absolute -top-1 h-4 w-px bg-alert-ink/60"
                        style={{ left: `${Math.min(alertLine, 1) * 100}%` }}
                        title={`告警线 ${Math.round(alertLine * 100)}%`}
                      />
                    </div>

                    <div className="mt-1.5 flex items-center justify-between text-[9px] text-ink-4">
                      <span>已用 {Math.round(budgetRatio * 100)}%</span>
                      <span>
                        预警 {Math.round(warnLine * 100)}% / 告警 {Math.round(alertLine * 100)}%
                      </span>
                    </div>
                    <p className="mt-1 text-[9px] text-ink-4">
                      剩余 {formatCents(Math.max(0, budgetAmount - spent))}
                    </p>
                  </>
                ) : (
                  <p className="text-[10px] text-ink-4">
                    还没有设置预算，
                    <Link href="/budget" className="text-coral-ink underline decoration-dotted underline-offset-2">
                      去设置
                    </Link>
                  </p>
                )}
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <Card key={index} className="p-4">
            <Skeleton className="h-2.5 w-16" />
            <Skeleton className="mt-2 h-6 w-28" />
            <Skeleton className="mt-2 h-2 w-32" />
          </Card>
        ))}
      </div>
      <div className="grid items-start gap-3 lg:grid-cols-[1.55fr_1fr]">
        <Card className="p-4">
          <Skeleton className="mb-3 h-3 w-28" />
          <Skeleton className="h-[176px] w-full" />
        </Card>
        <Card className="p-4">
          <Skeleton className="mb-3 h-3 w-24" />
          <Skeleton className="mx-auto h-[140px] w-[140px] rounded-full" />
          <Skeleton className="mt-3 h-2.5 w-full" />
        </Card>
      </div>
      <Card className="p-4">
        <Skeleton className="mb-3 h-3 w-20" />
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="mb-2 h-3 w-full" />
        ))}
      </Card>
    </div>
  );
}
