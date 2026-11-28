/**
 * 支付宝 / 微信账单 CSV 解析（第 6 天）。
 * 只做「解析 + 逐行判定」，去重与入库在 dev-store 里完成。
 * 后端就绪后这套逻辑搬到 Python 解析器，前端只消费 ImportReport。
 */
import type { CsvPreview, ImportParsedRow, ImportSource, TxDirection } from "@/lib/api/types";

export class CsvParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CsvParseError";
  }
}

/** 优先按 UTF-8 严格解码；失败说明是 GBK（支付宝导出默认） */
export function decodeCsvBytes(bytes: Uint8Array): string {
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    return new TextDecoder("utf-8").decode(bytes.subarray(3));
  }
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    try {
      return new TextDecoder("gbk").decode(bytes);
    } catch {
      return new TextDecoder("utf-8").decode(bytes);
    }
  }
}

/** 支持双引号包裹与字段内逗号（金额常写成 "1,299.00"） */
function splitCsvLine(line: string): string[] {
  const cells: string[] = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (quoted) {
      if (char === '"') {
        if (line[index + 1] === '"') {
          current += '"';
          index += 1;
        } else {
          quoted = false;
        }
      } else {
        current += char;
      }
      continue;
    }
    if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells.map((cell) => cell.trim());
}

const COLUMN_ALIASES = {
  occurredAt: ["交易时间"],
  merchant: ["交易对方", "交易对方名称"],
  note: ["备注", "商品说明", "商品"],
  amount: ["金额", "金额(元)", "金额（元）"],
  flow: ["收/支"],
  externalId: ["交易订单号", "交易单号"],
} as const;

function buildColumnMap(header: string[]) {
  const map: Record<string, number> = {};
  for (const [key, aliases] of Object.entries(COLUMN_ALIASES)) {
    const index = header.findIndex((cell) => (aliases as readonly string[]).includes(cell));
    if (index >= 0) map[key] = index;
  }
  return map;
}

function detectSource(header: string[], headLines: string[]): ImportSource | null {
  if (header.includes("交易订单号")) return "ALIPAY";
  if (header.includes("交易单号")) return "WECHAT";
  const head = headLines.join(" ");
  if (head.includes("支付宝")) return "ALIPAY";
  if (head.includes("微信")) return "WECHAT";
  return null;
}

function parseOccurredAt(raw: string): string | null {
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/);
  if (!match) return null;
  const [, year, month, day, hour, minute, second = "00"] = match;
  const monthNumber = Number(month);
  const dayNumber = Number(day);
  const hourNumber = Number(hour);
  const minuteNumber = Number(minute);
  if (monthNumber < 1 || monthNumber > 12) return null;
  if (dayNumber < 1 || dayNumber > 31) return null;
  if (hourNumber > 23 || minuteNumber > 59) return null;
  return `${year}-${month}-${day}T${hour}:${minute}:${second}+08:00`;
}

/** "¥1,299.00" / "38.00" → 129900（整数分，字符串运算避免浮点误差） */
function parseAmount(raw: string): number | null {
  const cleaned = raw.replace(/[¥￥,\s]/g, "");
  if (!/^\d{1,9}(\.\d{1,2})?$/.test(cleaned)) return null;
  const [yuan, fraction = ""] = cleaned.split(".");
  const cents = Number(yuan) * 100 + Number((fraction + "00").slice(0, 2));
  return cents > 0 ? cents : null;
}

function parseDirection(raw: string): TxDirection | null {
  if (raw === "支出") return "EXPENSE";
  if (raw === "收入") return "INCOME";
  if (raw === "不计收支") return "TRANSFER";
  return null;
}

export function parseBillCsv(text: string, fileName: string, size: number): CsvPreview {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");

  let headerIndex = -1;
  let headerCells: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (!lines[index].trim()) continue;
    const cells = splitCsvLine(lines[index]);
    if (cells.includes("交易时间") && cells.includes("收/支")) {
      headerIndex = index;
      headerCells = cells;
      break;
    }
  }

  if (headerIndex < 0) {
    throw new CsvParseError(
      "没有找到表头行：文件里缺少「交易时间 / 收/支」列，请确认这是支付宝或微信导出的账单 CSV。",
    );
  }

  const columns = buildColumnMap(headerCells);
  const source = detectSource(headerCells, lines.slice(0, 10));
  const rows: ImportParsedRow[] = [];
  let totalRows = 0;

  for (let index = headerIndex + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim()) continue;
    totalRows += 1;

    const cells = splitCsvLine(line);
    const pick = (key: keyof typeof COLUMN_ALIASES) => {
      const columnIndex = columns[key];
      return columnIndex === undefined ? "" : (cells[columnIndex] ?? "");
    };

    const cell = (key: keyof typeof COLUMN_ALIASES) => pick(key);
    const merchant = cell("merchant") || "未识别商户";
    const rawTime = cell("occurredAt");
    const rawAmount = cell("amount");
    const rawFlow = cell("flow");
    const externalId = cell("externalId") || null;
    const note = cell("note") || null;

    const buildRow = (
      status: ImportParsedRow["status"],
      reason: string | undefined,
      parsed: { occurredAt: string | null; amount: number | null; direction: TxDirection | null },
    ): ImportParsedRow => ({
      rowNumber: index + 1,
      occurredAt: parsed.occurredAt,
      merchant,
      note,
      amount: parsed.amount,
      direction: parsed.direction,
      externalId,
      status,
      reason,
    });

    if (cells.length < headerCells.length) {
      rows.push(
        buildRow("failed", `列数不足（${cells.length}/${headerCells.length}）`, {
          occurredAt: null,
          amount: null,
          direction: null,
        }),
      );
      continue;
    }

    const occurredAt = parseOccurredAt(rawTime);
    const amount = parseAmount(rawAmount);
    const direction = parseDirection(rawFlow);

    if (!externalId) {
      rows.push(buildRow("failed", "缺少交易单号", { occurredAt, amount, direction }));
      continue;
    }
    if (!occurredAt) {
      rows.push(buildRow("failed", `交易时间无法解析：${rawTime || "空"}`, { occurredAt, amount, direction }));
      continue;
    }
    if (amount === null) {
      rows.push(buildRow("failed", `金额无法解析：${rawAmount || "空"}`, { occurredAt, amount, direction }));
      continue;
    }
    if (!direction) {
      rows.push(buildRow("failed", `收/支无法识别：${rawFlow || "空"}`, { occurredAt, amount, direction }));
      continue;
    }

    rows.push(buildRow("new", undefined, { occurredAt, amount, direction }));
  }

  return {
    fileName,
    size,
    source,
    skippedHeaderRows: headerIndex,
    totalRows,
    newCount: rows.filter((row) => row.status === "new").length,
    duplicated: 0,
    failed: rows.filter((row) => row.status === "failed").length,
    rows,
  };
}
