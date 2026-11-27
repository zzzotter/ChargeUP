import { NextResponse } from "next/server";

import { testRule } from "@/lib/api/dev-store";

/** 规则干跑：只返回命中结果，不写库 */
export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { name?: string } | null;
  return NextResponse.json(testRule((body?.name ?? "").trim()));
}
