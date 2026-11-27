import { NextResponse } from "next/server";

import { consumeFailure, insertTransaction, queryTransactions } from "@/lib/api/dev-store";
import type { ApiErrorBody, NewTransactionInput, TxSource } from "@/lib/api/types";

const SOURCES: TxSource[] = ["ALIPAY", "WECHAT", "SCREENSHOT", "MANUAL"];
const DIRECTIONS = ["EXPENSE", "INCOME"];
const FILTER_DIRECTIONS = ["ALL", "EXPENSE", "INCOME", "TRANSFER"];

export async function GET(request: Request) {
  if (consumeFailure()) {
    return NextResponse.json(
      { code: "INTERNAL_ERROR", message: "开发桩：模拟的服务器错误" },
      { status: 500 },
    );
  }

  const { searchParams } = new URL(request.url);
  const rawSource = searchParams.get("source") ?? "ALL";
  const rawDirection = searchParams.get("direction") ?? "ALL";
  const page = Math.max(Number(searchParams.get("page") ?? 1) || 1, 1);
  const pageSize = Math.min(Math.max(Number(searchParams.get("pageSize") ?? 10) || 10, 1), 100);

  const result = queryTransactions({
    month: searchParams.get("month") ?? "",
    source: SOURCES.includes(rawSource as TxSource) ? (rawSource as TxSource) : "ALL",
    direction: FILTER_DIRECTIONS.includes(rawDirection)
      ? (rawDirection as "ALL" | "EXPENSE" | "INCOME" | "TRANSFER")
      : "ALL",
    categoryId: (searchParams.get("categoryId") ?? "ALL") as "ALL" | "NONE" | string,
    keyword: searchParams.get("q") ?? "",
    page,
    pageSize,
  });

  return NextResponse.json(result);
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as Partial<NewTransactionInput> | null;
  if (!body) {
    return NextResponse.json<ApiErrorBody>(
      { code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" },
      { status: 400 },
    );
  }

  const details: Array<{ field: string; reason: string }> = [];

  if (typeof body.merchant !== "string" || body.merchant.trim() === "") {
    details.push({ field: "merchant", reason: "不能为空" });
  } else if (body.merchant.trim().length > 60) {
    details.push({ field: "merchant", reason: "不能超过 60 字" });
  }

  if (typeof body.amount !== "number" || !Number.isInteger(body.amount)) {
    details.push({ field: "amount", reason: "必须是整数「分」" });
  } else if (body.amount <= 0) {
    details.push({ field: "amount", reason: "必须大于 0" });
  }

  if (!body.direction || !DIRECTIONS.includes(body.direction)) {
    details.push({ field: "direction", reason: "必须是 EXPENSE 或 INCOME" });
  }

  if (
    typeof body.occurredAt !== "string" ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)$/.test(body.occurredAt)
  ) {
    details.push({ field: "occurredAt", reason: "需为带时区的 ISO 8601 时间" });
  }

  if (body.categoryId !== null && body.categoryId !== undefined && typeof body.categoryId !== "string") {
    details.push({ field: "categoryId", reason: "需为字符串或 null" });
  }

  if (details.length > 0) {
    return NextResponse.json<ApiErrorBody>(
      { code: "VALIDATION_ERROR", message: "字段校验失败", details },
      { status: 422 },
    );
  }

  const created = insertTransaction({
    merchant: body.merchant as string,
    amount: body.amount as number,
    direction: body.direction as "EXPENSE" | "INCOME",
    occurredAt: body.occurredAt as string,
    categoryId: (body.categoryId ?? null) as string | null,
    note: body.note ?? null,
  });

  return NextResponse.json(created, { status: 201 });
}
