import { NextResponse } from "next/server";

import { jsonError } from "@/lib/api/dev-errors";
import { annotateCsvPreview } from "@/lib/api/dev-store";
import { CsvParseError, decodeCsvBytes, parseBillCsv } from "@/lib/import-csv";

const MAX_SIZE = 10 * 1024 * 1024;

/** 上传 → 解析预览（不写库），返回逐行状态与去重结果 */
export async function POST(request: Request) {
  try {
    const form = await request.formData().catch(() => null);
    const file = form?.get("file");
    if (!(file instanceof File)) {
      return NextResponse.json(
        { code: "VALIDATION_ERROR", message: "请用 multipart/form-data 上传 file 字段" },
        { status: 422 },
      );
    }
    if (file.size > MAX_SIZE) {
      return NextResponse.json(
        { code: "FILE_TOO_LARGE", message: "文件超过 10MB，请拆分后再导入" },
        { status: 422 },
      );
    }
    if (!/\.csv$/i.test(file.name)) {
      return NextResponse.json(
        { code: "UNSUPPORTED_FILE", message: "只支持 .csv 文件（支付宝/微信导出的账单）" },
        { status: 422 },
      );
    }

    const bytes = new Uint8Array(await file.arrayBuffer());
    const text = decodeCsvBytes(bytes);
    const preview = parseBillCsv(text, file.name, file.size);

    return NextResponse.json(annotateCsvPreview(preview));
  } catch (error) {
    if (error instanceof CsvParseError) {
      return NextResponse.json({ code: "CSV_PARSE_ERROR", message: error.message }, { status: 422 });
    }
    return jsonError(error);
  }
}
