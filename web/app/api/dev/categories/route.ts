import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { createCategory, listCategories } from "@/lib/api/dev-store";
import type { CategoryType } from "@/lib/api/types";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type") as CategoryType | null;
  return NextResponse.json(listCategories(type === "EXPENSE" || type === "INCOME" ? type : null));
}

export async function POST(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as { name?: string; type?: CategoryType } | null;
    if (!body) return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });
    const created = createCategory({ name: body.name ?? "", type: (body.type ?? "EXPENSE") as CategoryType });
    return NextResponse.json(created, { status: 201 });
  } catch (error) {
    return jsonError(error);
  }
}
