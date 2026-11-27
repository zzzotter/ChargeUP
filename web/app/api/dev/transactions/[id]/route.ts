import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { getTransaction, softDeleteTransaction, updateTransaction } from "@/lib/api/dev-store";
import type { TransactionPatch } from "@/lib/api/types";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    return NextResponse.json(getTransaction(id));
  } catch (error) {
    return jsonError(error);
  }
}

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    const body = (await request.json().catch(() => null)) as TransactionPatch | null;
    if (!body) {
      return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });
    }
    return NextResponse.json(updateTransaction(id, body));
  } catch (error) {
    return jsonError(error);
  }
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await context.params;
    softDeleteTransaction(id);
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    return jsonError(error);
  }
}
