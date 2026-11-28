import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { commitCsvImport } from "@/lib/api/dev-store";
import type { ImportCommitRow, ImportSource } from "@/lib/api/types";

/** 确认入账：只提交预览里 status=new 的行，服务端再幂等去重一次 */
export async function POST(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as {
      fileName?: string;
      source?: ImportSource;
      rows?: ImportCommitRow[];
      failed?: number;
      duplicated?: number;
    } | null;

    if (!body) {
      return NextResponse.json({ code: "VALIDATION_ERROR", message: "请求体不是合法 JSON" }, { status: 400 });
    }

    const result = commitCsvImport({
      fileName: body.fileName ?? "",
      source: (body.source ?? "ALIPAY") as ImportSource,
      rows: Array.isArray(body.rows) ? body.rows : [],
      failed: body.failed ?? 0,
      duplicated: body.duplicated ?? 0,
    });

    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    return jsonError(error);
  }
}
