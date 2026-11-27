"""微信/支付宝账单解析器（纯领域逻辑，独立于入库 API）。

支持两种导出格式：
- 支付宝 .csv（GBK/GB18030）与微信 .csv；
- 微信/支付宝 .xlsx（按文件头 zip 魔数识别，不依赖扩展名）。

覆盖 SRS F-P0-01 的坏账单要求：
- 跳过头部非数据行（支付宝 24 行、微信 16 行由「表头识别」自适应处理，不写死行号）；
- GBK / GB18030 编码与特殊符号清洗；
- 空行、缺列、乱码、金额/时间异常均不崩溃，转成可展示的拒识记录。
"""

from __future__ import annotations

import csv
import io
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.domain.enums import Direction, ImportRowStatus, Source
from app.domain.money import InvalidAmountError, parse_amount_to_cents
from app.domain.redaction import redact_text
from app.domain.time import as_utc

MAX_ISSUES = 50
_ENCODINGS = ("utf-8-sig", "gb18030")


def normalize_header(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\ufeff", "").replace('"', "").replace("'", "")
    return "".join(text.split()).lower()


# 别名按优先级排列（越靠前越优先）
_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("occurred_at", ("交易时间", "交易创建时间", "付款时间", "支付时间", "时间")),
    ("amount", ("金额(元)", "金额", "发生金额", "金额元")),
    ("merchant", ("交易对方", "商户全称", "对方", "交易对象")),
    ("description", ("商品", "商品说明", "商品名称", "备注")),
    ("direction", ("收/支", "收支", "资金流向", "收支类型")),
    ("external_id", ("交易单号", "交易号", "交易订单号", "订单号")),
    ("trade_type", ("交易类型", "类型")),
)

_TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y年%m月%d日 %H:%M:%S",
    "%Y年%m月%d日 %H:%M",
    "%Y年%m月%d日",
)

_SEPARATOR_CHARS = set("-—=_ 　\t*")
_FOOTER_MARKERS = ("导出时间", "共", "笔记录", "注：", "说明：", "以上")


@dataclass(frozen=True)
class ParsedRow:
    occurred_at: datetime  # UTC
    amount_cents: int  # 非负
    direction: Direction
    merchant: str
    external_id: str
    note: str = ""


@dataclass(frozen=True)
class ParseIssue:
    line_no: int
    status: ImportRowStatus
    detail: str
    raw: str  # 已脱敏


@dataclass(frozen=True)
class ParseResult:
    source: Source
    encoding: str
    rows: tuple[ParsedRow, ...]
    issues: tuple[ParseIssue, ...]
    skipped_lines: int
    header_fields: tuple[str, ...]
    total_rows: int = 0
    rejected_total: int = 0
    warnings: tuple[str, ...] = ()

    @property
    def issues_truncated(self) -> bool:
        """拒识明细是否因 MAX_ISSUES 被截断（total 仍为真实值）。"""
        return self.rejected_total > len(self.issues)


def decode_csv(content: bytes) -> tuple[str, str]:
    """解码字节流，返回 (文本, 实际编码)。"""
    if content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
        try:
            return content.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:  # pragma: no cover
            pass
    for encoding in _ENCODINGS:
        try:
            text = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
        if "\ufffd" not in text:
            return text, encoding
    return content.decode("utf-8", errors="replace"), "utf-8(replace)"


def detect_source(text: str, default: Source = Source.ALIPAY) -> Source:
    head = "\n".join(text.splitlines()[:40])
    if "支付宝" in head:
        return Source.ALIPAY
    if "微信" in head:
        return Source.WECHAT
    if "微信支付账单" in text:
        return Source.WECHAT
    return default


def _match_header(cells: Sequence[str]) -> dict[str, int] | None:
    normalized = [normalize_header(cell) for cell in cells]
    mapping: dict[str, int] = {}
    for field, aliases in _ALIASES:
        for alias in aliases:
            key = normalize_header(alias)
            if key in normalized:
                mapping[field] = normalized.index(key)
                break
    if "occurred_at" in mapping and "amount" in mapping:
        return mapping
    return None


def _cell(row: Sequence[str], index: int | None) -> str:
    """取单元格并规整空白：保留日期与时间之间的单个空格。"""
    if index is None or index >= len(row):
        return ""
    return " ".join(row[index].replace("\u3000", " ").split())


def _add_issue(
    issues: list[ParseIssue],
    line_no: int,
    status: ImportRowStatus,
    detail: str,
    raw: str,
) -> None:
    if len(issues) < MAX_ISSUES:
        issues.append(ParseIssue(line_no, status, detail, redact_text(raw)))


