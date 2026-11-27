"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { listInbox } from "@/lib/api/client";

type InboxCountValue = {
  count: number | null;
  /** 归类/导入后调用，刷新侧栏角标 */
  refresh: () => void;
};

const InboxCountContext = createContext<InboxCountValue>({ count: null, refresh: () => {} });

export function InboxCountProvider({ children }: { children: React.ReactNode }) {
  const [count, setCount] = useState<number | null>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    listInbox()
      .then((result) => {
        if (alive) setCount(result.total);
      })
      .catch(() => {
        if (alive) setCount(null);
      });
    return () => {
      alive = false;
    };
  }, [nonce]);

  const refresh = useCallback(() => setNonce((value) => value + 1), []);
  const value = useMemo(() => ({ count, refresh }), [count, refresh]);

  return <InboxCountContext.Provider value={value}>{children}</InboxCountContext.Provider>;
}

export function useInboxCount() {
  return useContext(InboxCountContext);
}
