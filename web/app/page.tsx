import { Suspense } from "react";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { Card, Skeleton } from "@/components/ui";

export default function HomePage() {
  return (
    <Suspense fallback={<DashboardFallback />}>
      <DashboardView />
    </Suspense>
  );
}

/** useSearchParams 需要 Suspense 边界；首屏给同构骨架 */
function DashboardFallback() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-[15px] font-bold tracking-tight">仪表盘</h1>
        <p className="mt-1 text-[11px] text-ink-3">加载中…</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <Card key={index} className="p-4">
            <Skeleton className="h-2.5 w-16" />
            <Skeleton className="mt-2 h-6 w-28" />
            <Skeleton className="mt-2 h-2 w-32" />
          </Card>
        ))}
      </div>
      <Card className="p-4">
        <Skeleton className="h-[176px] w-full" />
      </Card>
    </div>
  );
}
