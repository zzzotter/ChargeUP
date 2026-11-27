"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Check, ChevronLeft, Trash2, TriangleAlert } from "lucide-react";

import { useInboxCount } from "@/components/inbox-count";
import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  Divider,
  PageHeader,
  Skeleton,
  cx,
} from "@/components/ui";
import {
  ApiError,
  deleteTransaction,
  getTransaction,
  listCategories,
  updateTransaction,
} from "@/lib/api/client";
import type { CategoryWithCount, Transaction } from "@/lib/api/types";
import { SOURCE_LABEL, STATUS_META, categoryName } from "@/lib/dict";
import { formatCents, joinOccurredAt, parseYuanToCents, splitOccurredAt } from "@/lib/format";

type Status = "loading" | "ready" | "error";
type Notice = { tone: "ok" | "err"; text: string } | null;

const FIELD =
  "w-full rounded-sm border border-line bg-surface px-2.5 py-2 text-[12px] text-ink outline-none placeholder:text-ink-4 focus:border-coral focus:ring-2 focus:ring-coral-100";

function fieldClass(error?: string) {
  return error ? `${FIELD} border-alert-100 ring-1 ring-alert-100` : FIELD;
}

export function TransactionDetail({ id }: { id: string }) {
  const router = useRouter();
  const { refresh: refreshBadge } = useInboxCount();

  const [status, setStatus] = useState<Status>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [tx, setTx] = useState<Transaction | null>(null);
  const [categories, setCategories] = useState<CategoryWithCount[]>([]);

  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [note, setNote] = useState("");
  const [direction, setDirection] = useState<"EXPENSE" | "INCOME">("EXPENSE");

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  const hydrate = useCallback((record: Transaction) => {
    setMerchant(record.merchant);
    setAmount((record.amount / 100).toFixed(2));
    setCategoryId(record.categoryId);
    const parts = splitOccurredAt(record.occurredAt);
    setDate(parts.date);
    setTime(parts.time);
    setNote(record.note ?? "");
    setDirection(record.direction === "INCOME" ? "INCOME" : "EXPENSE");
    setErrors({});
  }, []);

  useEffect(() => {
    let alive = true;
    setStatus("loading");
    Promise.all([getTransaction(id), listCategories()])
      .then(([record, cats]) => {
        if (!alive) return;
        setTx(record);
        setCategories(cats);
        hydrate(record);
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (!alive) return;
        setLoadError(error instanceof ApiError ? error.message : "加载失败");
        setStatus("error");
      });
    return () => {
      alive = false;
    };
  }, [id, hydrate]);

  const isTransfer = tx?.direction === "TRANSFER";

  async function handleSave() {
    if (!tx) return;
    const next: Record<string, string> = {};
    if (!merchant.trim()) next.merchant = "请填写商户 / 名称";
    const cents = parseYuanToCents(amount);
    if (cents === null || cents === 0) next.amount = "金额需为大于 0 的数字，最多两位小数";
    if (!date) next.date = "请选择日期";
    setErrors(next);
    if (Object.keys(next).length > 0 || cents === null) return;

    setSaving(true);
    setNotice(null);
    try {
      const updated = await updateTransaction(tx.id, {
        merchant: merchant.trim(),
        amount: cents,
        categoryId,
        occurredAt: joinOccurredAt(date, time),
        note: note.trim() ? note.trim() : null,
        direction: isTransfer ? undefined : direction,
      });
      setTx(updated);
      hydrate(updated);
      setNotice({ tone: "ok", text: "已保存，账本与统计已同步" });
      refreshBadge();
    } catch (error) {
      if (error instanceof ApiError) {
        const firstDetail = error.details?.[0];
        setNotice({
          tone: "err",
          text: firstDetail ? `${firstDetail.reason}（${firstDetail.field}）` : error.message,
        });
      } else {
        setNotice({ tone: "err", text: "保存失败" });
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!tx) return;
    setDeleting(true);
    setNotice(null);
    try {
      await deleteTransaction(tx.id);
      refreshBadge();
      router.push("/ledger");
    } catch (error) {
      setNotice({ tone: "err", text: error instanceof ApiError ? error.message : "删除失败" });
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="交易详情" subtitle="加载中…" />
        <div className="grid items-start gap-3 lg:grid-cols-[1fr_226px]">
          <Card className="p-4">
            <Skeleton className="mb-3 h-3 w-24" />
            <div className="grid gap-3 sm:grid-cols-2">
              {[0, 1, 2, 3, 4, 5].map((index) => (
                <Skeleton key={index} className="h-9" />
              ))}
            </div>
          </Card>
          <Card className="p-4">
            <Skeleton className="h-20" />
          </Card>
        </div>
      </div>
    );
  }

  if (status === "error" || !tx) {
    return (
      <div className="flex flex-col gap-4">
        <PageHeader title="交易详情" subtitle="无法打开这条记录" />
        <Card className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <p className="text-xs font-semibold text-ink-2">{loadError ?? "记录不存在"}</p>
          <p className="max-w-[22rem] text-[10px] leading-relaxed text-ink-4">
            记录可能已被删除（软删除后不再出现在列表与详情），或链接里的编号不正确。
          </p>
          <ButtonLink href="/ledger" variant="ghost" className="mt-1">
            <ChevronLeft size={11} />
            返回账本
          </ButtonLink>
        </Card>
      </div>
    );
  }

  const statusMeta = STATUS_META[tx.status];

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="交易详情"
        subtitle={`${SOURCE_LABEL[tx.source]} · ${tx.occurredAt.slice(5, 16).replace("T", " ")} · ${formatCents(tx.amount)}`}
        action={
          <ButtonLink href="/ledger" variant="ghost">
            <ChevronLeft size={11} />
            返回账本
          </ButtonLink>
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

      <div className="grid items-start gap-3 lg:grid-cols-[1fr_226px]">
        <Card className="p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-[12px] font-semibold">编辑记录</h2>
            <div className="flex items-center gap-1.5">
              <Chip tone="coral">{SOURCE_LABEL[tx.source]}</Chip>
              <Chip>{statusMeta.label}</Chip>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">金额（元）</span>
              <input
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                inputMode="decimal"
                className={`${fieldClass(errors.amount)} nums text-[15px] font-bold`}
              />
              <span className={cx("text-[9px]", errors.amount ? "text-alert-ink" : "text-ink-4")}>
                {errors.amount ?? "保存时转整数分，不用浮点"}
              </span>
            </label>

            <div className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">方向</span>
              <div className="flex gap-0.5 self-start rounded-pill bg-sunken p-0.5">
                {(["EXPENSE", "INCOME"] as const).map((item) => (
                  <button
                    key={item}
                    type="button"
                    disabled={isTransfer}
                    onClick={() => setDirection(item)}
                    className={cx(
                      "rounded-pill px-3 py-1 text-[10px]",
                      direction === item && !isTransfer
                        ? "bg-surface font-semibold text-ink shadow-1"
                        : "text-ink-3",
                      isTransfer && "cursor-not-allowed opacity-50",
                    )}
                  >
                    {item === "EXPENSE" ? "支出" : "收入"}
                  </button>
                ))}
              </div>
              <span className="text-[9px] text-ink-4">
                {isTransfer ? "转账记录的方向不可修改" : "退款/转账由导入识别，不在此处切换"}
              </span>
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">商户 / 名称</span>
              <input
                value={merchant}
                onChange={(event) => setMerchant(event.target.value)}
                className={fieldClass(errors.merchant)}
              />
              {errors.merchant ? (
                <span className="text-[9px] text-alert-ink">{errors.merchant}</span>
              ) : null}
            </label>

            <div className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">分类</span>
              <select
                value={categoryId ?? "NONE"}
                onChange={(event) =>
                  setCategoryId(event.target.value === "NONE" ? null : event.target.value)
                }
                className="w-full rounded-sm border border-line bg-surface px-2.5 py-2 text-[12px] text-ink outline-none focus:border-coral"
              >
                <option value="NONE">未分类（进收件箱）</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
              <span className="text-[9px] text-ink-4">改为未分类会重新进入待分类收件箱</span>
            </div>

            <label className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">日期</span>
              <input
                type="date"
                value={date}
                onChange={(event) => setDate(event.target.value)}
                className={fieldClass(errors.date)}
              />
              {errors.date ? <span className="text-[9px] text-alert-ink">{errors.date}</span> : null}
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-[9.5px] text-ink-3">时间</span>
              <input
                type="time"
                value={time}
                onChange={(event) => setTime(event.target.value)}
                className={fieldClass()}
              />
            </label>

            <label className="flex flex-col gap-1.5 sm:col-span-2">
              <span className="text-[9.5px] text-ink-3">备注</span>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={2}
                placeholder="可选"
                className={`${FIELD} resize-none`}
              />
            </label>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button
              variant="primary"
              onClick={() => void handleSave()}
              className={cx(saving && "pointer-events-none opacity-60")}
            >
              <Check size={12} />
              {saving ? "保存中…" : "保存修改"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => hydrate(tx)}
              className={cx(saving && "pointer-events-none opacity-60")}
            >
              撤销修改
            </Button>

            <span className="ml-auto">
              {confirmDelete ? (
                <span className="flex items-center gap-1.5">
                  <span className="text-[9.5px] text-alert-ink">确认移入回收？</span>
                  <Button
                    variant="tiny"
                    onClick={() => void handleDelete()}
                    className={cx(deleting && "pointer-events-none opacity-50")}
                  >
                    {deleting ? "处理中…" : "确认"}
                  </Button>
                  <Button variant="tiny" onClick={() => setConfirmDelete(false)}>
                    取消
                  </Button>
                </span>
              ) : (
                <Button variant="tiny" onClick={() => setConfirmDelete(true)}>
                  <Trash2 size={11} />
                  移入回收（软删除）
                </Button>
              )}
            </span>
          </div>
        </Card>

        <div className="flex flex-col gap-3">
          <Card>
            <CardHeader title="数据血缘" />
            <div className="flex flex-col gap-1.5 px-4 pb-3.5 text-[9.5px]">
              <div className="flex items-center justify-between gap-2">
                <span className="text-ink-4">来源</span>
                <span>{SOURCE_LABEL[tx.source]}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-ink-4">方向</span>
                <span>
                  {tx.direction === "TRANSFER" ? "转账（不计支出）" : tx.direction === "INCOME" ? "收入" : "支出"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-ink-4">状态</span>
                <span>{statusMeta.label}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-ink-4">内部 ID</span>
                <span className="font-mono text-[9px]">{tx.id}</span>
              </div>

              <Divider className="my-1" />

              <div className="text-ink-4">退款关联</div>
              {tx.refundOfTransactionId ? (
                <Link
                  href={`/ledger/${tx.refundOfTransactionId}`}
                  className="text-coral-ink underline decoration-dotted underline-offset-2"
                >
                  关联原始交易 {tx.refundOfTransactionId}
                </Link>
              ) : tx.status === "refund" ? (
                <span className="text-warn-ink">未关联到原始交易（可能超出 7 天窗口）</span>
              ) : (
                <span className="text-ink-3">无</span>
              )}

              {tx.updatedAt ? (
                <>
                  <Divider className="my-1" />
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-ink-4">最近编辑</span>
                    <span>{tx.updatedAt.slice(0, 16).replace("T", " ")}</span>
                  </div>
                </>
              ) : null}
            </div>
          </Card>

          <Card flat>
            <CardHeader title="数据约束" />
            <ul className="flex flex-col gap-1.5 px-4 pb-4 text-[9.5px] leading-relaxed text-ink-4">
              <li>· 金额以整数「分」存储，展示时统一格式化。</li>
              <li>· 来源与方向由导入/识别写入，手工编辑不改这两个字段。</li>
              <li>· 删除为软删除（写 deleted_at），记录不可物理删除。</li>
              <li>· 退款行不计入收入，转账行不计入支出。</li>
            </ul>
          </Card>

          {tx.status === "duplicate" ? (
            <p className="flex items-start gap-1.5 rounded-sm border border-warn-100 bg-warn-50 px-3 py-2 text-[9.5px] leading-relaxed text-warn-ink">
              <TriangleAlert size={11} className="mt-0.5 shrink-0" />
              该记录被标记为疑似重复（同日同额同商户），请核对后再决定保留或删除。
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
