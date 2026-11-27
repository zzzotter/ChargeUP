"use client";

import { usePathname } from "next/navigation";
import { InboxCountProvider, useInboxCount } from "@/components/inbox-count";
import { MobileTabBar } from "@/components/mobile-tab-bar";
import { SideNav } from "@/components/side-nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <InboxCountProvider>
      <AppShellInner>{children}</AppShellInner>
    </InboxCountProvider>
  );
}

function AppShellInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { count } = useInboxCount();

  return (
    <div className="flex min-h-dvh bg-canvas">
      <SideNav pathname={pathname} inboxCount={count} />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* 移动端顶栏：侧栏收起后保留品牌（当前页名由页面标题与底部 Tab 表达） */}
        <header className="sticky top-0 z-20 flex h-12 items-center border-b border-line bg-canvas/90 px-4 backdrop-blur md:hidden">
          <span className="text-sm font-semibold tracking-tight">ledger-guard</span>
        </header>

        <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-4 pb-24 md:px-8 md:py-7 md:pb-10">
          {children}
        </main>
      </div>

      <MobileTabBar pathname={pathname} />
    </div>
  );
}
