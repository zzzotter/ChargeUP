import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { deleteRule } from "@/lib/api/dev-store";

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    deleteRule(id);
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    return jsonError(error);
  }
}
