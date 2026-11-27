"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BellRing, Check, RotateCcw, TriangleAlert } from "lucide-react";

import {
  Button,
  Card,
  CardHeader,
  Chip,
  Divider,
  PageHeader,
  Skeleton,
  cx,
} from "@/components/ui";
import { ApiError, getBudget, getMonthSummary, listAlerts, markAlertRead, saveBudget } from "@/lib/api/client";
import type { AlertEvent, Budget, MonthSummary } from "@/lib/api/types";
import { CURRENT_MONTH, DEMO_TODAY } from "@/lib/dict";
import { formatCents, parseYuanToCents } from "@/lib/format";

type Status = "loading" | "ready" | "error";
type Notice = { tone: "ok" | "err"; text: string } | null;

const FIELD =
  "w-full rounded-sm border border-line bg-surface px-2.5 py-2 text-[12px] text-ink outline-none placeholder:text-ink-4 focus:border-coral focus:ring-2 focus:ring-coral-100";

function fieldClass(error?: string) {
  return error ? `${FIELD} border-alert-100 ring-1 ring-alert-100` : FIELD;
}

function daysLeftInMonth(month: string, today: string): number {
  const [year, mon] = month.split("-").map(Number);
  const total = new Date(Date.UTC(year, mon, 0)).getUTCDate();
  const day = month === today.slice(0, 7) ? Number(today.slice(8, 10)) : total;
  return Math.max(1, total - day + 1);
}

