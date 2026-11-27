"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { Check, Clock3, Receipt, TriangleAlert } from "lucide-react";

import { Divider } from "@/components/ui";
import { useInboxCount } from "@/components/inbox-count";
import { ApiError, createTransaction, suggestCategory } from "@/lib/api/client";
import type { CategorySuggestion, Transaction } from "@/lib/api/types";
import { CATEGORIES, DEMO_TODAY, categoryName } from "@/lib/dict";
import { formatCents, parseYuanToCents } from "@/lib/format";

type Errors = { merchant?: string; amount?: string; date?: string };

const FIELD =
  "w-full rounded-sm border border-line bg-surface px-2.5 py-2 text-[12px] text-ink outline-none placeholder:text-ink-4 focus:border-coral focus:ring-2 focus:ring-coral-100";

function fieldClass(error?: string) {
  return error ? `${FIELD} border-alert-100 ring-1 ring-alert-100` : FIELD;
}

export function QuickEntryForm() {
  const { refresh: refreshInbox } = useInboxCount();
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [manualCategory, setManualCategory] = useState(false);
  const [direction, setDirection] = useState<"EXPENSE" | "INCOME">("EXPENSE");
  const [date, setDate] = useState(DEMO_TODAY);
  const [time, setTime] = useState("");
  const [note, setNote] = useState("");

  const [suggestion, setSuggestion] = useState<CategorySuggestion | null>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [pending, setPending] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [created, setCreated] = useState<Transaction | null>(null);

  const effectiveCategory = manualCategory
    ? categoryId
    : (categoryId ?? suggestion?.categoryId ?? null);
  const cents = parseYuanToCents(amount);

  // 分类建议：防抖 300ms，对应 GET /categories/suggest
  useEffect(() => {
    const name = merchant.trim();
    if (!name) {
      setSuggestion(null);
      return;
    }
    let alive = true;
    const timer = setTimeout(() => {
      suggestCategory(name)
        .then((result) => {
          if (alive) setSuggestion(result);
        })
        .catch(() => {
          if (alive) setSuggestion(null);
        });
    }, 300);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [merchant]);

  function touch() {
    setCreated(null);
    setSubmitError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next: Errors = {};
    if (!merchant.trim()) next.merchant = "请填写商户 / 名称";
    if (cents === null) next.amount = "金额需为正数，最多两位小数";
    else if (cents === 0) next.amount = "金额需大于 0";
    if (!date) next.date = "请选择日期";
    else if (date > DEMO_TODAY) next.date = `不能晚于今天（${DEMO_TODAY}）`;
    setErrors(next);
    if (Object.keys(next).length > 0 || cents === null) return;

    setPending(true);
    setSubmitError(null);
    try {
      const tx = await createTransaction({
        merchant: merchant.trim(),
        amount: cents,
        direction,
        occurredAt: `${date}T${time || "12:00"}:00+08:00`,
        categoryId: effectiveCategory,
        note: note.trim() || null,
      });
      setCreated(tx);
      // 未分类会进收件箱，顺手刷新侧栏角标
      if (!tx.categoryId) refreshInbox();
      setMerchant("");
      setAmount("");
      setNote("");
      setCategoryId(null);
      setManualCategory(false);
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : "保存失败，请重试");
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      onKeyDown={(event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.currentTarget.requestSubmit();
        }
      }}
      className="grid items-start gap-3 lg:grid-cols-[1fr_232px]"
    >
      {/* 左：表单 */}
      <section className="rounded-md border border-line bg-surface p-4 shadow-1">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-[12px] font-semibold">记一笔</h2>
          <p className="text-[9.5px] text-ink-4">仅填名称 + 金额 + 日期即可入账</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5">
            <span className="text-[9.5px] text-ink-3">商户 / 名称</span>
            <input
              value={merchant}
              onChange={(event) => {
                setMerchant(event.target.value);
                touch();
              }}
              placeholder="例如：楼下便利店"
              className={fieldClass(errors.merchant)}
            />
            {errors.merchant ? (
              <span className="text-[9px] text-alert-ink">{errors.merchant}</span>
            ) : (
              <span className="text-[9px] text-ink-4">用于分类规则匹配</span>
            )}
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-[9.5px] text-ink-3">金额（元）</span>
            <input
              value={amount}
              onChange={(event) => {
                setAmount(event.target.value);
                touch();
              }}
              inputMode="decimal"
              placeholder="24.50"
              className={`${fieldClass(errors.amount)} nums text-[14px] font-bold`}
            />
            {errors.amount ? (
              <span className="text-[9px] text-alert-ink">{errors.amount}</span>
            ) : (
              <span className="text-[9px] text-ink-4">入库转整数分，不用浮点</span>
            )}
          </label>

          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <span className="text-[9.5px] text-ink-3">
              分类
              {manualCategory
                ? "（已手动指定）"
                : suggestion?.matchedBy
                  ? `（自动匹配：命中「${suggestion.keyword}」）`
                  : "（未命中规则则进收件箱）"}
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {CATEGORIES.map((category) => {
                const active = effectiveCategory === category.id;
                return (
                  <button
                    key={category.id}
                    type="button"
                    onClick={() => {
                      setCategoryId(category.id);
                      setManualCategory(true);
                      touch();
                    }}
                    className={
                      active
                        ? "rounded-pill border border-coral-100 bg-coral-50 px-2.5 py-1 text-[10px] font-semibold text-coral-ink"
                        : "rounded-pill border border-line bg-surface px-2.5 py-1 text-[10px] text-ink-2 hover:bg-sunken"
                    }
                  >
                    {category.name}
                  </button>
                );
              })}
              <button
                type="button"
                onClick={() => {
                  setCategoryId(null);
                  setManualCategory(true);
                  touch();
                }}
                className={
                  manualCategory && categoryId === null
                    ? "rounded-pill border border-warn-100 bg-warn-50 px-2.5 py-1 text-[10px] font-semibold text-warn-ink"
                    : "rounded-pill border border-line bg-surface px-2.5 py-1 text-[10px] text-ink-2 hover:bg-sunken"
                }
              >
                未分类
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[9.5px] text-ink-3">方向</span>
            <div className="flex gap-0.5 self-start rounded-pill bg-sunken p-0.5">
              {(["EXPENSE", "INCOME"] as const).map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => {
                    setDirection(item);
                    touch();
                  }}
                  className={
                    direction === item
                      ? "rounded-pill bg-surface px-3 py-1 text-[10px] font-semibold text-ink shadow-1"
                      : "rounded-pill px-3 py-1 text-[10px] text-ink-3"
                  }
                >
                  {item === "EXPENSE" ? "支出" : "收入"}
                </button>
              ))}
            </div>
          </div>

          <label className="flex flex-col gap-1.5">
            <span className="text-[9.5px] text-ink-3">日期</span>
            <input
              type="date"
              max={DEMO_TODAY}
              value={date}
              onChange={(event) => {
                setDate(event.target.value);
                touch();
              }}
              className={fieldClass(errors.date)}
            />
            {errors.date ? <span className="text-[9px] text-alert-ink">{errors.date}</span> : null}
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="text-[9.5px] text-ink-3">时间（可留空）</span>
            <input
              type="time"
              value={time}
              onChange={(event) => {
                setTime(event.target.value);
                touch();
              }}
              className={fieldClass()}
            />
            <span className="text-[9px] text-ink-4">留空按 12:00 记录</span>
          </label>

          <label className="flex flex-col gap-1.5 sm:col-span-2">
            <span className="text-[9.5px] text-ink-3">备注</span>
            <textarea
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
                touch();
              }}
              rows={2}
              placeholder="可选，例如：加班夜宵"
              className={`${FIELD} resize-none`}
            />
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={pending}
            className={`press inline-flex items-center gap-1.5 rounded-pill bg-coral px-3.5 py-2 text-[11px] font-semibold text-ink-on-coral ${
              pending ? "cursor-not-allowed opacity-60" : ""
            }`}
          >
            <Check size={12} />
            {pending ? "保存中…" : "保存并继续记一笔"}
          </button>
          <Link
            href="/ledger"
            className="press inline-flex items-center gap-1.5 rounded-pill border border-line bg-surface px-3 py-1.5 text-[11px] text-ink-2 hover:bg-sunken"
          >
            取消
          </Link>
          <span className="ml-auto text-[9px] text-ink-4">⌘ / Ctrl + Enter 提交</span>
        </div>

        {created ? (
          <div className="mt-3 flex items-start gap-1.5 rounded-sm border border-mint-100 bg-mint-50 px-3 py-2 text-[9.5px] leading-relaxed text-mint-ink">
            <Check size={11} className="mt-0.5 shrink-0" />
            <span>
              已记入账本：{created.merchant} · {formatCents(created.amount)} ·{" "}
              {categoryName(created.categoryId) ?? "未分类"} ·{" "}
              {created.occurredAt.slice(5, 16).replace("T", " ")}
              <Link href="/ledger" className="ml-1.5 underline decoration-dotted underline-offset-2">
                去账本查看
              </Link>
            </span>
          </div>
        ) : null}

        {submitError ? (
          <p className="mt-3 flex items-center gap-1.5 rounded-sm border border-alert-100 bg-alert-50 px-3 py-2 text-[9.5px] text-alert-ink">
            <TriangleAlert size={11} />
            {submitError}
          </p>
        ) : null}
      </section>

      {/* 右：入账预览 */}
      <div className="flex flex-col gap-3">
        <section className="rounded-md border border-line bg-canvas p-4">
          <h3 className="mb-3 text-[11px] font-semibold text-ink-2">入账预览</h3>
          <div className="flex items-center gap-2">
            <Receipt size={15} className="shrink-0 text-ink-4" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[11px] font-semibold">
                {merchant.trim() || "未填写名称"}
              </p>
              <p className="mt-0.5 truncate text-[9px] text-ink-4">
                {(date || "——").slice(5)} {time || "12:00"} ·{" "}
                {categoryName(effectiveCategory) ?? "未分类"} · MANUAL
              </p>
            </div>
            <span
              className={`nums shrink-0 text-[13px] font-bold ${
                direction === "INCOME" ? "text-mint-ink" : ""
              }`}
            >
              {cents === null ? "—" : `${direction === "INCOME" ? "+" : "-"}${formatCents(cents)}`}
            </span>
          </div>

          <Divider className="my-2.5" />

          <dl className="flex flex-col gap-1.5 text-[9.5px]">
            <div className="flex items-center justify-between gap-2">
              <dt className="text-ink-4">来源</dt>
              <dd className="text-right">MANUAL（系统生成 external_id）</dd>
            </div>
            <div className="flex items-center justify-between gap-2">
              <dt className="text-ink-4">分类</dt>
              <dd className="text-right">
                {manualCategory
                  ? "手动指定"
                  : suggestion?.matchedBy
                    ? `规则命中「${suggestion.keyword}」`
                    : "未命中 → 收件箱"}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-2">
              <dt className="text-ink-4">合并</dt>
              <dd className="text-right">同商户同日同金额不自动合并</dd>
            </div>
            {note.trim() ? (
              <div className="flex items-start justify-between gap-2">
                <dt className="shrink-0 text-ink-4">备注</dt>
                <dd className="text-right">{note.trim()}</dd>
              </div>
            ) : null}
          </dl>
        </section>

        <section className="rounded-md border border-line bg-canvas p-4">
          <h3 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-ink-2">
            <Clock3 size={12} className="text-ink-4" />
            小提示
          </h3>
          <ul className="flex flex-col gap-1.5 text-[9.5px] leading-relaxed text-ink-4">
            <li>· 时间留空按 12:00 记录，不影响当月统计口径。</li>
            <li>· 分类可手动指定；未命中规则时进入「待分类收件箱」。</li>
            <li>· 保存后即出现在账本，参与本月概览与后续预算预警。</li>
          </ul>
        </section>
      </div>
    </form>
  );
}
