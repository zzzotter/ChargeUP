import { NextResponse } from "next/server";

import { summarizeMonth } from "@/lib/api/dev-store";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  return NextResponse.json(summarizeMonth(searchParams.get("month") ?? ""));
}
