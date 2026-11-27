"""通用账单解析基类（与文件格式解耦，输入为 TableData）。

设计要点：
- 按“列名”定位列而非写死列索引，真实账单列名/列序有差异时只需改配置；
- 表头在预期头部行数附近自动定位，兼容头行偏移（真实微信 xlsx 表头在第 18 行）；
- 空行跳过、缺关键列或非法数据按行拒识并记录，0 元记录单列，整体不崩溃。
"""
import re
from dataclasses import dataclass
from datetime import datetime

from .models import Direction, ParseReport, RawTransaction, RejectedRow, Source
from .money import yuan_to_cents, MoneyError
from .table_source import TableData

_PAREN = re.compile(r"[（(].*?[)）]")


class ParseError(RuntimeError):
    """致命解析错误（如找不到表头/关键列）。"""


def _norm(name: str) -> str:
    text = str(name).strip()
    text = text.replace("（", "(").replace("）", ")")
    text = _PAREN.sub("", text)          # 去掉括号及单位，如“金额(元)” -> “金额”
    return text.replace(" ", "").lower()


@dataclass(frozen=True)
class ColumnSpec:
    key: str
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class PlatformConfig:
    source: Source
    expected_header_lines: int
    columns: tuple[ColumnSpec, ...]
    direction_map: dict[str, Direction]
    neutral_direction_values: tuple[str, ...]   # 收支列中表示中性的值
    transfer_keywords: tuple[str, ...]
    datetime_formats: tuple[str, ...]


# 缺这些关键列则单行无法解析
_REQUIRED_KEYS = ("external_id", "amount", "direction", "transacted_at")
_HEADER_SEARCH_CAP = 40


class BaseParser:
    config: PlatformConfig

    def parse(self, table: TableData) -> ParseReport:
        header_idx, col_index = self._locate_header(table.rows)
        report = ParseReport(
            source=self.config.source,
            fmt=table.fmt,
            encoding=table.encoding,
            had_decoding_errors=table.had_decoding_errors,
            header_line_no=header_idx + 1,
        )

        for line_no in range(header_idx + 1, len(table.rows)):
            fields = table.rows[line_no]
            if not any(str(c).strip() for c in fields):
                continue  # 空行直接跳过
            report.total_data_rows += 1

            def cell(key: str) -> str:
                idx = col_index.get(key)
                if idx is None or idx >= len(fields):
                    return ""
                return str(fields[idx]).strip()

            try:
                tx = self._build_row(cell)
            except _RowError as exc:
                report.rejected.append(
                    RejectedRow(line_no + 1, str(exc), ",".join(fields))
                )
                continue

            if tx.amount_cents == 0:
                report.zero_amount.append(tx)  # 0 元记录单列，默认不参与金额统计
            else:
                report.parsed.append(tx)

        return report

    # ---------- 表头定位 ----------
    def _locate_header(self, rows: list[list[str]]) -> tuple[int, dict[str, int]]:
        search_end = min(len(rows), max(
            _HEADER_SEARCH_CAP, self.config.expected_header_lines + 8))
        best: tuple[int, dict[str, int], int] | None = None

        for idx in range(search_end):
            normalized = [_norm(c) for c in rows[idx]]
            col_index: dict[str, int] = {}
            for col in self.config.columns:
                for cand in col.candidates:
                    cand_n = _norm(cand)
                    if cand_n in normalized:
                        col_index[col.key] = normalized.index(cand_n)
                        break
            hit = sum(1 for k in _REQUIRED_KEYS if k in col_index)
            if best is None or hit > best[2]:
                best = (idx, col_index, hit)

        if best is None or best[2] < len(_REQUIRED_KEYS):
            raise ParseError(
                f"{self.config.source.value} 账单在预期位置未找到完整表头，关键列缺失"
            )
        return best[0], best[1]

    # ---------- 单行构建 ----------
    def _build_row(self, cell) -> RawTransaction:
        external_id = cell("external_id")
        if not external_id:
            raise _RowError("缺少外部交易单号")

        amount_text = cell("amount")
        if not amount_text:
            raise _RowError("缺少金额列")
        try:
            signed = yuan_to_cents(amount_text)
        except MoneyError as exc:
            raise _RowError(str(exc))
        amount_cents = abs(signed)

        direction = self._resolve_direction(cell("direction"), cell("type"))
        if direction is None:
            raise _RowError(f"无法识别资金流向: {cell('direction')!r}")

        transacted_at = self._parse_time(cell("transacted_at"))
        if transacted_at is None:
            raise _RowError(f"交易时间无法解析: {cell('transacted_at')!r}")

        return RawTransaction(
            external_id=external_id,
            source=self.config.source,
            amount_cents=amount_cents,
            direction=direction,
            counterparty=cell("counterparty"),
            item_name=cell("item_name"),
            transacted_at=transacted_at,
            status=cell("status"),
            note=cell("note"),
        )

    def _resolve_direction(self, text: str, type_text: str) -> Direction | None:
        text = text.strip()
        if text in self.config.direction_map:
            return self.config.direction_map[text]
        # 中性收支值（支付宝“不计收支”、微信“/”）
        if text in self.config.neutral_direction_values:
            return Direction.TRANSFER
        # 兜底：结合交易类型关键字判断
        combined = f"{text} {type_text}"
        if any(kw in combined for kw in self.config.transfer_keywords):
            return Direction.TRANSFER
        return None

    def _parse_time(self, text: str) -> datetime | None:
        text = text.strip()
        if not text:
            return None
        for fmt in self.config.datetime_formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None


class _RowError(ValueError):
    pass
