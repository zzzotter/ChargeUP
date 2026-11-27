"use client";

import Link from "next/link";
import { RotateCcw } from "lucide-react";

import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  EmptyState,
  Skeleton,
  cx,
} from "@/components/ui";
import type { Transaction, TxPage } from "@/lib/api/types";
import { SOURCE_LABEL, STATUS_META, categoryName } from "@/lib/dict";
import { formatCents, formatTxTime } from "@/lib/format";

export type LoadStatus = "loading" | "ready" | "error";

const W_TIME = "w-[86px]";
const W_CAT = "w-[52px]";
const W_SRC = "w-[56px]";
const W_AMT = "w-[76px]";
const W_STAT = "w-[62px]";

export function TransactionTable({
  page,
  status,
  hasFilters,
  errorDetail,
  excluded,
  onRetry,
  onPageChange,
  onClearFilters,
}: {
  page: TxPage | null;
  status: LoadStatus;
  hasFilters: boolean;
  errorDetail?: string | null;
  excluded?: { transfers: number; refunds: number };
  onRetry: () => void;
  onPageChange: (next: number) => void;
  onClearFilters: () => void;
}) {
  const lastPage = page ? Math.max(1, Math.ceil(page.total / page.pageSize)) : 1;
  const excludedText = excluded
    ? `已剔除 ${excluded.transfers} 笔转账 / ${excluded.refunds} 笔退款`
    : "转账与退款不计入支出";

  return (
    <Card className="flex flex-col">
      <CardHeader
        title="流水明细"
        hint={status === "ready" && page ? `共 ${page.total} 条 · ${excludedText}` : excludedText}
        action={
          <>
            <Chip>批量归类</Chip>
            <Chip>导出</Chip>
          </>
        }
      />

      <div className="hidden items-center gap-3 border-b border-line px-4 pb-1.5 text-[9px] text-ink-4 sm:flex">
        <span className={W_TIME}>时间</span>
        <span className="flex-1">商户 / 名称</span>
        <span className={W_CAT}>分类</span>
        <span className={W_SRC}>来源</span>
        <span className={cx(W_AMT, "text-right")}>金额</span>
        <span className={cx(W_STAT, "text-right")}>状态</span>
      </div>

      {status === "loading" ? <SkeletonRows /> : null}

      {status === "error" ? (
        <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <p className="text-xs font-semibold text-ink-2">列表加载失败</p>
          <p className="max-w-[22rem] text-[10px] leading-relaxed text-ink-4">
            {errorDetail ?? "请求超时或服务未就绪。"}
            　可重试，或回头检查后端是否已启动（错误来自真实 HTTP 响应）。
          </p>
          <Button variant="ghost" onClick={onRetry}>
            <RotateCcw size={11} />
            重试
          </Button>
        </div>
      ) : null}

      {status === "ready" && page && page.items.length === 0 ? (
        hasFilters ? (
          <EmptyState
            title="当前条件没有匹配记录"
            description="换个来源、分类或关键词试试；也可以清空筛选回到本月全部流水。"
            action={<Button onClick={onClearFilters}>清除筛选</Button>}
          />
        ) : (
          <EmptyState
            title="这个月还没有流水"
            description="导入支付宝 / 微信账单，或先记一笔；入库后这里会按分类与来源自动归档。"
            action={<ButtonLink href="/import">去导入</ButtonLink>}
          />
        )
      ) : null}

      {status === "ready" && page && page.items.length > 0 ? (
        <ul>
          {page.items.map((row) => (
            <TransactionRow key={row.id} row={row} />
          ))}
        </ul>
      ) : null}

      <footer className="mt-auto flex items-center justify-between gap-2 border-t border-line-soft px-4 py-2 text-[9.5px] text-ink-4">
        <span>
          {status === "ready" && page
            ? `第 ${page.page} / ${lastPage} 页 · 每页 ${page.pageSize} 条`
            : "—"}
        </span>
        <span className="flex items-center gap-1.5">
          <Button
            variant="tiny"
            onClick={() => onPageChange(Math.max(1, (page?.page ?? 1) - 1))}
            className={page && page.page > 1 && status === "ready" ? "" : "opacity-40"}
          >
            上一页
          </Button>
          <Button
            variant="tiny"
            onClick={() => onPageChange(Math.min(lastPage, (page?.page ?? 1) + 1))}
            className={page && page.page < lastPage && status === "ready" ? "" : "opacity-40"}
          >
            下一页
          </Button>
        </span>
      </footer>
    </Card>
  );
}

function TransactionRow({ row }: { row: Transaction }) {
  const category = categoryName(row.categoryId);
  const status = STATUS_META[row.status];
  const income = row.direction === "INCOME";
  const transfer = row.direction === "TRANSFER";

  return (
    <li className="border-b border-line-soft last:border-b-0">
      <Link
        href={`/ledger/${row.id}`}
        className="flex items-center gap-3 px-4 py-2.5 hover:bg-canvas"
      >
        <span className={cx(W_TIME, "hidden shrink-0 text-[10px] text-ink-3 sm:block")}>
          {formatTxTime(row.occurredAt)}
        </span>

        <div className="min-w-0 flex-1">
          <p className="truncate text-[12px] font-semibold">{row.merchant}</p>
          <p className="mt-0.5 truncate text-[9px] text-ink-4 sm:hidden">
            {formatTxTime(row.occurredAt)} · {SOURCE_LABEL[row.source]} · {category ?? "未分类"}
            {row.note ? ` · ${row.note}` : ""}
          </p>
        </div>

        <span className={cx(W_CAT, "hidden sm:block")}>
          {category ? <Chip>{category}</Chip> : <Chip tone="warn">未分类</Chip>}
        </span>

        <span className={cx(W_SRC, "hidden text-[10px] text-ink-4 sm:block")}>
          {SOURCE_LABEL[row.source]}
        </span>

        <span
          className={cx(
            W_AMT,
            "shrink-0 text-right text-[12px] font-semibold nums",
            income && "text-mint-ink",
            transfer && "text-ink-3",
          )}
        >
          {transfer ? formatCents(row.amount) : `${income ? "+" : "-"}${formatCents(row.amount)}`}
        </span>

        <span className={cx(W_STAT, "hidden justify-end sm:flex")}>
          {transfer ? <Chip tone="lilac">转账</Chip> : <Chip tone={status.tone}>{status.label}</Chip>}
        </span>
      </Link>
    </li>
  );
}

function SkeletonRows() {
  return (
    <ul aria-hidden>
      {[0, 1, 2, 3, 4, 5].map((index) => (
        <li
          key={index}
          className="flex items-center gap-3 border-b border-line-soft px-4 py-3 last:border-b-0"
        >
          <Skeleton className={cx(W_TIME, "hidden h-2.5 sm:block")} />
          <div className="flex-1">
            <Skeleton className="h-3 w-2/5" />
            <Skeleton className="mt-1.5 h-2 w-1/4 sm:hidden" />
          </div>
          <Skeleton className={cx(W_CAT, "hidden h-2.5 sm:block")} />
          <Skeleton className={cx(W_SRC, "hidden h-2.5 sm:block")} />
          <Skeleton className={cx(W_AMT, "h-3")} />
          <Skeleton className={cx(W_STAT, "hidden h-2.5 sm:block")} />
        </li>
      ))}
    </ul>
  );
}
