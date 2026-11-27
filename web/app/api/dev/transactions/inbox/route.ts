import { NextResponse } from "next/server";

import { listInbox } from "@/lib/api/dev-store";

export async function GET() {
  return NextResponse.json(listInbox());
}
