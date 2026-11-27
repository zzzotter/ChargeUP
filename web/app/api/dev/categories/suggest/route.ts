import { NextResponse } from "next/server";

import { suggestFor } from "@/lib/api/dev-store";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get("name") ?? "";
  return NextResponse.json(suggestFor(name));
}
