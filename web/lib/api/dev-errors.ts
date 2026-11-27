import { NextResponse } from "next/server";

import { StoreError } from "@/lib/api/dev-store";

/** 把开发桩的业务异常统一转成 {code,message} 响应 */
export function jsonError(error: unknown) {
  if (error instanceof StoreError) {
    return NextResponse.json(
      { code: error.code, message: error.message, details: error.details },
      { status: error.status },
    );
  }
  console.error("[dev-api]", error);
  return NextResponse.json(
    { code: "INTERNAL_ERROR", message: "开发桩内部错误" },
    { status: 500 },
  );
}
