"use client";

import Link from "next/link";
import { useCallback, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  Check,
  Download,
  FileSpreadsheet,
  RefreshCw,
  TriangleAlert,
  Upload,
} from "lucide-react";

import { useInboxCount } from "@/components/inbox-count";
import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  Skeleton,
  cx,
} from "@/components/ui";
import { ApiError, commitCsvImport, previewCsv } from "@/lib/api/client";
import type { CsvPreview, ImportResult } from "@/lib/api/types";
import { SOURCE_LABEL } from "@/lib/dict";
import { formatCents } from "@/lib/format";

type Step = "pick" | "preview" | "done";
type Busy = null | "parsing" | "committing";
type RowFilter = "all" | "new" | "duplicate" | "failed";

const MAX_SIZE = 10 * 1024 * 1024;
const STEPS = ["选择文件", "解析预览", "确认入账"] as const;

const SAMPLES = [
  { name: "alipay-2026-11.csv", label: "支付宝样例", hint: "GBK · 24 行表头" },
  { name: "wechat-2026-11.csv", label: "微信样例", hint: "UTF-8 · 16 行表头" },
  { name: "no-header.csv", label: "坏文件", hint: "验证报错提示" },
];

function csvCell(value: string | number): string {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function statusChip(status: "new" | "duplicate" | "failed") {
  if (status === "new") return <Chip tone="mint">新建</Chip>;
  if (status === "duplicate") return <Chip>跳过·重复</Chip>;
  return <Chip tone="alert">解析失败</Chip>;
}

export function CsvImportView() {
  const { refresh: refreshInbox } = useInboxCount();
  const inputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>("pick");
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<CsvPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [filter, setFilter] = useState<RowFilter>("all");
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    if (!/\.csv$/i.test(file.name)) {
      setError("只支持 .csv 文件（支付宝/微信导出的账单）");
      return;
    }
    if (file.size > MAX_SIZE) {
      setError("文件超过 10MB，请拆分后再导入");
      return;
    }

    setBusy("parsing");
    setError(null);
    try {
      const next = await previewCsv(file);
      setPreview(next);
      setFilter("all");
      setStep("preview");
    } catch (err) {
      setPreview(null);
      setError(err instanceof ApiError ? err.message : "解析失败，请检查文件");
    } finally {
      setBusy(null);
    }
  }, []);

  const loadSample = useCallback(
    async (name: string) => {
      setBusy("parsing");
      setError(null);
      try {
        const response = await fetch(`/samples/${name}`);
        if (!response.ok) throw new Error("sample missing");
        const blob = await response.blob();
        await handleFile(new File([blob], name, { type: "text/csv" }));
      } catch {
        setError("样例文件加载失败");
        setBusy(null);
      }
    },
    [handleFile],
  );

  const confirmImport = useCallback(async () => {
    if (!preview?.source) {
      setError("无法识别账单来源（支付宝 / 微信），请确认文件是否完整");
      return;
    }
    const rows = preview.rows
      .filter((row) => row.status === "new" && row.occurredAt && row.amount !== null && row.direction && row.externalId)
      .map((row) => ({
        occurredAt: row.occurredAt as string,
        merchant: row.merchant,
        note: row.note,
        amount: row.amount as number,
        direction: row.direction as "EXPENSE" | "INCOME" | "TRANSFER",
        externalId: row.externalId as string,
      }));

    if (rows.length === 0) return;

    setBusy("committing");
    setError(null);
    try {
      const record = await commitCsvImport({
        fileName: preview.fileName,
        source: preview.source,
        rows,
        failed: preview.failed,
        duplicated: preview.duplicated,
      });
      setResult(record);
      setStep("done");
      refreshInbox();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "入账失败，请重试");
    } finally {
      setBusy(null);
    }
  }, [preview, refreshInbox]);

  function reset() {
    setStep("pick");
    setPreview(null);
    setResult(null);
    setError(null);
    setFilter("all");
    if (inputRef.current) inputRef.current.value = "";
  }

  function exportFailures() {
    if (!preview) return;
    const failed = preview.rows.filter((row) => row.status === "failed");
    const lines = [
      "行号,交易时间,商户,金额（元）,失败原因",
      ...failed.map((row) =>
        [
          row.rowNumber,
          row.occurredAt ?? "",
          row.merchant,
          row.amount === null ? "" : (row.amount / 100).toFixed(2),
          row.reason ?? "",
        ]
          .map(csvCell)
          .join(","),
      ),
    ];
    const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `导入失败行-${preview.fileName.replace(/\.csv$/i, "")}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const filteredRows = useMemo(() => {
    if (!preview) return [];
    if (filter === "all") return preview.rows;
    return preview.rows.filter((row) => row.status === filter);
  }, [preview, filter]);

  const stepIndex = step === "pick" ? 0 : step === "preview" ? 1 : 2;

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[15px] font-bold tracking-tight">CSV 账单导入</h1>
          <p className="mt-1 text-[11px] text-ink-3">
            支付宝 / 微信导出文件 · 自动跳表头、处理 GBK、按（来源 + 交易单号）幂等去重
          </p>
        </div>
        <Link
          href="/import"
          className="inline-flex items-center gap-1 text-[10px] text-ink-2 underline decoration-dotted underline-offset-2"
        >
          <ArrowLeft size={11} />
          返回导入中心
        </Link>
      </header>

      <div className="flex flex-wrap items-center gap-2 rounded-sm border border-line bg-surface px-3 py-2">
        {STEPS.map((label, index) => {
          const done = index < stepIndex;
          const active = index === stepIndex;
          return (
            <span key={label} className="flex items-center gap-1.5">
              <span
                className={cx(
                  "flex h-4 w-4 items-center justify-center rounded-full text-[9px]",
                  done
                    ? "bg-mint-50 text-mint-ink ring-1 ring-mint-100"
                    : active
                      ? "bg-coral text-ink-on-coral"
                      : "bg-sunken text-ink-4",
                )}
              >
                {done ? <Check size={9} /> : index + 1}
              </span>
              <span className={cx("text-[9.5px]", active ? "font-semibold text-ink" : "text-ink-4")}>
                {label}
              </span>
              {index < STEPS.length - 1 ? <span className="mx-1 h-px w-6 bg-line" /> : null}
            </span>
          );
        })}
        {preview ? (
          <span className="ml-auto flex items-center gap-1.5">
            <Chip>{preview.fileName}</Chip>
            {preview.source ? <Chip tone="coral">{SOURCE_LABEL[preview.source]}</Chip> : null}
          </span>
        ) : null}
      </div>

      {error ? (
        <p className="flex items-start gap-1.5 rounded-sm border border-alert-100 bg-alert-50 px-3 py-2 text-[10px] leading-relaxed text-alert-ink">
          <TriangleAlert size={12} className="mt-0.5 shrink-0" />
          {error}
        </p>
      ) : null}

      {step === "pick" ? (
        <Card className="p-4">
          <CardHeader
            title="选择账单文件"
            hint="≤10MB，单次 1000 条以内解析并入库 ≤3s"
            action={<Chip>CSV</Chip>}
          />

          <label
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              const file = event.dataTransfer.files?.[0];
              if (file) void handleFile(file);
            }}
            className={cx(
              "mx-4 flex cursor-pointer flex-col items-center gap-1.5 rounded-md border border-dashed px-6 py-10 text-center transition-colors",
              dragging ? "border-coral bg-coral-50" : "border-line bg-canvas hover:bg-sunken/60",
              busy === "parsing" && "pointer-events-none opacity-60",
            )}
          >
            <Upload size={18} className="text-ink-4" />
            <span className="text-[11px] font-semibold">
              {busy === "parsing" ? "解析中…" : "拖拽 CSV 到这里，或点击选择文件"}
            </span>
            <span className="text-[9.5px] text-ink-4">
              支付宝（GBK，24 行表头）· 微信（UTF-8，16 行表头）
            </span>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void handleFile(file);
              }}
            />
          </label>

          <div className="flex flex-wrap items-center gap-2 px-4 pb-4 pt-3">
            <span className="text-[9.5px] text-ink-4">没有文件？用内置样例跑一遍：</span>
            {SAMPLES.map((sample) => (
              <Button
                key={sample.name}
                variant="tiny"
                onClick={() => void loadSample(sample.name)}
                className={cx(busy === "parsing" && "pointer-events-none opacity-60")}
              >
                <FileSpreadsheet size={11} />
                {sample.label}
                <span className="text-ink-4">{sample.hint}</span>
              </Button>
            ))}
          </div>

          {busy === "parsing" ? (
            <div className="flex flex-col gap-2 px-4 pb-4">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ) : null}
        </Card>
      ) : null}

      {step === "preview" && preview ? (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Card className="p-3">
              <p className="text-[9.5px] text-ink-3">可入账</p>
              <p className="nums text-[18px] font-bold text-mint-ink">{preview.newCount}</p>
            </Card>
            <Card className="p-3">
              <p className="text-[9.5px] text-ink-3">重复（跳过）</p>
              <p className="nums text-[18px] font-bold">{preview.duplicated}</p>
            </Card>
            <Card className="p-3">
              <p className="text-[9.5px] text-ink-3">解析失败</p>
              <p
                className={cx(
                  "nums text-[18px] font-bold",
                  preview.failed > 0 ? "text-alert-ink" : "text-ink-4",
                )}
              >
                {preview.failed}
              </p>
            </Card>
            <Card className="p-3">
              <p className="text-[9.5px] text-ink-3">数据行数</p>
              <p className="nums text-[18px] font-bold">{preview.totalRows}</p>
              <p className="text-[8.5px] text-ink-4">已跳过 {preview.skippedHeaderRows} 行表头</p>
            </Card>
          </div>

          <Card>
            <CardHeader
              title="解析结果"
              hint={`共 ${preview.rows.length} 行`}
              action={
                <span className="flex flex-wrap items-center gap-1">
                  {(
                    [
                      ["all", `全部 ${preview.rows.length}`],
                      ["new", `仅新建 ${preview.newCount}`],
                      ["duplicate", `仅重复 ${preview.duplicated}`],
                      ["failed", `仅失败 ${preview.failed}`],
                    ] as Array<[RowFilter, string]>
                  ).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setFilter(value)}
                      className={cx(
                        "rounded-pill px-2 py-0.5 text-[9.5px]",
                        filter === value
                          ? "bg-coral-50 font-semibold text-coral-ink ring-1 ring-coral-100"
                          : "text-ink-3 hover:bg-sunken",
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </span>
              }
            />

            <div className="hidden items-center gap-2 border-b border-line px-4 pb-1.5 text-[9px] text-ink-4 sm:flex">
              <span className="w-8">行号</span>
              <span className="w-[92px]">交易时间</span>
              <span className="flex-1">商户 / 名称</span>
              <span className="w-[80px] text-right">金额</span>
              <span className="w-[86px] text-right">状态</span>
            </div>

            <ul className="max-h-[320px] overflow-y-auto">
              {filteredRows.length === 0 ? (
                <li className="px-4 py-6 text-center text-[10px] text-ink-4">该分组没有记录</li>
              ) : null}
              {filteredRows.map((row) => (
                <li
                  key={`${row.rowNumber}-${row.externalId ?? "x"}`}
                  className="flex items-center gap-2 border-b border-line-soft px-4 py-1.5 text-[10px] last:border-b-0"
                >
                  <span className="hidden w-8 shrink-0 text-ink-4 sm:block">{row.rowNumber}</span>
                  <span className="hidden w-[92px] shrink-0 text-ink-3 sm:block">
                    {row.occurredAt ? row.occurredAt.slice(5, 16).replace("T", " ") : "—"}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate">{row.merchant}</span>
                    <span className="block truncate text-[9px] text-ink-4 sm:hidden">
                      L{row.rowNumber} ·{" "}
                      {row.occurredAt ? row.occurredAt.slice(5, 16).replace("T", " ") : "时间缺失"}
                      {row.status !== "new" && row.reason ? ` · ${row.reason}` : ""}
                    </span>
                    {row.status === "failed" && row.reason ? (
                      <span className="hidden truncate text-[9px] text-alert-ink sm:block">
                        {row.reason}
                      </span>
                    ) : row.status === "duplicate" && row.reason ? (
                      <span className="hidden truncate text-[9px] text-ink-4 sm:block">
                        {row.reason}
                      </span>
                    ) : null}
                  </span>
                  <span className="nums w-[76px] shrink-0 text-right">
                    {row.amount === null ? "—" : formatCents(row.amount)}
                  </span>
                  <span className="w-[78px] shrink-0 text-right">{statusChip(row.status)}</span>
                </li>
              ))}
            </ul>

            <p className="px-4 pt-1.5 text-[8.5px] leading-relaxed text-ink-4">
              行号为文件中的实际行号（含表头），便于对照原始文件排查。
            </p>

            <div className="flex flex-wrap items-center gap-2 border-t border-line-soft px-4 py-2.5">
              <span className="text-[9.5px] text-ink-4">
                {preview.newCount > 0 ? `将写入 ${preview.newCount} 条；` : ""}
                {preview.duplicated} 条重复跳过、{preview.failed} 条失败不入库
              </span>
              <span className="ml-auto flex items-center gap-1.5">
                <Button variant="ghost" onClick={reset}>
                  <RefreshCw size={11} />
                  重新选择
                </Button>
                <Button
                  variant="primary"
                  onClick={() => void confirmImport()}
                  className={cx(
                    (preview.newCount === 0 || busy === "committing") &&
                      "pointer-events-none opacity-50",
                  )}
                >
                  <Check size={12} />
                  {busy === "committing" ? "入账中…" : `确认入账 ${preview.newCount} 条`}
                </Button>
              </span>
            </div>
          </Card>

          {preview.failed > 0 ? (
            <p className="rounded-sm border border-dashed border-line bg-canvas px-3 py-2 text-[9.5px] leading-relaxed text-ink-4">
              失败行不会阻塞其余记录入库；可入账后再导出失败行核对，或修正文件后重新上传。
            </p>
          ) : null}
        </div>
      ) : null}

      {step === "done" && result ? (
        <Card className="flex flex-col items-center gap-2 px-6 py-10 text-center">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-mint-50 text-mint-ink">
            <Check size={18} />
          </span>
          <p className="text-[14px] font-semibold">已入账 {result.created} 条</p>
          <p className="text-[10px] text-ink-4">
            {result.fileName} · {SOURCE_LABEL[result.source]} · 跳过重复 {result.duplicated} · 解析失败{" "}
            {result.failed}
          </p>
          <p className="max-w-[26rem] text-[9.5px] leading-relaxed text-ink-4">
            命中关键词规则的记录已自动分类；未命中的进入待分类收件箱，可逐条归类或沉淀规则。
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
            <ButtonLink href="/ledger">查看账本</ButtonLink>
            <ButtonLink href="/inbox" variant="ghost">
              去收件箱
            </ButtonLink>
            <Button variant="ghost" onClick={reset}>
              再导入一份
            </Button>
            {result.failed > 0 && preview ? (
              <Button variant="ghost" onClick={exportFailures}>
                <Download size={11} />
                导出失败行
              </Button>
            ) : null}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
