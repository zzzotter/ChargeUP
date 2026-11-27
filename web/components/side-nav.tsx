"use client";

import Link from "next/link";
import { isActive, NAV_GROUPS } from "@/lib/nav";

export function SideNav({
  pathname,
  inboxCount,
}: {
  pathname: string;
  inboxCount?: number | null;
}) {
  return (
    <aside className="hidden w-[232px] shrink-0 flex-col border-r border-line bg-surface/60 md:flex">
      <div className="flex items-center gap-2 px-5 pb-3 pt-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-coral-50 text-coral">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round">
            <rect x="3.6" y="6.4" width="16.8" height="12" rx="2.4" />
            <path d="M3.6 10h16.8" />
          </svg>
        </span>
        <span className="text-sm font-semibold tracking-tight">
          ledger-guard
          <span className="block text-[10px] font-normal text-ink-4">手账式记账 · 消费干预</span>
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="mb-1">
            <p className="px-3 pb-1 pt-3 text-[10px] tracking-[0.14em] text-ink-4">{group.title}</p>
            {group.items.map((item) => {
              const active = isActive(pathname, item.href);
              const Icon = item.icon;
              const badgeValue =
                item.badgeKey === "inbox" && inboxCount && inboxCount > 0 ? inboxCount : null;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "flex items-center gap-2 rounded-sm px-3 py-2 text-xs transition-colors",
                    active
                      ? "bg-coral-50 font-semibold text-ink ring-1 ring-coral-100"
                      : "text-ink-2 hover:bg-sunken",
                  ].join(" ")}
                >
                  <Icon size={14} strokeWidth={1.7} />
                  <span>{item.label}</span>
                  {badgeValue ? (
                    <span className="ml-auto rounded-pill border border-line bg-sunken px-1.5 text-[9px] text-ink-2">
                      {badgeValue > 99 ? "99+" : badgeValue}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <p className="border-t border-line-soft px-4 py-3 text-[9px] leading-relaxed text-ink-4">
        金额均以「分」入库
        <br />
        展示层统一格式化
      </p>
    </aside>
  );
}
