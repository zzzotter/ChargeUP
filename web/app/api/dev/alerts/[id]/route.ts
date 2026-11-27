import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { markAlertRead } from "@/lib/api/dev-store";

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    const body = (await request.json().catch(() => null)) as { read?: boolean } | null;
    if (!body?.read) {
      return NextResponse.json({ code: "VALIDATION_ERROR", message: "只支持标记已读（read: true）" }, { status: 422 });
    }
    return NextResponse.json(markAlertRead(id));
  } catch (error) {
    return jsonError(error);
  }
}
