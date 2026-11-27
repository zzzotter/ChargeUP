# -*- coding: utf-8 -*-
"""生成《ledger-guard 前端设计基线（第 1 天）》DOCX。"""
import os
import sys

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
DAY1 = os.path.dirname(HERE)
ASSETS = os.path.join(DAY1, "assets")
OUT = os.path.join(DAY1, "前端第1天-页面清单-用户流程-线框.docx")

sys.path.insert(0, HERE)
import pages as wf  # noqa: E402

INK = RGBColor(0x24, 0x1F, 0x1A)
INK2 = RGBColor(0x5C, 0x53, 0x48)
INK3 = RGBColor(0x8C, 0x81, 0x75)
CORAL = RGBColor(0xC2, 0x70, 0x7F)
FONT = "微软雅黑"
MONO = "Consolas"

BODY_SIZE = 10


# --------------------------------------------------------------------------- 基础工具
def set_run_font(run, name=FONT, size=BODY_SIZE, bold=False, color=INK, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), name)
    rf.set(qn("w:hAnsi"), name)
    rf.set(qn("w:eastAsia"), name)


def para(doc, text="", size=BODY_SIZE, bold=False, color=INK, align=None,
         before=0, after=6, spacing=1.35, indent=0, font=FONT):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    if text:
        set_run_font(p.add_run(text), font, size, bold, color)
    return p


def rich(doc, parts, size=BODY_SIZE, align=None, before=0, after=6, spacing=1.35, indent=0):
    """parts: list of (text, bold, color) 或 (text, bold, color, font)"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    if indent:
        pf.left_indent = Cm(indent)
    if align is not None:
        p.alignment = align
    for item in parts:
        t, b, c = item[0], item[1], item[2]
        f = item[3] if len(item) > 3 else FONT
        set_run_font(p.add_run(t), f, size, b, c)
    return p


def bottom_border(p, color="E9E0D2", sz=6):
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    pPr.append(borders)


def h1(doc, num, text, new_page=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_with_next = True
    if new_page:
        p.paragraph_format.page_break_before = True
    set_run_font(p.add_run("%s  " % num), FONT, 16, True, CORAL)
    set_run_font(p.add_run(text), FONT, 16, True, INK)
    bottom_border(p)
    return p


def h2(doc, num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(13)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    set_run_font(p.add_run("%s  " % num), FONT, 12, True, CORAL)
    set_run_font(p.add_run(text), FONT, 12, True, INK)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    set_run_font(p.add_run(text), FONT, 10.5, True, INK2)
    return p


def bullets(doc, items, size=BODY_SIZE, indent=0.4):
    for it in items:
        if isinstance(it, tuple):
            head, rest = it
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.left_indent = Cm(indent + 0.5)
            set_run_font(p.add_run(head), FONT, size, True, INK)
            set_run_font(p.add_run(rest), FONT, size, False, INK2)
        else:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.left_indent = Cm(indent + 0.5)
            set_run_font(p.add_run(it), FONT, size, False, INK2)


def mono_block(doc, text, size=8.5):
    for line in text.split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.12
        set_run_font(p.add_run(line if line else " "), MONO, size, False, INK2)


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), color)
    tcPr.append(sh)


def table_borders(table, color="DCD3C4"):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:%s" % edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def cell_text(cell, text, size=8.5, bold=False, color=INK2, align=None, ls=1.2):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = ls
    if align is not None:
        p.alignment = align
    lines = str(text).split("\n")
    for i, ln in enumerate(lines):
        if i:
            p.add_run().add_break()
        set_run_font(p.add_run(ln), FONT, size, bold, color)


def table(doc, headers, rows, widths, size=8.5, head_bg="F7F2EA", zebra=None, ls=1.2):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    table_borders(t)
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        shade(hdr[i], head_bg)
        cell_text(hdr[i], htxt, size, True, INK, ls=ls)
    # 表头重复
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)
    for r_i, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cell_text(cells[i], val, size, False, INK2, ls=ls)
            if zebra and r_i % 2 == 1:
                shade(cells[i], zebra)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trPr.append(cant)
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    return t


def caption(doc, text, size=8, color=INK3, align=WD_ALIGN_PARAGRAPH.LEFT, after=8):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(after)
    p.alignment = align
    set_run_font(p.add_run(text), FONT, size, False, color)
    return p


def note_box(doc, title, text, bg="FFF2F5"):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    cell = t.rows[0].cells[0]
    cell.width = Cm(16.6)
    shade(cell, bg)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.35
    set_run_font(p.add_run(title + "　"), FONT, 9, True, CORAL)
    set_run_font(p.add_run(text), FONT, 9, False, INK2)
    table_borders(t, "F6E2E6")
    return t


def landscape(doc):
    old = doc.sections[-1]
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width = Cm(29.7)
    s.page_height = Cm(21.0)
    s.left_margin = Cm(2.0)
    s.right_margin = Cm(2.0)
    s.top_margin = Cm(1.9)
    s.bottom_margin = Cm(1.6)
    return s


def portrait(doc):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(1.9)
    return s


def footer_text(doc, text):
    for s in doc.sections:
        f = s.footer.paragraphs[0]
        f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f.text = ""
        set_run_font(f.add_run(text), FONT, 7.5, False, INK3)
