import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { batchClassify } from "@/lib/api/dev-store";
import type { BatchClassifyInput } from "@/lib/api/types";

export async function POST(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as Partial<BatchClassifyInput> | null;
    if (!body) return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });

    const result = batchClassify({
      ids: Array.isArray(body.ids) ? body.ids : [],
      categoryId: body.categoryId ?? "",
      createRule: body.createRule,
    });
    return NextResponse.json(result);
  } catch (error) {
    return jsonError(error);
  }
}
