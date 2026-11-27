import { NextResponse } from "next/server";

import { monthlyTrend } from "@/lib/api/dev-store";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const month = searchParams.get("month") ?? "";
  const months = Number(searchParams.get("months") ?? 6) || 6;
  return NextResponse.json(monthlyTrend(month, months));
}
