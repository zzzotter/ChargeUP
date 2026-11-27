import { NextResponse } from "next/server";

import { categoryBreakdown } from "@/lib/api/dev-store";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  return NextResponse.json(categoryBreakdown(searchParams.get("month") ?? ""));
}
