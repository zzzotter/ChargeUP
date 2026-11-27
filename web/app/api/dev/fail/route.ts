import { NextResponse } from "next/server";

import { armFailure } from "@/lib/api/dev-store";

/** 开发桩专用：让下一次 GET /api/dev/transactions 失败一次，用于验证前端错误态 */
export async function POST() {
  armFailure();
  return NextResponse.json({ ok: true });
}
