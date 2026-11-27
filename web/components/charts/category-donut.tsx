"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { CategorySlice } from "@/lib/api/types";
import { CATEGORIES } from "@/lib/dict";
import { formatCents } from "@/lib/format";

const TONE_COLOR: Record<string, string> = {
  coral: "var(--color-coral)",
  mint: "var(--color-mint)",
  lilac: "var(--color-lilac)",
  clay: "var(--color-clay)",
  default: "var(--color-line)",
};

export function sliceColor(categoryId: string | null): string {
  if (!categoryId) return "var(--color-ink-4)";
  const tone = CATEGORIES.find((item) => item.id === categoryId)?.tone ?? "default";
  return TONE_COLOR[tone];
}

type TooltipProps = {
  active?: boolean;
  payload?: Array<{ payload?: CategorySlice }>;
};

function SliceTooltip({ active, payload }: TooltipProps) {
  const slice = payload?.[0]?.payload;
  if (!active || !slice) return null;
  return (
    <div className="rounded-sm border border-line bg-surface px-2 py-1 shadow-2">
      <p className="text-[9px] text-ink-4">{slice.name}</p>
      <p className="nums text-[11px] font-semibold">{formatCents(slice.amount)}</p>
      <p className="text-[9px] text-ink-4">{Math.round(slice.ratio * 100)}%</p>
    </div>
  );
}

/** 分类支出分布：环形图，颜色复用全局语义色（分类色映射由 dict 决定） */
export function CategoryDonut({ data, total }: { data: CategorySlice[]; total: number }) {
  return (
    <div className="relative h-[176px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="amount"
            nameKey="name"
            innerRadius={54}
            outerRadius={74}
            paddingAngle={2}
            stroke="none"
          >
            {data.map((slice) => (
              <Cell key={slice.categoryId ?? "none"} fill={sliceColor(slice.categoryId)} />
            ))}
          </Pie>
          <Tooltip content={<SliceTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[9px] text-ink-4">支出合计</span>
        <span className="nums text-[14px] font-bold">{formatCents(total)}</span>
      </div>
    </div>
  );
}
