"use client";

import { CalendarDays, ChevronDown, RotateCcw, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { Segmented } from "@/components/segmented";
import { Button, Card } from "@/components/ui";
import type { LedgerFilters, TxDirection, TxSource } from "@/lib/api/types";
import { CATEGORIES, SOURCE_LABEL } from "@/lib/dict";

type SourceFilter = TxSource | "ALL";

const SOURCE_OPTIONS: ReadonlyArray<{ value: SourceFilter; label: string }> = [
  { value: "ALL", label: "全部来源" },
  ...(Object.keys(SOURCE_LABEL) as TxSource[]).map((value) => ({
    value,
    label: SOURCE_LABEL[value],
  })),
];

const DIRECTION_OPTIONS: ReadonlyArray<{ value: TxDirection | "ALL"; label: string }> = [
  { value: "ALL", label: "全部方向" },
  { value: "EXPENSE", label: "支出" },
  { value: "INCOME", label: "收入" },
  { value: "TRANSFER", label: "转账" },
];

export function LedgerFilterBar({
  value,
  onChange,
  onReset,
}: {
  value: LedgerFilters;
  onChange: (patch: Partial<LedgerFilters>) => void;
  onReset: () => void;
}) {
  const [keyword, setKeyword] = useState(value.keyword);

  // 重置时同步输入框
  useEffect(() => {
    setKeyword(value.keyword);
  }, [value.keyword]);

  // 关键词防抖 300ms
  useEffect(() => {
    if (keyword === value.keyword) return;
    const timer = setTimeout(() => onChange({ keyword }), 300);
    return () => clearTimeout(timer);
  }, [keyword, value.keyword, onChange]);

  return (
    <Card flat className="flex flex-wrap items-center gap-2 px-2.5 py-2">
      <label className="flex items-center gap-1.5 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] text-ink-2">
        <CalendarDays size={11} className="text-ink-4" />
        <input
          type="month"
          value={value.month}
          aria-label="月份"
          onChange={(event) => onChange({ month: event.target.value })}
          className="w-[102px] bg-transparent text-[10px] outline-none"
        />
      </label>

      <Segmented
        options={SOURCE_OPTIONS}
        value={value.source}
        onChange={(source) => onChange({ source })}
        size="sm"
      />

      <Segmented
        options={DIRECTION_OPTIONS}
        value={value.direction}
        onChange={(direction) => onChange({ direction })}
        size="sm"
      />

      <label className="relative flex items-center">
        <select
          value={value.categoryId}
          aria-label="分类"
          onChange={(event) => onChange({ categoryId: event.target.value as LedgerFilters["categoryId"] })}
          className="appearance-none rounded-sm border border-line bg-surface py-1.5 pl-2.5 pr-6 text-[10px] text-ink-2 outline-none"
        >
          <option value="ALL">全部分类</option>
          {CATEGORIES.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
          <option value="NONE">未分类</option>
        </select>
        <ChevronDown size={11} className="pointer-events-none absolute right-2 text-ink-4" />
      </label>

      <label className="flex min-w-[110px] flex-1 items-center gap-1.5 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px]">
        <Search size={11} className="text-ink-4" />
        <input
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="商户 / 关键词"
          aria-label="关键词"
          className="w-full bg-transparent text-ink outline-none placeholder:text-ink-4"
        />
      </label>

      <Button variant="tiny" onClick={onReset}>
        <RotateCcw size={11} />
        重置筛选
      </Button>
    </Card>
  );
}