def _is_noise_line(row: Sequence[str]) -> bool:
    cells = [cell for cell in row if cell.strip()]
    if not cells:
        return True
    joined = "".join(cells).strip()
    if joined and set(joined) <= _SEPARATOR_CHARS:
        return True
    if len(cells) <= 2 and any(marker in joined for marker in _FOOTER_MARKERS):
        return True
    return False


def _parse_time(raw: str, tzinfo: ZoneInfo) -> datetime:
    text = " ".join((raw or "").split())
    for fmt in _TIME_FORMATS:
        try:
            return as_utc(datetime.strptime(text, fmt).replace(tzinfo=tzinfo))
        except ValueError:
            continue
    raise ValueError(f"无法识别的时间：{raw!r}")


def _parse_direction(raw: str, amount_cents: int, trade_type: str, description: str) -> Direction:
    text = normalize_header(raw)
    context = normalize_header(f"{trade_type} {description}")
    if "不计收支" in text or "转账" in context or "提现" in context:
        return Direction.TRANSFER
    if "收入" in text or text in ("收", "收入"):
        return Direction.INCOME
    if "支出" in text or text in ("支", "支出"):
        return Direction.EXPENSE
    if "退款" in context:
        return Direction.INCOME
    return Direction.EXPENSE if amount_cents >= 0 else Direction.INCOME


def _resolve_source(
    text: str, default_source: Source, explicit_source: Source | None
) -> tuple[Source, tuple[str, ...]]:
    detected = detect_source(text, default=default_source)
    source = explicit_source or detected
    warnings: tuple[str, ...] = ()
    if explicit_source is not None and explicit_source is not detected:
        warnings = (
            f"文件内容探测为 {detected.value}，与指定来源 {explicit_source.value} 不一致，"
            "已按指定来源导入",
        )
    return source, warnings


def _parse_rows(
    rows: Sequence[Sequence[str]],
    *,
    tzinfo: ZoneInfo,
    source: Source,
    encoding: str,
    warnings: tuple[str, ...],
) -> ParseResult:
    """CSV / XLSX 共用的表头识别与逐行校验。"""
    header_index: int | None = None
    columns: dict[str, int] | None = None
    for index, row in enumerate(rows):
        if _is_noise_line(row):
            continue
        columns = _match_header(row)
        if columns is not None:
            header_index = index
            break

    if columns is None or header_index is None:
        return ParseResult(
            source=source,
            encoding=encoding,
            rows=(),
            issues=(
                ParseIssue(
                    line_no=1,
                    status=ImportRowStatus.MISSING_HEADER,
                    detail="未找到账单表头（需要同时包含交易时间与金额列）",
                    raw=redact_text(" | ".join(",".join(row) for row in rows[:3])),
                ),
            ),
            skipped_lines=0,
            header_fields=(),
            rejected_total=1,
            warnings=warnings,
        )

    missing = [field for field in ("occurred_at", "amount", "external_id") if field not in columns]
    if missing:
        return ParseResult(
            source=source,
            encoding=encoding,
            rows=(),
            issues=(
                ParseIssue(
                    line_no=header_index + 1,
                    status=ImportRowStatus.MISSING_COLUMNS,
                    detail=f"表头缺少必要列：{', '.join(missing)}",
                    raw=redact_text(",".join(rows[header_index])),
                ),
            ),
            skipped_lines=0,
            header_fields=tuple(rows[header_index]),
            rejected_total=1,
            warnings=warnings,
        )

    parsed: list[ParsedRow] = []
    issues: list[ParseIssue] = []
    skipped = 0
    data_rows = 0
    rejected = 0

    for offset, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if _is_noise_line(row):
            skipped += 1
            continue
        data_rows += 1
        joined = ",".join(row)
        if "\ufffd" in joined:
            _add_issue(issues, offset, ImportRowStatus.GARBLED_ROW, "编码异常，无法识别", joined)
            rejected += 1
            continue

        amount_raw = _cell(row, columns.get("amount"))
        time_raw = _cell(row, columns.get("occurred_at"))
        external_id = _cell(row, columns.get("external_id")).lstrip("\t'\"")
        if not amount_raw or not time_raw:
            _add_issue(issues, offset, ImportRowStatus.MISSING_COLUMNS, "金额或时间缺失", joined)
            rejected += 1
            continue
        if not external_id:
            _add_issue(issues, offset, ImportRowStatus.MISSING_EXTERNAL_ID, "缺少交易单号", joined)
            rejected += 1
            continue

        try:
            signed_cents = parse_amount_to_cents(amount_raw)
        except InvalidAmountError as exc:
            _add_issue(issues, offset, ImportRowStatus.INVALID_AMOUNT, str(exc), joined)
            rejected += 1
            continue

        try:
            occurred_at = _parse_time(time_raw, tzinfo)
        except ValueError as exc:
            _add_issue(issues, offset, ImportRowStatus.INVALID_TIME, str(exc), joined)
            rejected += 1
            continue

        trade_type = _cell(row, columns.get("trade_type"))
        description = _cell(row, columns.get("description"))
        direction = _parse_direction(
            _cell(row, columns.get("direction")), signed_cents, trade_type, description
        )

        parsed.append(
            ParsedRow(
                occurred_at=occurred_at,
                amount_cents=abs(signed_cents),
                direction=direction,
                merchant=_cell(row, columns.get("merchant")),
                external_id=external_id,
                note=description,
            )
        )

    return ParseResult(
        source=source,
        encoding=encoding,
        rows=tuple(parsed),
        issues=tuple(issues),
        skipped_lines=skipped,
        header_fields=tuple(rows[header_index]),
        total_rows=data_rows,
        rejected_total=rejected,
        warnings=warnings,
    )


