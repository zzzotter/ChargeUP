"use client";

import { useEffect, useState } from "react";

import { Card, CardHeader, Chip, Skeleton } from "@/components/ui";
import { listImports } from "@/lib/api/client";
import type { ImportRecord } from "@/lib/api/types";
import { SOURCE_LABEL } from "@/lib/dict";

function formatTime(iso: string) {
  return iso.slice(5, 16).replace("T", " ");
}

/** 导入历史：读取 /imports，失败时静默降级为空列表 */
export function ImportHistory() {
  const [items, setItems] = useState<ImportRecord[] | null>(null);

  useEffect(() => {
    let alive = true;
    listImports()
      .then((records) => {
        if (alive) setItems(records);
      })
      .catch(() => {
        if (alive) setItems([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <Card>
      <CardHeader title="导入历史" hint="CSV 内容脱敏后才写日志" />
      <div className="px-4 pb-3.5">
        {items === null ? (
          <div className="flex flex-col gap-2 py-1">
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-3 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="py-4 text-[10px] text-ink-4">还没有导入记录，先从上面的入口导入一份账单。</p>
        ) : (
          <ul className="flex flex-col">
            {items.map((item) => (
              <li
                key={item.importId}
                className="flex items-center gap-2 border-b border-line-soft py-2 text-[10px] last:border-b-0"
              >
                <span className="w-[74px] shrink-0 text-[9.5px] text-ink-4">
                  {formatTime(item.createdAt)}
                </span>
                <span className="min-w-0 flex-1 truncate">{item.fileName}</span>
                <Chip>{SOURCE_LABEL[item.source]}</Chip>
                <span className="shrink-0 text-mint-ink">+{item.created}</span>
                <span className="shrink-0 text-ink-4">重复 {item.duplicated}</span>
                <span className={item.failed > 0 ? "shrink-0 text-alert-ink" : "shrink-0 text-ink-4"}>
                  失败 {item.failed}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
