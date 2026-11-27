import { Suspense } from "react";

import { LedgerView } from "@/components/ledger/ledger-view";
import { Card, Skeleton } from "@/components/ui";

export default function LedgerPage() {
  return (
    <Suspense fallback={<LedgerLoading />}>
      <LedgerView />
    </Suspense>
  );
}

/** useSearchParams 需要 Suspense 边界；这里给同构骨架，避免掉成空白 */
function LedgerLoading() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-[15px] font-bold tracking-tight">账本</h1>
        <p className="mt-1 text-[11px] text-ink-3">加载中…</p>
      </div>
      <Card flat className="flex flex-wrap items-center gap-2 px-2.5 py-2">
        <Skeleton className="h-7 w-[118px]" />
        <Skeleton className="h-7 w-[220px]" />
        <Skeleton className="h-7 w-[92px]" />
        <Skeleton className="h-7 flex-1" />
      </Card>
      <Card className="p-4">
        <Skeleton className="mb-3 h-3 w-24" />
        {[0, 1, 2, 3, 4, 5].map((index) => (
          <div key={index} className="flex items-center gap-3 border-b border-line-soft py-3 last:border-b-0">
            <Skeleton className="h-2.5 w-[86px]" />
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3 w-[76px]" />
          </div>
        ))}
      </Card>
    </div>
  );
}
