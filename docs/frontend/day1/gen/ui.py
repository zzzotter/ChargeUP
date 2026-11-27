# -*- coding: utf-8 -*-
"""线框图 HTML 基础件：设计令牌 CSS、图标、布局外壳。"""

CSS = r"""
:root{
  --canvas:#FDFBF7; --surface:#FFFFFF; --sunken:#F7F2EA; --line:#E9E0D2; --line-soft:#F3EBDD;
  --ink:#241F1A; --ink-2:#5C5348; --ink-3:#8C8175; --ink-4:#A79C8C;
  --coral:#FF8BA7; --coral-50:#FFF2F5; --coral-100:#FFDCE4;
  --mint:#7DD8C0; --mint-50:#EEFAF7; --mint-100:#D6F3EB;
  --lilac:#B8A9E8; --lilac-50:#F5F1FD; --lilac-100:#E4DBF8;
  --warn:#E0A45E; --warn-50:#FDF3E6; --alert:#DE6B5E; --alert-50:#FCEDEA;
  --r-xs:6px; --r-sm:10px; --r-md:14px; --r-lg:20px; --r-xl:28px;
  --sh-1:0 2px 8px rgba(84,66,48,.06); --sh-2:0 10px 24px rgba(84,66,48,.10);
}
*{box-sizing:border-box;margin:0;padding:0;}
body{
  font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",system-ui,sans-serif;
  color:var(--ink); background:#EFE9DE; -webkit-font-smoothing:antialiased;
}
.board-head{max-width:1240px;margin:0 auto;padding:28px 20px 6px;}
.board-head h1{font-size:22px;letter-spacing:.5px;}
.board-head p{font-size:12px;color:var(--ink-3);margin-top:6px;}
.board-wrap{max-width:1240px;margin:0 auto;padding:14px 20px 60px;display:flex;flex-direction:column;gap:26px;}
.art{width:1200px;background:var(--canvas);border:1px solid var(--line);border-radius:var(--r-lg);
     overflow:hidden;box-shadow:var(--sh-1);}
.art-head{height:44px;display:flex;align-items:center;gap:10px;padding:0 16px;
          border-bottom:1px solid var(--line);background:#FFFDF9;}
.art-head .no{font-size:11px;font-weight:700;letter-spacing:.06em;color:#B4626F;background:var(--coral-50);
              border:1px solid var(--coral-100);padding:2px 8px;border-radius:999px;}
.art-head .ttl{font-size:14px;font-weight:700;}
.art-head .route{font-size:11px;color:var(--ink-3);font-family:Consolas,monospace;}
.art-head .pr{margin-left:auto;font-size:10px;padding:2px 8px;border-radius:999px;border:1px solid var(--line);
              color:var(--ink-2);background:var(--sunken);}
.art-body{display:flex;height:676px;}
.frame{width:980px;display:flex;background:var(--canvas);overflow:hidden;}
.rail{width:220px;border-left:1px solid var(--line);background:#FFFDF9;padding:14px 13px;overflow:hidden;}
.rail h4{font-size:10px;letter-spacing:.1em;color:#B4626F;margin-bottom:10px;}
.notes{list-style:none;display:flex;flex-direction:column;gap:9px;}
.notes li{font-size:10.5px;line-height:1.5;color:var(--ink-2);display:flex;gap:6px;}
.notes li b{flex:none;width:14px;height:14px;border-radius:50%;background:var(--coral-50);color:#B4626F;
            font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700;margin-top:1px;}

/* ---------- 应用外壳 ---------- */
.side{width:196px;flex:none;background:#FFFDF9;border-right:1px solid var(--line);padding:14px 12px;
      display:flex;flex-direction:column;}
.brand{display:flex;align-items:center;gap:7px;font-size:13px;font-weight:700;letter-spacing:.2px;
       padding:2px 6px 12px;}
.brand .mark{width:20px;height:20px;border-radius:7px;background:var(--coral-50);border:1px solid var(--coral-100);
             display:flex;align-items:center;justify-content:center;color:#C2707F;}
.brand small{display:block;font-size:9px;color:var(--ink-4);font-weight:400;letter-spacing:.04em;}
.nav-group{font-size:9px;color:var(--ink-4);letter-spacing:.12em;padding:9px 8px 4px;}
.nav-item{display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:var(--r-sm);
          font-size:12px;color:var(--ink-2);}
.nav-item.on{background:var(--coral-50);color:var(--ink);font-weight:600;
             box-shadow:inset 0 0 0 1px var(--coral-100);}
.nav-item .badge{margin-left:auto;font-size:9px;background:var(--sunken);border:1px solid var(--line);
                 border-radius:999px;padding:0 6px;color:var(--ink-2);}
.nav-item.on .badge{background:#fff;border-color:var(--coral-100);color:#B4626F;}
.main{flex:1;display:flex;flex-direction:column;min-width:0;}
.topbar{height:56px;flex:none;display:flex;align-items:center;gap:10px;padding:0 20px;
        border-bottom:1px solid var(--line);background:#FFFDF9;}
.h1{font-size:15px;font-weight:700;letter-spacing:.2px;}
.sub{font-size:10.5px;color:var(--ink-3);margin-top:2px;}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:8px;}
.content{flex:1;padding:16px 20px;display:flex;flex-direction:column;gap:12px;overflow:hidden;}

/* ---------- 基础块 ---------- */
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);
      padding:12px 14px;box-shadow:var(--sh-1);display:flex;flex-direction:column;min-width:0;}
.card.flat{box-shadow:none;background:#FFFDF9;}
.card-h{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:9px;}
.card-t{font-size:12px;font-weight:700;}
.card-t small{font-weight:400;color:var(--ink-4);font-size:10px;margin-left:6px;}
.grid{display:grid;gap:12px;}
.g2{grid-template-columns:1fr 1fr;}
.g3{grid-template-columns:repeat(3,1fr);}
.g4{grid-template-columns:repeat(4,1fr);}
.g-2-1{grid-template-columns:1.55fr 1fr;}
.row{display:flex;align-items:center;gap:8px;}
.col{display:flex;flex-direction:column;gap:6px;}
.mt{margin-top:auto;}
.kpi-l{font-size:10px;color:var(--ink-3);}
.kpi-v{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.5px;margin-top:3px;}
.kpi-v em{font-size:11px;font-style:normal;font-weight:400;color:var(--ink-3);margin-left:2px;}
.kpi-s{font-size:9.5px;color:var(--ink-4);margin-top:3px;}
.btn{display:inline-flex;align-items:center;gap:5px;font-size:10.5px;font-weight:600;white-space:nowrap;
     padding:6px 11px;border-radius:999px;background:var(--ink);color:#FFFDF9;border:1px solid var(--ink);}
.btn.coral{background:var(--coral);border-color:var(--coral);color:#4A222B;}
.btn.ghost{background:#fff;color:var(--ink-2);border-color:var(--line);font-weight:400;}
.btn.tiny{padding:4px 9px;font-size:9.5px;}
.chip{display:inline-flex;align-items:center;gap:4px;font-size:9.5px;padding:2px 8px;border-radius:999px;
      background:var(--sunken);border:1px solid var(--line);color:var(--ink-2);white-space:nowrap;}
.chip.coral{background:var(--coral-50);border-color:var(--coral-100);color:#B4626F;}
.chip.mint{background:var(--mint-50);border-color:var(--mint-100);color:#3E8E7B;}
.chip.lilac{background:var(--lilac-50);border-color:var(--lilac-100);color:#6E5FA6;}
.chip.warn{background:var(--warn-50);border-color:#F3DFC4;color:#A9712C;}
.chip.alert{background:var(--alert-50);border-color:#F6CDC6;color:#B04B40;}
.input{height:29px;border:1px solid var(--line);border-radius:var(--r-sm);background:#fff;
       display:flex;align-items:center;gap:6px;padding:0 9px;font-size:10.5px;color:var(--ink-4);}
.input.focus{border-color:var(--coral);box-shadow:0 0 0 3px var(--coral-50);color:var(--ink);}
.input .ph{color:var(--ink-4);}
.label{font-size:9.5px;color:var(--ink-3);margin-bottom:4px;display:block;}
.hint{font-size:9px;color:var(--ink-4);margin-top:4px;}
.field{display:flex;flex-direction:column;}
.trow{display:flex;align-items:center;gap:10px;padding:7px 2px;border-bottom:1px dashed var(--line-soft);font-size:10.5px;}
.trow:last-child{border-bottom:none;}
.trow .w1{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.amt{font-variant-numeric:tabular-nums;font-weight:600;font-size:11px;}
.amt.in{color:#3E8E7B;}
.muted{color:var(--ink-3);}
.dim{color:var(--ink-4);}
.divider{height:1px;background:var(--line-soft);margin:2px 0;}
.bar-track{height:7px;background:var(--sunken);border-radius:999px;overflow:hidden;}
.bar-fill{height:100%;border-radius:999px;background:var(--coral);}
.bar-fill.mint{background:var(--mint);}
.bar-fill.lilac{background:var(--lilac);}
.bar-fill.warn{background:var(--warn);}
.axis{display:flex;align-items:flex-end;gap:9px;height:108px;padding-top:6px;}
.axis .b{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;gap:4px;align-items:center;}
.axis .b i{display:block;width:100%;border-radius:6px 6px 3px 3px;background:var(--coral-100);}
.axis .b.on i{background:var(--coral);}
.axis .b u{font-size:8.5px;color:var(--ink-4);text-decoration:none;font-style:normal;}
.donut{width:96px;height:96px;border-radius:50%;position:relative;flex:none;
       background:conic-gradient(var(--coral) 0 36%,var(--mint) 36% 64%,var(--lilac) 64% 84%,#E8DCC8 84% 100%);}
.donut:after{content:"";position:absolute;inset:24px;background:#fff;border-radius:50%;}
.legend{display:flex;flex-direction:column;gap:7px;font-size:10px;color:var(--ink-2);}
.legend span{display:flex;align-items:center;gap:6px;}
.legend i{width:7px;height:7px;border-radius:3px;display:block;}
.skel{background:linear-gradient(90deg,#F3EDE3 0%,#FAF6EF 45%,#F3EDE3 100%);border-radius:var(--r-xs);}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;
       padding:14px;text-align:center;flex:1;}
.empty .art2{width:132px;height:66px;position:relative;}
.empty .t{font-size:11.5px;font-weight:600;color:var(--ink-2);}
.empty .d{font-size:9.5px;color:var(--ink-4);line-height:1.6;max-width:220px;}
.dot{width:6px;height:6px;border-radius:50%;}
.step{display:flex;align-items:center;gap:6px;font-size:9.5px;color:var(--ink-4);white-space:nowrap;}
.step b{width:16px;height:16px;border-radius:50%;background:var(--sunken);color:var(--ink-3);
        display:flex;align-items:center;justify-content:center;font-size:9px;}
.step.on{color:var(--ink);font-weight:600;}
.step.on b{background:var(--coral);color:#4A222B;}
.step.done b{background:var(--mint-50);color:#3E8E7B;border:1px solid var(--mint-100);}
.step-line{width:26px;height:1px;background:var(--line);}
.drop{border:1.5px dashed var(--line);border-radius:var(--r-md);background:#FFFDF9;
      display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;color:var(--ink-3);}
.thn{width:88px;height:88px;border-radius:var(--r-sm);background:var(--sunken);border:1px solid var(--line);
     display:flex;align-items:center;justify-content:center;color:var(--ink-4);flex:none;}
.seg{display:flex;background:var(--sunken);border-radius:999px;padding:2px;gap:2px;}
.seg span{font-size:9.5px;padding:3px 10px;border-radius:999px;color:var(--ink-3);white-space:nowrap;}
.seg span.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:var(--sh-1);}
.table-h{display:flex;align-items:center;gap:10px;padding:4px 2px 7px;font-size:9px;color:var(--ink-4);
         border-bottom:1px solid var(--line);}
.rule-card{border:1px solid var(--line);border-radius:var(--r-sm);padding:8px 10px;background:#FFFDF9;}
.count{font-variant-numeric:tabular-nums;font-weight:700;}
.mobile-wrap{display:flex;gap:48px;align-items:flex-start;justify-content:center;width:1200px;height:676px;
             background:var(--canvas);padding-top:6px;}
.phone{width:300px;height:600px;border-radius:32px;border:1px solid var(--line);background:var(--canvas);
       box-shadow:var(--sh-2);overflow:hidden;display:flex;flex-direction:column;}
.phone .ph-top{height:34px;display:flex;align-items:center;justify-content:space-between;padding:0 14px;
               font-size:8.5px;color:var(--ink-4);border-bottom:1px solid var(--line-soft);}
.phone .ph-body{flex:1;padding:12px;display:flex;flex-direction:column;gap:9px;overflow:hidden;}
.phone .tabbar{height:52px;border-top:1px solid var(--line);background:#FFFDF9;display:flex;
               align-items:center;justify-content:space-around;font-size:8px;color:var(--ink-4);}
.phone .tabbar div{display:flex;flex-direction:column;align-items:center;gap:3px;}
.phone .tabbar div.on{color:var(--ink);font-weight:600;}
.solo .board-head{display:none;}
.solo .board-wrap{padding:0;}
.solo .art{border-radius:0;box-shadow:none;border:none;}
.solo .art{display:none;}

/* ---------- 流程图（D01） ---------- */
.lane-wrap{width:1200px;padding:16px 18px;display:flex;flex-direction:column;gap:12px;background:var(--canvas);}
.lane{border:1px solid var(--line);border-radius:var(--r-md);background:#FFFDF9;padding:11px 14px 12px;
      display:flex;flex-direction:column;gap:9px;box-shadow:var(--sh-1);}
.lane-h{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:700;}
.lane-h small{font-weight:400;font-size:9.5px;color:var(--ink-4);}
.flow-row{display:flex;align-items:stretch;}
.node{flex:1;min-width:0;border:1px solid var(--line);background:#fff;border-radius:var(--r-sm);
      padding:7px 9px;font-size:11px;font-weight:600;display:flex;flex-direction:column;gap:2px;
      box-shadow:0 1px 4px rgba(84,66,48,.05);}
.node small{font-weight:400;color:var(--ink-4);font-size:8.8px;line-height:1.45;}
.node.accent{border-color:var(--coral-100);background:var(--coral-50);}
.node.mint{border-color:var(--mint-100);background:var(--mint-50);}
.node.lilac{border-color:var(--lilac-100);background:var(--lilac-50);}
.node.dash{border-style:dashed;background:#fff;box-shadow:none;}
.node.warn{background:var(--warn-50);border-color:#F3DFC4;}
.arw{width:22px;flex:none;display:flex;align-items:center;justify-content:center;color:#C0B4A2;font-size:12px;}
.sub-row{display:flex;align-items:center;gap:8px;}
.sub-node{width:186px;border:1px dashed var(--line);border-radius:var(--r-sm);padding:5px 9px;font-size:10px;
          color:var(--ink-2);background:#fff;display:flex;flex-direction:column;gap:1px;}
.sub-node small{font-size:8.5px;color:var(--ink-4);}
.sub-arw{color:#C0B4A2;font-size:11px;}
.sub-label{font-size:8.5px;color:var(--ink-4);}
"""

