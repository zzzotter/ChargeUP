# -*- coding: utf-8 -*-
"""入口：生成 DOCX。"""
import os
import sys

from docx import Document
from docx.shared import Cm

HERE = os.path.dirname(os.path.abspath(__file__))
DAY1 = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import docx_part1 as p1  # noqa: E402
import docx_part2 as p2  # noqa: E402
import docx_part3 as p3  # noqa: E402
from docx_base import OUT, footer_text, landscape, portrait  # noqa: E402


def main():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "微软雅黑"
    st.font.size = __import__("docx").shared.Pt(10)

    s = doc.sections[0]
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(1.9)

    p1.cover(doc)
    p1.toc(doc)
    p1.sec_scope(doc)
    p1.sec_tokens(doc)
    p1.sec_ia(doc)
    p2.sec_pages(doc)
    p2.sec_flows(doc)
    p3.sec_wireframes(doc)
    p3.sec_api(doc)
    p3.sec_components(doc)
    p3.sec_review(doc)
    p3.sec_plan(doc)
    p3.sec_dod(doc)

    footer_text(doc, "ledger-guard · 前端设计基线（第 1 天）· v1.0 · 2026-11-26")
    doc.core_properties.title = "ledger-guard 前端设计基线（第 1 天）"
    doc.core_properties.author = "前端"
    doc.core_properties.subject = "页面清单 · 用户流程 · 线框"
    doc.save(OUT)
    print("saved:", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
