import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { createRule, listRules } from "@/lib/api/dev-store";

export async function GET() {
  return NextResponse.json(listRules());
}

export async function POST(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as
      | { keyword?: string; categoryId?: string }
      | null;
    if (!body) return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });
    const created = createRule({ keyword: body.keyword ?? "", categoryId: body.categoryId ?? "" });
    return NextResponse.json(created, { status: 201 });
  } catch (error) {
    return jsonError(error);
  }
}
