"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import { Segmented } from "@/components/segmented";
import {
  Button,
  ButtonLink,
  Card,
  CardHeader,
  Chip,
  Divider,
  PageHeader,
  Skeleton,
  cx,
} from "@/components/ui";
import {
  ApiError,
  createCategory,
  createRule,
  deleteCategory,
  deleteRule,
  listCategories,
  listRules,
  renameCategory,
  testRule,
} from "@/lib/api/client";
import type { CategoryRule, CategoryType, CategoryWithCount, RuleTestResult } from "@/lib/api/types";

type Status = "loading" | "ready" | "error";
type Notice = { tone: "ok" | "err"; text: string } | null;

const TONE_DOT: Record<CategoryWithCount["tone"], string> = {
  coral: "bg-coral",
  mint: "bg-mint",
  lilac: "bg-lilac",
  clay: "bg-clay",
  default: "bg-ink-4",
};

const TYPE_OPTIONS: ReadonlyArray<{ value: CategoryType; label: string }> = [
  { value: "EXPENSE", label: "支出" },
  { value: "INCOME", label: "收入" },
];

export function CategoriesView() {
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<CategoryWithCount[]>([]);
  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [type, setType] = useState<CategoryType>("EXPENSE");

  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const [keyword, setKeyword] = useState("");
  const [ruleCategoryId, setRuleCategoryId] = useState("");
  const [testName, setTestName] = useState("");
  const [testResult, setTestResult] = useState<RuleTestResult | null>(null);

  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setStatus("loading");
    try {
      const [cats, nextRules] = await Promise.all([listCategories(), listRules()]);
      setCategories(cats);
      setRules(nextRules);
      setRuleCategoryId((prev) => prev || (cats[0]?.id ?? ""));
      setStatus("ready");
      setError(null);
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : "加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function run<T>(action: () => Promise<T>, success: (result: T) => string) {
    setBusy(true);
    setNotice(null);
    try {
      const result = await action();
      setNotice({ tone: "ok", text: success(result) });
      await load(true);
      return true;
    } catch (err) {
      setNotice({ tone: "err", text: err instanceof ApiError ? err.message : "操作失败" });
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate() {
    const name = newName.trim();
    if (!name) {
      setNotice({ tone: "err", text: "请输入分类名称" });
      return;
    }
    const ok = await run(() => createCategory({ name, type }), (created) => `已新建分类「${created.name}」`);
    if (ok) {
      setNewName("");
      setCreating(false);
    }
  }

  async function handleRename(id: string) {
    const name = editName.trim();
    if (!name) {
      setNotice({ tone: "err", text: "分类名称不能为空" });
      return;
    }
    const ok = await run(() => renameCategory(id, name), (updated) => `已重命名为「${updated.name}」`);
    if (ok) setEditingId(null);
  }

  const visibleCategories = categories.filter((item) => item.type === type);
  const categoryName = (id: string) => categories.find((item) => item.id === id)?.name ?? "—";

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="分类与规则"
        subtitle="分类体系与自动匹配规则 · 双向可维护"
        action={
          <ButtonLink href="/inbox" variant="ghost">
            查看待分类
          </ButtonLink>
        }
      />

      {notice ? (
        <p
          className={cx(
            "rounded-sm border px-3 py-2 text-[10px]",
            notice.tone === "ok"
              ? "border-mint-100 bg-mint-50 text-mint-ink"
              : "border-alert-100 bg-alert-50 text-alert-ink",
          )}
        >
          {notice.text}
        </p>
      ) : null}

      <div className="grid items-start gap-3 lg:grid-cols-[268px_1fr]">
        {/* 左：分类 */}
        <Card>
          <CardHeader
            title="分类"
            action={
              <Button variant="tiny" onClick={() => setCreating((value) => !value)}>
                <Plus size={11} />
                新建
              </Button>
            }
          />
          <div className="flex flex-col gap-2 px-4 pb-3">
            <Segmented options={TYPE_OPTIONS} value={type} onChange={setType} size="sm" className="self-start" />

            {creating ? (
              <div className="flex items-center gap-1.5">
                <input
                  autoFocus
                  value={newName}
                  onChange={(event) => setNewName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void handleCreate();
                  }}
                  placeholder={`新${type === "EXPENSE" ? "支出" : "收入"}分类`}
                  className="min-w-0 flex-1 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] outline-none placeholder:text-ink-4 focus:border-coral"
                />
                <Button variant="tiny" onClick={() => void handleCreate()}>
                  保存
                </Button>
              </div>
            ) : null}

            {status === "loading"
              ? [0, 1, 2].map((index) => (
                  <div key={index} className="flex items-center gap-2 py-1.5">
                    <Skeleton className="h-2 w-2 rounded-full" />
                    <Skeleton className="h-2.5 flex-1" />
                  </div>
                ))
              : null}

            {status === "ready" && visibleCategories.length === 0 ? (
              <p className="py-2 text-[10px] text-ink-4">还没有{type === "EXPENSE" ? "支出" : "收入"}分类</p>
            ) : null}

            <ul className="flex flex-col">
              {visibleCategories.map((category) => (
                <li
                  key={category.id}
                  className="flex items-center gap-2 border-b border-line-soft py-2 last:border-b-0"
                >
                  <span className={cx("h-1.5 w-1.5 shrink-0 rounded-full", TONE_DOT[category.tone])} />

                  {editingId === category.id ? (
                    <>
                      <input
                        autoFocus
                        value={editName}
                        onChange={(event) => setEditName(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") void handleRename(category.id);
                          if (event.key === "Escape") setEditingId(null);
                        }}
                        className="min-w-0 flex-1 rounded-sm border border-line bg-surface px-1.5 py-1 text-[10px] outline-none focus:border-coral"
                      />
                      <button
                        type="button"
                        onClick={() => void handleRename(category.id)}
                        className="text-[9.5px] text-mint-ink underline decoration-dotted underline-offset-2"
                      >
                        保存
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="text-[9.5px] text-ink-4 underline decoration-dotted underline-offset-2"
                      >
                        取消
                      </button>
                    </>
                  ) : (
                    <>
                      <span className="min-w-0 flex-1 truncate text-[11px]">{category.name}</span>
                      <span className="shrink-0 text-[9px] text-ink-4">{category.ruleCount} 条规则</span>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingId(category.id);
                          setEditName(category.name);
                        }}
                        className="shrink-0 text-[9.5px] text-ink-3 underline decoration-dotted underline-offset-2 hover:text-ink-2"
                      >
                        编辑
                      </button>
                      {!category.isBuiltin ? (
                        confirmId === category.id ? (
                          <span className="flex shrink-0 items-center gap-1">
                            <button
                              type="button"
                              onClick={async () => {
                                const ok = await run(
                                  () => deleteCategory(category.id),
                                  () => `已删除分类「${category.name}」`,
                                );
                                setConfirmId(null);
                                if (ok) setEditingId(null);
                              }}
                              className="text-[9.5px] font-semibold text-alert-ink"
                            >
                              确认
                            </button>
                            <button
                              type="button"
                              onClick={() => setConfirmId(null)}
                              className="text-[9.5px] text-ink-4"
                            >
                              取消
                            </button>
                          </span>
                        ) : (
                          <button
                            type="button"
                            aria-label={`删除 ${category.name}`}
                            onClick={() => setConfirmId(category.id)}
                            className="shrink-0 text-ink-4 hover:text-alert-ink"
                          >
                            <Trash2 size={11} />
                          </button>
                        )
                      ) : null}
                    </>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {/* 右：规则 + 测试器 */}
        <div className="flex flex-col gap-3">
          <Card>
            <CardHeader
              title="关键词规则"
              hint="优先级：用户规则 > 内置词库 > 未分类"
              action={<Chip>{rules.length} 条</Chip>}
            />
            <div className="flex flex-col gap-2 px-4 pb-4">
              <div className="flex flex-wrap items-center gap-1.5">
                <input
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && keyword.trim() && ruleCategoryId) {
                      void run(
                        () => createRule({ keyword: keyword.trim(), categoryId: ruleCategoryId }),
                        (created) => `已新增规则「${created.keyword}」`,
                      ).then((ok) => {
                        if (ok) setKeyword("");
                      });
                    }
                  }}
                  placeholder="关键词，例如：星巴克"
                  className="min-w-0 flex-1 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] outline-none placeholder:text-ink-4 focus:border-coral"
                />
                <select
                  value={ruleCategoryId}
                  onChange={(event) => setRuleCategoryId(event.target.value)}
                  aria-label="规则目标分类"
                  className="rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] text-ink-2 outline-none"
                >
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <Button
                  variant="tiny"
                  onClick={() => {
                    if (!keyword.trim() || !ruleCategoryId) return;
                    void run(
                      () => createRule({ keyword: keyword.trim(), categoryId: ruleCategoryId }),
                      (created) => `已新增规则「${created.keyword}」`,
                    ).then((ok) => {
                      if (ok) setKeyword("");
                    });
                  }}
                >
                  添加
                </Button>
              </div>

              <Divider />

              {status === "loading" ? (
                <div className="flex flex-col gap-2 py-1">
                  {[0, 1, 2].map((index) => (
                    <Skeleton key={index} className="h-3 w-2/3" />
                  ))}
                </div>
              ) : null}

              {status === "ready" && rules.length === 0 ? (
                <p className="py-2 text-[10px] text-ink-4">还没有规则，所有交易都会进收件箱</p>
              ) : null}

              <ul className="flex flex-col">
                {rules.map((rule) => (
                  <li
                    key={rule.id}
                    className="flex items-center gap-2 border-b border-line-soft py-1.5 text-[10.5px] last:border-b-0"
                  >
                    <span className="min-w-0 flex-1 truncate">{rule.keyword}</span>
                    <Chip>{categoryName(rule.categoryId)}</Chip>
                    <Chip tone={rule.source === "USER" ? "coral" : "default"}>
                      {rule.source === "USER" ? "用户" : "内置"}
                    </Chip>
                    {rule.source === "USER" ? (
                      <button
                        type="button"
                        aria-label={`删除规则 ${rule.keyword}`}
                        onClick={() =>
                          void run(() => deleteRule(rule.id), () => `已删除规则「${rule.keyword}」`)
                        }
                        className="shrink-0 text-ink-4 hover:text-alert-ink"
                      >
                        <Trash2 size={11} />
                      </button>
                    ) : (
                      <span className="w-[11px] shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </Card>

          <Card flat>
            <CardHeader title="规则测试器" hint="干跑，不写库" />
            <div className="flex flex-col gap-2 px-4 pb-4">
              <div className="flex items-center gap-1.5">
                <input
                  value={testName}
                  onChange={(event) => setTestName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void run(() => testRule(testName.trim()), () => "已试算");
                  }}
                  placeholder="输入商户名称，例如：星巴克臻选（国贸店）"
                  className="min-w-0 flex-1 rounded-sm border border-line bg-surface px-2 py-1.5 text-[10px] outline-none placeholder:text-ink-4 focus:border-coral"
                />
                <Button
                  variant="tiny"
                  onClick={async () => {
                    const name = testName.trim();
                    setBusy(true);
                    setNotice(null);
                    try {
                      const result = await testRule(name);
                      setTestResult(result);
                      setNotice({ tone: "ok", text: "试算完成（未写库）" });
                    } catch (err) {
                      setNotice({ tone: "err", text: err instanceof ApiError ? err.message : "试算失败" });
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  测试
                </Button>
              </div>

              {testResult ? (
                <p className="text-[10px] leading-relaxed">
                  {testResult.categoryId ? (
                    <>
                      命中规则「{testResult.keyword}」→{" "}
                      <span className="font-semibold text-coral-ink">{testResult.categoryName}</span>
                      <span className="text-ink-4">
                        （{testResult.source === "USER" ? "用户规则，优先级 1" : "内置词库"}）
                      </span>
                    </>
                  ) : (
                    <span className="text-warn-ink">
                      未命中任何规则 → 进入待分类收件箱（categoryId = null）
                    </span>
                  )}
                </p>
              ) : (
                <p className="text-[9.5px] text-ink-4">输入商户名试算命中结果，不产生副作用。</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {busy ? <p className="text-[9px] text-ink-4">处理中…</p> : null}
    </div>
  );
}
