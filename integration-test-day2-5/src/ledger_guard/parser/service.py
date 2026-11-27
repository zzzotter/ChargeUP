"""解析服务统一入口（自动识别 CSV / xlsx）。"""
from .alipay import AlipayParser
from .base import ParseError
from .models import ParseReport, Source
from .table_source import read_table
from .wechat import WechatParser

_PARSERS = {
    Source.ALIPAY: AlipayParser(),
    Source.WECHAT: WechatParser(),
}


def parse_bill(raw: bytes, source: Source | str) -> ParseReport:
    if isinstance(source, str):
        source = Source(source)
    table = read_table(raw)
    return _PARSERS[source].parse(table)
