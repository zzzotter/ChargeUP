import { NextResponse } from "next/server";

import { listImports } from "@/lib/api/dev-store";

export async function GET() {
  return NextResponse.json(listImports());
}
