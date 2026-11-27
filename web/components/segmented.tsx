"use client";

import { cx } from "@/components/ui";

/** 分段控件：筛选来源、收支方向、视图状态都用它 */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
  className,
  size = "md",
}: {
  options: ReadonlyArray<{ value: T; label: string }>;
  value: T;
  onChange: (next: T) => void;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <div
      role="tablist"
      className={cx("flex flex-wrap items-center gap-0.5 rounded-pill bg-sunken p-0.5", className)}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            role="tab"
            type="button"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={cx(
              "rounded-pill transition-colors",
              size === "sm" ? "px-2 py-0.5 text-[9.5px]" : "px-2.5 py-1 text-[10px]",
              active
                ? "bg-surface font-semibold text-ink shadow-1"
                : "text-ink-3 hover:text-ink-2",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