export function BudgetView() {
  const month = CURRENT_MONTH;
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [summary, setSummary] = useState<MonthSummary | null>(null);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  const [amount, setAmount] = useState("");
  const [warn, setWarn] = useState("80");
  const [alert, setAlert] = useState("100");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  const hydrate = useCallback((config: Budget) => {
    setAmount((config.amount / 100).toFixed(2));
    setWarn(String(Math.round(config.warnThreshold * 100)));
    setAlert(String(Math.round(config.alertThreshold * 100)));
    setErrors({});
  }, []);

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setStatus("loading");
      try {
        const [config, nextSummary, page] = await Promise.all([
          getBudget(),
          getMonthSummary(month),
          listAlerts({ month, pageSize: 20 }),
        ]);
        setBudget(config);
        setSummary(nextSummary);
        setAlerts(page.items);
        if (!silent) hydrate(config);
        setStatus("ready");
        setError(null);
      } catch (err) {
        setStatus("error");
        setError(err instanceof ApiError ? err.message : "加载失败");
      }
    },
    [month, hydrate],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const spent = summary?.totalExpense ?? 0;
  const budgetAmount = budget?.amount ?? 0;
  const ratio = budgetAmount > 0 ? spent / budgetAmount : 0;
  const remaining = Math.max(0, budgetAmount - spent);
  const dailyAvailable = remaining / daysLeftInMonth(month, DEMO_TODAY);
  const warnValue = budget?.warnThreshold ?? 0.8;
  const alertValue = budget?.alertThreshold ?? 1;
  const barTone = ratio >= alertValue ? "bg-alert" : ratio >= warnValue ? "bg-warn" : "bg-mint";
  const unread = alerts.filter((item) => !item.read).length;

  async function handleSave() {
    const next: Record<string, string> = {};
    const cents = parseYuanToCents(amount);
    if (cents === null || cents === 0) next.amount = "预算需为大于 0 的数字";
    const warnNum = Number(warn);
    const alertNum = Number(alert);
    if (!Number.isFinite(warnNum) || warnNum <= 0) next.warn = "预警线需大于 0";
    if (!Number.isFinite(alertNum)) next.alert = "告警线需为数字";
    if (Number.isFinite(warnNum) && Number.isFinite(alertNum) && alertNum <= warnNum) {
      next.alert = "告警线必须高于预警线";
    }
    setErrors(next);
    if (Object.keys(next).length > 0 || cents === null) return;

    setSaving(true);
    setNotice(null);
    try {
      const saved = await saveBudget({
        amount: cents,
        warnThreshold: warnNum / 100,
        alertThreshold: alertNum / 100,
      });
      setBudget(saved);
      hydrate(saved);
      setNotice({ tone: "ok", text: "已保存，阈值立即生效（跨线会生成新的预警事件）" });
      await load(true);
    } catch (err) {
      const detail = err instanceof ApiError ? err.details?.[0] : undefined;
      setNotice({
        tone: "err",
        text: detail ? `${detail.reason}（${detail.field}）` : err instanceof ApiError ? err.message : "保存失败",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleMarkRead(id: string) {
    try {
      await markAlertRead(id);
      setAlerts((prev) => prev.map((item) => (item.id === id ? { ...item, read: true } : item)));
    } catch (err) {
      setNotice({ tone: "err", text: err instanceof ApiError ? err.message : "操作失败" });
    }
  }

  async function handleMarkAllRead() {
    const targets = alerts.filter((item) => !item.read);
    try {
      await Promise.all(targets.map((item) => markAlertRead(item.id)));
      setAlerts((prev) => prev.map((item) => ({ ...item, read: true })));
    } catch (err) {
      setNotice({ tone: "err", text: err instanceof ApiError ? err.message : "操作失败" });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="预算与预警"
        subtitle={`${month} · 双阈值：跨预警线触发一次 WARN，跨告警线触发一次 ALERT`}
        action={
          <Link
            href="/"
            className="text-[10px] text-ink-2 underline decoration-dotted underline-offset-2"
          >
            回到仪表盘
          </Link>
        }
      />

      {notice ? (
        <p
          className={cx(
            "rounded-sm border px-3 py-2 text-[10px]",
            notice.tone === "ok"
              ? "border-mint-100 bg-mint-50 text-mint-ink"
              : "border-alert-100 bg-alert-50 text-alert-ink",
          )}
        >
          {notice.text}
        </p>
      ) : null}

      {status === "error" ? (
        <Card className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <p className="text-xs font-semibold text-ink-2">预算加载失败</p>
          <p className="text-[10px] text-ink-4">{error}</p>
          <Button variant="ghost" onClick={() => void load()}>
            重试
          </Button>
        </Card>
      ) : null}

      {status === "loading" ? (
        <div className="grid items-start gap-3 lg:grid-cols-[1fr_250px]">
          <Card className="p-4">
            <Skeleton className="mb-3 h-3 w-24" />
            <div className="grid gap-3 sm:grid-cols-2">
              <Skeleton className="h-9" />
              <Skeleton className="h-9" />
            </div>
            <Skeleton className="mt-4 h-2 w-full" />
          </Card>
          <Card className="p-4">
            <Skeleton className="mx-auto h-[104px] w-[104px] rounded-full" />
          </Card>
        </div>
      ) : null}

      {status === "ready" ? (
        <div className="grid items-start gap-3 lg:grid-cols-[1fr_250px]">
          <div className="flex flex-col gap-3">
            <Card className="p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-[12px] font-semibold">月度预算与双阈值</h2>
                <div className="flex items-center gap-1.5">
                  <Chip>{month} 生效</Chip>
                  {unread > 0 ? <Chip tone={ratio >= alertValue ? "alert" : "warn"}>{unread} 条未读</Chip> : null}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-1.5">
                  <span className="text-[9.5px] text-ink-3">月度预算（元）</span>
                  <input
                    value={amount}
                    onChange={(event) => setAmount(event.target.value)}
                    inputMode="decimal"
                    className={`${fieldClass(errors.amount)} nums text-[15px] font-bold`}
                  />
                  <span className={cx("text-[9px]", errors.amount ? "text-alert-ink" : "text-ink-4")}>
                    {errors.amount ?? "保存时转整数分"}
                  </span>
                </label>

                <div className="flex flex-col gap-1.5">
                  <span className="text-[9.5px] text-ink-3">当前进度</span>
                  <div className="flex items-baseline gap-1.5">
                    <span className="nums text-[15px] font-bold">{Math.round(ratio * 100)}%</span>
                    <span className="text-[9.5px] text-ink-4">
                      已用 {formatCents(spent)} / {formatCents(budgetAmount)}
                    </span>
                  </div>
                  <div className="relative mt-1 h-2 rounded-pill bg-sunken">
                    <div
                      className={cx("absolute inset-y-0 left-0 rounded-pill", barTone)}
                      style={{ width: `${Math.min(ratio, 1) * 100}%` }}
                    />
                    <span
                      className="absolute -top-1 h-4 w-px bg-warn-ink/60"
                      style={{ left: `${Math.min(warnValue, 1) * 100}%` }}
                      title={`预警线 ${Math.round(warnValue * 100)}%`}
                    />
                    <span
                      className="absolute -top-1 h-4 w-px bg-alert-ink/60"
                      style={{ left: `${Math.min(alertValue, 1) * 100}%` }}
                      title={`告警线 ${Math.round(alertValue * 100)}%`}
                    />
                  </div>
                </div>

                <label className="flex flex-col gap-1.5">
                  <span className="text-[9.5px] text-ink-3">预警线 warnThreshold（%）</span>
                  <input
                    value={warn}
                    onChange={(event) => setWarn(event.target.value)}
                    inputMode="numeric"
                    className={fieldClass(errors.warn)}
                  />
                  <span className={cx("text-[9px]", errors.warn ? "text-alert-ink" : "text-ink-4")}>
                    {errors.warn ?? "默认 80%，跨线产生一条 WARN 事件"}
                  </span>
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-[9.5px] text-ink-3">告警线 alertThreshold（%）</span>
                  <input
                    value={alert}
                    onChange={(event) => setAlert(event.target.value)}
                    inputMode="numeric"
                    className={fieldClass(errors.alert)}
                  />
                  <span className={cx("text-[9px]", errors.alert ? "text-alert-ink" : "text-ink-4")}>
                    {errors.alert ?? "默认 100%，跨线产生一条 ALERT 事件"}
                  </span>
                </label>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Button
                  variant="primary"
                  onClick={() => void handleSave()}
                  className={cx(saving && "pointer-events-none opacity-60")}
                >
                  <Check size={12} />
                  {saving ? "保存中…" : "保存设置"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setAmount("4200.00");
                    setWarn("80");
                    setAlert("100");
                    setErrors({});
                    setNotice(null);
                  }}
                >
                  <RotateCcw size={11} />
                  恢复默认值
                </Button>
                <span className="ml-auto text-[9px] text-ink-4">同一阈值在同一月内只触发一次</span>
              </div>
            </Card>

            <Card>
              <CardHeader
                title="预警事件"
                hint={`${month} · 共 ${alerts.length} 条`}
                action={
                  unread > 0 ? (
                    <Button variant="tiny" onClick={() => void handleMarkAllRead()}>
                      全部标记已读
                    </Button>
                  ) : (
                    <Chip tone="mint">全部已读</Chip>
                  )
                }
              />
              <div className="px-4 pb-3">
                <Divider className="mb-2" />
                {alerts.length === 0 ? (
                  <p className="py-6 text-center text-[10px] text-ink-4">
                    本月还没有跨线事件。把预算调低，或继续记账直到超过 80% 就会出现在这里。
                  </p>
                ) : (
                  <ul className="flex flex-col">
                    {alerts.map((item) => {
                      const isAlert = item.level === "ALERT";
                      const actualRatio = item.budget > 0 ? item.actual / item.budget : 0;
                      return (
                        <li
                          key={item.id}
                          className="flex items-start gap-2 border-b border-line-soft py-2 last:border-b-0"
                        >
                          <Chip tone={isAlert ? "alert" : "warn"}>{isAlert ? "告警" : "预警"}</Chip>
                          <div className="min-w-0 flex-1">
                            <p className="text-[10.5px] leading-relaxed">
                              {item.period} 支出达预算的 {Math.round(actualRatio * 100)}%，跨过
                              {Math.round(item.threshold * 100)}%
                              {isAlert ? "告警线" : "预警线"}
                            </p>
                            <p className="mt-0.5 text-[9px] text-ink-4">
                              {item.createdAt.slice(5, 16).replace("T", " ")} · 触发时支出{" "}
                              {formatCents(item.actual)} / 预算 {formatCents(item.budget)}
                            </p>
                          </div>
                          {item.read ? (
                            <span className="shrink-0 text-[9px] text-ink-4">已读</span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => void handleMarkRead(item.id)}
                              className="shrink-0 text-[9.5px] text-ink-2 underline decoration-dotted underline-offset-2"
                            >
                              标记已读
                            </button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </Card>
          </div>

          <div className="flex flex-col gap-3">
            <Card className="p-4">
              <h3 className="mb-3 text-[11px] font-semibold text-ink-2">本月进度</h3>
              <div className="flex flex-col items-center gap-3">
                <div
                  className="relative h-[104px] w-[104px] rounded-full"
                  style={{
                    background: `conic-gradient(${
                      ratio >= alertValue
                        ? "var(--color-alert)"
                        : ratio >= warnValue
                          ? "var(--color-warn)"
                          : "var(--color-mint)"
                    } 0 ${Math.min(ratio, 1) * 100}%, var(--color-sunken) ${Math.min(ratio, 1) * 100}% 100%)`,
                  }}
                >
                  <div className="absolute inset-[13px] flex flex-col items-center justify-center rounded-full bg-canvas">
                    <span className="nums text-[16px] font-bold">{Math.round(ratio * 100)}%</span>
                    <span className="text-[8px] text-ink-4">已用 / 预算</span>
                  </div>
                </div>
                <dl className="flex w-full flex-col gap-1.5 text-[9.5px]">
                  <div className="flex items-center justify-between">
                    <dt className="text-ink-4">剩余可用</dt>
                    <dd className="nums font-semibold">{formatCents(remaining)}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-ink-4">剩余 {daysLeftInMonth(month, DEMO_TODAY)} 天日均</dt>
                    <dd className="nums font-semibold">{formatCents(Math.round(dailyAvailable))}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-ink-4">预警 / 告警</dt>
                    <dd className="nums">
                      {Math.round(warnValue * 100)}% / {Math.round(alertValue * 100)}%
                    </dd>
                  </div>
                </dl>
              </div>
            </Card>

            <Card flat>
              <CardHeader title="触发规则" />
              <ul className="flex flex-col gap-1.5 px-4 pb-4 text-[9.5px] leading-relaxed text-ink-4">
                <li className="flex items-start gap-1.5">
                  <TriangleAlert size={11} className="mt-0.5 shrink-0" />
                  达到 80% 触发一次 WARN，达到 100% 触发一次 ALERT。
                </li>
                <li className="flex items-start gap-1.5">
                  <BellRing size={11} className="mt-0.5 shrink-0" />
                  同一阈值在同一月份只触发一次；换月重新计算。
                </li>
                <li>· 统计口径与仪表盘一致：剔除转账、扣回已关联退款。</li>
                <li>· 预算按月生效；修改阈值后，下一次统计会重新判断是否跨线。</li>
              </ul>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
