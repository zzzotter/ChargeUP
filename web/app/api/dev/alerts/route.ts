import { NextResponse } from "next/server";

import { listAlerts } from "@/lib/api/dev-store";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const month = searchParams.get("month") ?? "";
  const page = Math.max(Number(searchParams.get("page") ?? 1) || 1, 1);
  const pageSize = Math.min(Math.max(Number(searchParams.get("pageSize") ?? 20) || 20, 1), 100);

  return NextResponse.json(listAlerts({ month: month || undefined, page, pageSize }));
}
