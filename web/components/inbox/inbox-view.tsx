"use client";

import { Check, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { useInboxCount } from "@/components/inbox-count";
import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  Divider,
  EmptyState,
  PageHeader,
  Skeleton,
  cx,
} from "@/components/ui";
import { ApiError, batchClassify, listCategories, listInbox } from "@/lib/api/client";
import type { CategoryWithCount, InboxResult, Transaction } from "@/lib/api/types";
import { SOURCE_LABEL } from "@/lib/dict";
import { formatCents, formatTxTime } from "@/lib/format";

type Status = "loading" | "ready" | "error";
type Notice = { tone: "ok" | "err"; text: string } | null;

/** 从商户名里猜一个关键词，减少输入（如「未识别商户 8821」→ 8821） */
function guessKeyword(merchant: string) {
  const digits = merchant.match(/\d{3,}/);
  if (digits) return digits[0];
  return merchant.replace(/[（）()·\s]/g, "").slice(0, 12);
}

export function InboxView() {
  const { refresh: refreshBadge } = useInboxCount();
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<InboxResult | null>(null);
  const [categories, setCategories] = useState<CategoryWithCount[]>([]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [withRule, setWithRule] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [checked, setChecked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setStatus("loading");
    try {
      const [inbox, cats] = await Promise.all([listInbox(), listCategories()]);
      setData(inbox);
      setCategories(cats);
      setSelectedId((prev) =>
        prev && inbox.items.some((item) => item.id === prev) ? prev : (inbox.items[0]?.id ?? null),
      );
      setChecked([]);
      setStatus("ready");
      setError(null);
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : "加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selected: Transaction | null =
    data?.items.find((item) => item.id === selectedId) ?? null;

  // 换选中项时重置右侧面板（成功提示保留，直到用户主动切换）
  useEffect(() => {
    if (!selected) return;
    setCategoryId(null);
    setWithRule(false);
    setKeyword(guessKeyword(selected.merchant));
  }, [selected]);

  function toggleChecked(id: string) {
    setChecked((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  }

  async function classify(ids: string[], withRuleFlag: boolean) {
    if (!categoryId || ids.length === 0) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await batchClassify({
        ids,
        categoryId,
        createRule:
          withRuleFlag && keyword.trim() ? { keyword: keyword.trim() } : undefined,
      });
      const categoryLabel = categories.find((item) => item.id === categoryId)?.name ?? "分类";
      setNotice({
        tone: "ok",
        text: `已归入「${categoryLabel}」共 ${result.updated} 笔${
          result.rule ? `，并建立规则：${result.rule.keyword} → ${categoryLabel}` : ""
        }`,
      });
      refreshBadge();
      await load(true);
    } catch (err) {
      setNotice({ tone: "err", text: err instanceof ApiError ? err.message : "归类失败" });
    } finally {
      setBusy(false);
    }
  }

  const total = data?.total ?? 0;

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="待分类收件箱"
        subtitle={total > 0 ? `${total} 笔待归类 · 归类后立即进入账本统计` : "全部处理完了"}
        action={
          <Button
            variant="ghost"
            onClick={() => {
              void load();
              refreshBadge();
            }}
          >
            <RefreshCw size={11} />
            刷新
          </Button>
        }
      />

      <div className="grid items-start gap-3 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader
            title="待分类"
            hint={status === "ready" ? `${total} 笔` : undefined}
            action={<Chip>按日期倒序</Chip>}
          />

          {status === "loading" ? (
            <ul aria-hidden>
              {[0, 1, 2, 3].map((index) => (
                <li key={index} className="flex items-center gap-2.5 border-b border-line-soft px-3 py-3">
                  <Skeleton className="h-3.5 w-3.5" />
                  <div className="flex-1">
                    <Skeleton className="h-3 w-2/5" />
                    <Skeleton className="mt-1.5 h-2 w-1/4" />
                  </div>
                  <Skeleton className="h-3 w-16" />
                </li>
              ))}
            </ul>
          ) : null}

          {status === "error" ? (
            <div className="flex flex-col items-center gap-2 px-6 py-10 text-center">
              <p className="text-xs font-semibold text-ink-2">收件箱加载失败</p>
              <p className="text-[10px] text-ink-4">{error}</p>
              <Button variant="ghost" onClick={() => void load()}>
                重试
              </Button>
            </div>
          ) : null}

          {status === "ready" && total === 0 ? (
            <EmptyState
              title="收件箱清空了"
              description="所有交易都已经有分类。新导入且未命中规则的交易会自动出现在这里。"
              action={<ButtonLink href="/ledger">去账本</ButtonLink>}
            />
          ) : null}

          {status === "ready" && total > 0 ? (
            <ul>
              {data?.items.map((item) => {
                const active = item.id === selectedId;
                const isChecked = checked.includes(item.id);
                const income = item.direction === "INCOME";
                return (
                  <li
                    key={item.id}
                    onClick={() => {
                      setSelectedId(item.id);
                      setNotice(null);
                    }}
                    className={cx(
                      "flex cursor-pointer items-center gap-2.5 border-b border-line-soft px-3 py-2.5 last:border-b-0",
                      active ? "bg-sunken" : "hover:bg-canvas",
                    )}
                  >
                    <button
                      type="button"
                      role="checkbox"
                      aria-checked={isChecked}
                      aria-label={`选择 ${item.merchant}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleChecked(item.id);
                      }}
                      className={cx(
                        "flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-[4px] border",
                        isChecked ? "border-coral bg-coral text-ink-on-coral" : "border-line bg-surface",
                      )}
                    >
                      {isChecked ? <Check size={9} /> : null}
                    </button>

                    <span
                      className={cx(
                        "h-1.5 w-1.5 shrink-0 rounded-full",
                        item.status === "duplicate" ? "bg-warn" : "bg-ink-4",
                      )}
                    />

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[10.5px] font-semibold">{item.merchant}</p>
                      <p className="mt-0.5 truncate text-[9px] text-ink-4">
                        {formatTxTime(item.occurredAt)} · {SOURCE_LABEL[item.source]}
                        {item.note ? ` · ${item.note}` : ""}
                      </p>
                    </div>

                    <span
                      className={cx(
                        "nums shrink-0 text-[11px] font-semibold",
                        income && "text-mint-ink",
                      )}
                    >
                      {income ? "+" : "-"}
                      {formatCents(item.amount)}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </Card>

        <div className="flex flex-col gap-3">
          <Card>
            <CardHeader
              title="归类操作"
              hint={selected ? `${SOURCE_LABEL[selected.source]} · ${formatTxTime(selected.occurredAt)}` : undefined}
            />
            <div className="flex flex-col gap-2 px-4 pb-4">
              {selected ? (
                <>
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-[11px] font-semibold">{selected.merchant}</p>
                    <span className="nums shrink-0 text-[11px] font-semibold">
                      {formatCents(selected.amount)}
                    </span>
                  </div>
                  <p className="text-[9px] text-ink-4">无规则命中，归入后会计入当月统计</p>

                  <Divider className="my-1" />

                  <p className="text-[9.5px] text-ink-3">① 指定分类</p>
                  <div className="flex flex-wrap gap-1.5">
                    {categories.map((category) => {
                      const active = category.id === categoryId;
                      return (
                        <button
                          key={category.id}
                          type="button"
                          onClick={() => setCategoryId(category.id)}
                          className={cx(
                            "rounded-pill border px-2.5 py-1 text-[10px]",
                            active
                              ? "border-coral-100 bg-coral-50 font-semibold text-coral-ink"
                              : "border-line bg-surface text-ink-2 hover:bg-sunken",
                          )}
                        >
                          {category.name}
                        </button>
                      );
                    })}
                  </div>

                  <Divider className="my-1" />

                  <label className="flex items-start gap-1.5 text-[9.5px] text-ink-2">
                    <input
                      type="checkbox"
                      checked={withRule}
                      onChange={(event) => setWithRule(event.target.checked)}
                      className="mt-0.5 h-3 w-3 accent-coral"
                    />
                    <span>② 同时为该商户建立关键词规则</span>
                  </label>
                  <input
                    value={keyword}
                    onChange={(event) => setKeyword(event.target.value)}
                    disabled={!withRule}
                    placeholder="关键词"
                    className={cx(
                      "w-full rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] outline-none placeholder:text-ink-4",
                      !withRule && "opacity-50",
                    )}
                  />
                  <p className="text-[9px] text-ink-4">用户规则优先于内置词库，命中后不再进收件箱</p>

                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <Button
                      variant="primary"
                      onClick={() => void classify([selected.id], withRule)}
                      className={cx(!categoryId && "pointer-events-none opacity-50")}
                    >
                      确认归类
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => void classify([selected.id], false)}
                      className={cx(!categoryId && "pointer-events-none opacity-50")}
                    >
                      仅本次
                    </Button>
                  </div>

                  {notice ? (
                    <p
                      className={cx(
                        "mt-1 rounded-sm border px-2.5 py-1.5 text-[9.5px] leading-relaxed",
                        notice.tone === "ok"
                          ? "border-mint-100 bg-mint-50 text-mint-ink"
                          : "border-alert-100 bg-alert-50 text-alert-ink",
                      )}
                    >
                      {notice.text}
                    </p>
                  ) : null}

                  {busy ? <p className="text-[9px] text-ink-4">处理中…</p> : null}
                </>
              ) : (
                <p className="text-[10px] text-ink-4">左侧选一笔，开始归类。</p>
              )}
            </div>
          </Card>

          <Card flat>
            <CardHeader title="批量处理" />
            <div className="flex flex-col gap-2 px-4 pb-4 text-[9.5px]">
              <div className="flex items-center justify-between">
                <span className="text-ink-3">已选 {checked.length} 笔</span>
                <button
                  type="button"
                  onClick={() => setChecked(checked.length === total ? [] : (data?.items.map((item) => item.id) ?? []))}
                  className="text-ink-2 underline decoration-dotted underline-offset-2"
                >
                  {checked.length === total ? "取消全选" : "全选本页"}
                </button>
              </div>
              <Button
                variant="tiny"
                onClick={() => void classify(checked, false)}
                className={cx((checked.length === 0 || !categoryId) && "pointer-events-none opacity-50")}
              >
                批量归类（沿用右侧分类）
              </Button>
              <p className="text-[9px] leading-relaxed text-ink-4">
                批量归类只改分类、不建规则；需要沉淀规则时逐条处理。
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
