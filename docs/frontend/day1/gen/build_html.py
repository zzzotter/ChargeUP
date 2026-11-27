# -*- coding: utf-8 -*-
"""生成线框看板 HTML，并用本机 Chrome 逐张截图。"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DAY1 = os.path.dirname(HERE)
OUT_HTML = os.path.join(DAY1, "wireframes.html")
ASSETS = os.path.join(DAY1, "assets")
CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

sys.path.insert(0, HERE)
from ui import CSS, art  # noqa: E402
import pages  # noqa: E402

BOARD_CSS = r"""
.board-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:#5C5348;margin-top:10px}
.board-legend b{display:block;font-size:11px;color:#8C8175;font-weight:400;margin-top:2px}
.token-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.sw{width:74px;height:52px;border-radius:10px;border:1px solid #E9E0D2;display:flex;align-items:flex-end;
    justify-content:center;font-size:9px;color:#5C5348;padding-bottom:4px;background:#fff}
.flow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:11px;color:#5C5348}
.flow .n{background:#fff;border:1px solid #E9E0D2;border-radius:10px;padding:6px 10px}
.flow .a{color:#B4626F}
"""


def build():
    shots = [(p["no"], p["pr"], p["route"], p["title"], p["body"](), p["notes"]) for p in pages.PAGES]
    arts = "".join(art(no, route, title, pr, body, notes) for no, pr, route, title, body, notes in shots)
    d01 = art("D01", "主流程总览", "记账闭环与干预闭环", "P0–P2", pages.d01(), [], height=472, rail=False)
    arms = d01 + arts

    tokens = [("#FDFBF7", "canvas", "var(--canvas)"), ("#FFFFFF", "surface", "var(--surface)"),
              ("#F7F2EA", "sunken", "var(--sunken)"), ("#E9E0D2", "line", "var(--line)"),
              ("#241F1A", "ink", "var(--ink)"), ("#FF8BA7", "coral", "var(--coral)"),
              ("#7DD8C0", "mint", "var(--mint)"), ("#B8A9E8", "lilac", "var(--lilac)")]
    sw = "".join('<div class="sw" style="background:%s;color:%s">%s<br>%s</div>'
                 % (val, "#241F1A" if name in ("canvas", "surface", "sunken") else "#fff", val, name)
                 for val, name, _ in tokens)

    legend = """
    <div class="board-head">
      <h1>ledger-guard · 前端第 1 天：页面清单 / 用户流程 / 线框</h1>
      <p>低保真线框 · 暖白手账风 · 桌面基准 1200px 画板（应用区 980px）· 移动端基准 375px ·
         金额一律「分」入库、展示层格式化 · 图标为占位几何形，实现阶段统一替换 Lucide</p>
      <div class="board-legend">
        <div>画板编号<b>W01–W17，与《页面清单》一一对应</b></div>
        <div>右侧窄栏<b>该页的线框说明与验收要点</b></div>
        <div>P0 10 张 / P1 2 张 / P2 3 张 / 设置 1 张 / 移动端 1 张<b>共 17 张 + 流程总览 D01</b></div>
      </div>
      <div class="token-row">%s</div>
    </div>
    """ % sw

    html = ("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<title>ledger-guard 线框看板（前端 D1）</title><style>%s%s</style></head><body>"
            "%s<div class='board-wrap'>%s</div>"
            "<script>"
            "var q=new URLSearchParams(location.search).get('only');"
            "if(q){document.body.classList.add('solo');"
            "document.querySelectorAll('.art').forEach(function(a){a.style.display=(a.id===q)?'block':'none';});"
            "}"
            "</script></body></html>" % (CSS, BOARD_CSS, legend, arms))

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("html:", OUT_HTML, len(html))
    return shots


def shots(shots):
    os.makedirs(ASSETS, exist_ok=True)
    url_base = "file:///" + OUT_HTML.replace("\\", "/")
    targets = [("D01", 1200, 520)]
    targets += [(no, 1200, 720) for no, pr, route, title, body, notes in shots]
    for no, w, h in targets:
        out = os.path.join(ASSETS, no + ".png")
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--force-device-scale-factor=2", "--window-size=%d,%d" % (w, h),
               "--screenshot=" + out, url_base + "?only=" + no]
        subprocess.run(cmd, capture_output=True, timeout=90)
        print(no, "<-", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else 0)


if __name__ == "__main__":
    s = build()
    shots(s)