def parse_csv(
    content: bytes,
    *,
    tzinfo: ZoneInfo,
    default_source: Source = Source.ALIPAY,
    explicit_source: Source | None = None,
) -> ParseResult:
    text, encoding = decode_csv(content)
    source, warnings = _resolve_source(text, default_source, explicit_source)
    rows = list(csv.reader(io.StringIO(text)))
    return _parse_rows(rows, tzinfo=tzinfo, source=source, encoding=encoding, warnings=warnings)


# XLSX 本质是 zip 容器；旧版 .xls 是 OLE 复合文档，openpyxl 无法读取，单独提示。
_XLSX_MAGIC = b"PK\x03\x04"
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
# 行数上限：防止压缩率极高的 xlsx（zip 炸弹）被完整展开后占满内存
MAX_XLSX_ROWS = 20000


def detect_format(content: bytes) -> str:
    """按文件头识别账单格式，返回 "xlsx" / "xls" / "csv"。"""
    if content.startswith(_XLSX_MAGIC):
        return "xlsx"
    if content.startswith(_OLE_MAGIC):
        return "xls"
    return "csv"


def _xlsx_cell_text(value: object) -> str:
    """把 openpyxl 单元格值统一转成文本，供表头匹配与行校验复用。"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def parse_xlsx(
    content: bytes,
    *,
    tzinfo: ZoneInfo,
    default_source: Source = Source.ALIPAY,
    explicit_source: Source | None = None,
) -> ParseResult:
    encoding = "xlsx"
    workbook = None
    try:
        from openpyxl import load_workbook

        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.active
        if sheet is None:
            raise ValueError("工作簿没有可用工作表")
        rows: list[tuple[str, ...]] = []
        truncated = False
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            if index >= MAX_XLSX_ROWS:
                truncated = True
                break
            rows.append(tuple(_xlsx_cell_text(cell) for cell in row))
    except Exception:  # 坏 xlsx（损坏/伪造 zip）与坏 CSV 同样只拒识不崩溃
        return ParseResult(
            source=explicit_source or default_source,
            encoding=encoding,
            rows=(),
            issues=(
                ParseIssue(
                    line_no=1,
                    status=ImportRowStatus.MISSING_HEADER,
                    detail="无法解析 XLSX 文件（文件损坏或不是有效工作簿）",
                    raw="",
                ),
            ),
            skipped_lines=0,
            header_fields=(),
            rejected_total=1,
        )
    finally:
        if workbook is not None:
            workbook.close()

    head = "\n".join(",".join(row) for row in rows[:40])
    source, warnings = _resolve_source(head, default_source, explicit_source)
    if truncated:
        warnings += (f"XLSX 行数超过上限，仅解析前 {MAX_XLSX_ROWS} 行",)
    return _parse_rows(
        rows, tzinfo=tzinfo, source=source, encoding=encoding, warnings=warnings
    )


def parse_bill(
    content: bytes,
    *,
    tzinfo: ZoneInfo,
    default_source: Source = Source.ALIPAY,
    explicit_source: Source | None = None,
) -> ParseResult:
    """按文件内容自动分发：xlsx 走 openpyxl，csv 走文本解码，无需看扩展名。"""
    fmt = detect_format(content)
    if fmt == "xlsx":
        return parse_xlsx(
            content,
            tzinfo=tzinfo,
            default_source=default_source,
            explicit_source=explicit_source,
        )
    if fmt == "xls":
        return ParseResult(
            source=explicit_source or default_source,
            encoding="xls",
            rows=(),
            issues=(
                ParseIssue(
                    line_no=1,
                    status=ImportRowStatus.MISSING_HEADER,
                    detail="不支持旧版 .xls 账单，请另存为 .xlsx 或 .csv 后重试",
                    raw="",
                ),
            ),
            skipped_lines=0,
            header_fields=(),
            rejected_total=1,
        )
    return parse_csv(
        content,
        tzinfo=tzinfo,
        default_source=default_source,
        explicit_source=explicit_source,
    )