ICONS = {
    "home": '<path d="M4 11.2 12 4l8 7.2"/><path d="M6 10.6V20h12v-9.4"/>',
    "receipt": '<rect x="6" y="3" width="12" height="18" rx="2.2"/><path d="M9 8h6M9 12h6M9 16h3.5"/>',
    "upload": '<path d="M12 16.5V6"/><path d="M8 9.6 12 5.6l4 4"/><path d="M4.5 16.5v2.2h15v-2.2"/>',
    "image": '<rect x="4" y="5" width="16" height="14" rx="2.2"/><circle cx="9" cy="10" r="1.5"/>'
             '<path d="M5.8 17.2l4.2-4.2 3 3 2.2-2.2 3 3"/>',
    "pen": '<path d="M4.5 19.5l4.6-1.1 8.9-8.9-3.5-3.5-8.9 8.9z"/><path d="M14 6l3.5 3.5"/>',
    "list": '<path d="M8.5 6h11M8.5 12h11M8.5 18h11"/><circle cx="4.6" cy="6" r=".9"/>'
            '<circle cx="4.6" cy="12" r=".9"/><circle cx="4.6" cy="18" r=".9"/>',
    "inbox": '<path d="M4 13.2 6 4.6h12l2 8.6v5.4H4z"/><path d="M4 13.2h4l1.1 2.2h5.8l1.1-2.2h4"/>',
    "tag": '<path d="M4 4h7.2l8.8 8.8-7.2 7.2L4 11.2z"/><circle cx="8.4" cy="8.4" r="1.4"/>',
    "chart": '<path d="M4.5 4v16h15"/><rect x="7.5" y="12" width="3.2" height="5"/>'
             '<rect x="12.5" y="8" width="3.2" height="9"/><rect x="17.5" y="14" width="3.2" height="3"/>',
    "gauge": '<path d="M4 17.2a8 8 0 1 1 16 0"/><path d="M12 17.2l3.6-4.6"/>',
    "shirt": '<path d="M8.2 4.4 12 6.4l3.8-2 3.4 2.6-2 3v9.6H6.8V10l-2-3z"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.4"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 7.6V12l3.2 2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 3.2v2.2M12 18.6v2.2M3.2 12h2.2M18.6 12h2.2'
                'M5.8 5.8l1.6 1.6M16.6 16.6l1.6 1.6M18.2 5.8l-1.6 1.6M7.4 16.6l-1.6 1.6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="M15.6 15.6 20 20"/>',
    "calendar": '<rect x="4" y="5.4" width="16" height="14.6" rx="2.2"/>'
                '<path d="M4 10.4h16M8.4 3.2v4M15.6 3.2v4"/>',
    "check": '<path d="M5 12.8 9.6 17.4 19 8"/>',
    "alert": '<path d="M12 4.4 20.4 19.6H3.6z"/><path d="M12 10v4M12 17.2v.01"/>',
    "spark": '<path d="M12 4.4l1.7 5.3 5.3 1.7-5.3 1.7L12 18.4l-1.7-5.3L5 11.4l5.3-1.7z"/>',
    "arrow": '<path d="M4.6 12h13.2M13 6.4l5.6 5.6L13 17.6"/>',
    "chevron": '<path d="M6.6 9.4 12 14.8l5.4-5.4"/>',
    "filter": '<path d="M4.4 6.4h15.2M7.4 12h9.2M10.2 17.6h3.6"/>',
    "user": '<circle cx="12" cy="9" r="3.4"/><path d="M5 20c1.5-3.4 3.9-4.9 7-4.9s5.5 1.5 7 4.9"/>',
    "x": '<path d="M6.4 6.4 17.6 17.6M17.6 6.4 6.4 17.6"/>',
    "link": '<path d="M9.6 14.4 14.4 9.6"/><path d="M8.4 11.6 6.8 13.2a3.1 3.1 0 0 0 4.4 4.4l1.6-1.6"/>'
            '<path d="M15.6 12.4l1.6-1.6a3.1 3.1 0 0 0-4.4-4.4l-1.6 1.6"/>',
    "repeat": '<path d="M4.4 9.2h13.2l-3-3"/><path d="M19.6 14.8H6.4l3 3"/>',
    "camera": '<rect x="4" y="7" width="16" height="12.2" rx="2.2"/><circle cx="12" cy="13" r="3.1"/>'
              '<path d="M9 7l1-2h4l1 2"/>',
    "wallet": '<rect x="3.6" y="6.4" width="16.8" height="12" rx="2.4"/><path d="M3.6 10h16.8"/>'
              '<circle cx="16.4" cy="14.4" r="1.1"/>',
}


