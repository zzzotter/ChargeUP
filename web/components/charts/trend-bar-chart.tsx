"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis } from "recharts";

import type { TrendPoint } from "@/lib/api/types";
import { formatCents } from "@/lib/format";

type TooltipProps = {
  active?: boolean;
  payload?: Array<{ value?: number }>;
  label?: string;
};

function BarTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-sm border border-line bg-surface px-2 py-1 shadow-2">
      <p className="text-[9px] text-ink-4">{label}</p>
      <p className="nums text-[11px] font-semibold">{formatCents(payload[0]?.value ?? 0)}</p>
    </div>
  );
}

/** 近 N 个月支出趋势：单系列柱状图，最后一根（当前月）用主强调色 */
export function TrendBarChart({ data }: { data: TrendPoint[] }) {
  const chartData = data.map((point, index) => ({
    label: `${Number(point.month.slice(5, 7))}月`,
    expense: point.expense,
    current: index === data.length - 1,
  }));

  return (
    <div className="h-[176px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 4, bottom: 0, left: 4 }} barCategoryGap="28%">
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 9, fill: "var(--color-ink-4)" }}
            dy={4}
          />
          <Tooltip cursor={{ fill: "var(--color-sunken)" }} content={<BarTooltip />} />
          <Bar dataKey="expense" radius={[6, 6, 3, 3]}>
            {chartData.map((point) => (
              <Cell
                key={point.label}
                fill={point.current ? "var(--color-coral)" : "var(--color-coral-100)"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
