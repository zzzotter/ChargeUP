"use client";

import Link from "next/link";
import { isActive, MOBILE_TABS } from "@/lib/nav";

export function MobileTabBar({ pathname }: { pathname: string }) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
      <ul className="flex items-stretch justify-around">
        {MOBILE_TABS.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className={[
                  "flex flex-col items-center gap-1 py-2 text-[10px]",
                  active ? "font-semibold text-ink" : "text-ink-4",
                ].join(" ")}
              >
                <Icon size={16} strokeWidth={1.7} />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
