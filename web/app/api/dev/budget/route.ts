import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { getBudget, saveBudget } from "@/lib/api/dev-store";
import type { Budget } from "@/lib/api/types";

export async function GET() {
  return NextResponse.json(getBudget());
}

export async function PUT(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as Partial<Budget> | null;
    if (!body) {
      return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });
    }
    return NextResponse.json(saveBudget(body));
  } catch (error) {
    return jsonError(error);
  }
}