def ico(name, size=14, cls=""):
    return ('<svg class="ico %s" width="%d" height="%d" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg>'
            % (cls, size, size, ICONS[name]))


NAV = [
    ("记账", [("home", "仪表盘", "/", None), ("receipt", "账本", "/ledger", None),
              ("upload", "导入账单", "/import", None), ("inbox", "待分类收件箱", "/inbox", "12")]),
    ("管理", [("tag", "分类与规则", "/categories", None), ("gauge", "预算与预警", "/budget", None)]),
    ("消费档案", [("shirt", "衣橱物品", "/wardrobe", None)]),
    ("购买意图", [("target", "购买意图", "/intents", "2")]),
    ("系统", [("settings", "设置", "/settings", None)]),
]


def sidebar(active):
    out = ['<div class="side">',
           '<div class="brand"><span class="mark">%s</span><span>ledger-guard'
           '<small>手账式记账 · 消费干预</small></span></div>' % ico("wallet", 12)]
    for group, items in NAV:
        out.append('<div class="nav-group">%s</div>' % group)
        for icon, label, route, badge in items:
            on = " on" if route == active else ""
            b = '<span class="badge">%s</span>' % badge if badge else ""
            out.append('<div class="nav-item%s">%s<span>%s</span>%s</div>'
                       % (on, ico(icon, 13), label, b))
    out.append('<div class="mt muted" style="font-size:9px;padding:8px 8px 0;line-height:1.6">'
               '金额均以「分」入库<br>展示层统一格式化</div>')
    out.append('</div>')
    return "".join(out)


def shell(active, title, sub, right, content):
    return ('<div class="frame">%s<div class="main"><div class="topbar">'
            '<div><div class="h1">%s</div><div class="sub">%s</div></div>'
            '<div class="tb-right">%s</div></div>'
            '<div class="content">%s</div></div></div>' % (sidebar(active), title, sub, right, content))


def art(no, route, title, pr, frame_html, notes, height=676, extra_cls="", rail=True):
    lis = "".join('<li><b>%d</b><span>%s</span></li>' % (i + 1, n) for i, n in enumerate(notes))
    body = frame_html
    if rail:
        body = (frame_html + '<aside class="rail"><h4>线框说明</h4><ol class="notes">%s</ol></aside>' % lis)
    return ('<section class="art %s" id="%s">'
            '<div class="art-head"><span class="no">%s</span><span class="ttl">%s</span>'
            '<span class="route">%s</span><span class="pr">%s</span></div>'
            '<div class="art-body" style="height:%dpx">%s</div></section>'
            % (extra_cls, no, no, title, route, pr, height, body))
