import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { deleteCategory, renameCategory } from "@/lib/api/dev-store";

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    const body = (await request.json().catch(() => null)) as { name?: string } | null;
    if (!body?.name) {
      return NextResponse.json({ code: "VALIDATION_ERROR", message: "name 不能为空" }, { status: 422 });
    }
    return NextResponse.json(renameCategory(id, body.name));
  } catch (error) {
    return jsonError(error);
  }
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    deleteCategory(id);
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    return jsonError(error);
  }
}
