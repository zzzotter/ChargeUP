"""账单导入应用逻辑：幂等去重与计数（第 6 天）。

通过 ImportGateway 端口与数据库解耦，后端交付前用 MockGateway 即可完整测试：
- 首次出现的单号 -> inserted；
- 数据库已存在、或同批重复的单号 -> duplicated，不重复写入；
- 0 元记录 -> zero_skipped，默认不入库；
- 解析阶段拒识行 -> rejected。
"""
from dataclasses import dataclass, field

from ..gateway.ports import ImportGateway
from ..parser.models import ParseReport, RawTransaction


@dataclass
class ImportResult:
    inserted: int = 0
    duplicated: int = 0
    zero_skipped: int = 0
    rejected: int = 0
    inserted_ids: list[str] = field(default_factory=list)
    duplicated_ids: list[str] = field(default_factory=list)


def import_report(report: ParseReport, gateway: ImportGateway) -> ImportResult:
    result = ImportResult(
        rejected=report.rejected_count,
        zero_skipped=report.zero_amount_count,
    )

    parsed: list[RawTransaction] = report.parsed
    existing = gateway.existing_external_ids(
        report.source, [tx.external_id for tx in parsed]
    )
    batch_seen: set[str] = set()
    to_insert: list[RawTransaction] = []

    for tx in parsed:
        if tx.external_id in existing or tx.external_id in batch_seen:
            result.duplicated += 1
            result.duplicated_ids.append(tx.external_id)
            continue
        batch_seen.add(tx.external_id)
        result.inserted += 1
        result.inserted_ids.append(tx.external_id)
        to_insert.append(tx)

    gateway.insert(to_insert)
    return result
