# -*- coding: utf-8 -*-
"""17 张低保真线框：P0 记账 9 页 + P1 档案 2 页 + P2 意图 3 页 + 设置 1 页 + 移动端 1 张。"""
from ui import ico, shell, art


def btn(label, kind="", icon=None, cls=""):
    i = ico(icon, 11) if icon else ""
    return '<span class="btn %s %s">%s%s</span>' % (kind, cls, i, label)


def chip(label, kind=""):
    return '<span class="chip %s">%s</span>' % (kind, label)


def field(label, inner, hint=""):
    h = '<div class="hint">%s</div>' % hint if hint else ""
    return '<div class="field"><span class="label">%s</span>%s%s</div>' % (label, inner, h)


def inp(text, cls="", icon=None, w=""):
    i = ico(icon, 11) if icon else ""
    style = ' style="width:%s"' % w if w else ""
    return '<div class="input %s"%s>%s<span class="ph">%s</span></div>' % (cls, style, i, text)


def trow(cells, widths):
    parts = []
    for (c, w) in zip(cells, widths):
        style = ' style="width:%s"' % w if w else ' style="flex:1"'
        parts.append('<div%s>%s</div>' % (style, c))
    return '<div class="trow">%s</div>' % "".join(parts)


def thead(labels, widths):
    parts = []
    for (c, w) in zip(labels, widths):
        style = ' style="width:%s"' % w if w else ' style="flex:1"'
        parts.append('<div%s>%s</div>' % (style, c))
    return '<div class="table-h">%s</div>' % "".join(parts)


def amt(v, kind=""):
    return '<span class="amt %s">%s</span>' % (kind, v)


def skel(w, h="8px", r="6px"):
    return '<div class="skel" style="width:%s;height:%s;border-radius:%s"></div>' % (w, h, r)


def steps(items, active):
    out = []
    for i, t in enumerate(items):
        if i:
            out.append('<span class="step-line"></span>')
        cls = "on" if i == active else ("done" if i < active else "")
        mark = "check" if i < active else str(i + 1)
        b = ico("check", 9) if i < active else str(i + 1)
        out.append('<span class="step %s"><b>%s</b>%s</span>' % (cls, b, t))
    return '<div class="row" style="gap:2px">%s</div>' % "".join(out)


# --------------------------------------------------------------------------- W01
def w01():
    banner = ('<div class="card" style="flex-direction:row;align-items:center;gap:10px;background:var(--lilac-50);'
              'border-color:var(--lilac-100);padding:9px 14px;box-shadow:none">'
              + ico("target", 14) +
              '<div style="font-size:11px"><b>2 个购买意图冷静期已到期</b>'
              '<div class="dim" style="font-size:9.5px;margin-top:1px">最早 11-24 18:20 到期 · 待决策：买下 / 放弃 / 延期</div></div>'
              + '<span style="margin-left:auto">' + btn("去决策", "ghost tiny", "arrow") + '</span></div>')

    kpi1 = ('<div class="card"><div class="kpi-l">本月总支出（已剔除退款与转账）</div>'
            '<div class="kpi-v">¥4,286<em>.50</em></div>'
            '<div class="kpi-s">较上月 ↓12.4% · 剔除退款 2 笔 / 转账 3 笔</div></div>')
    kpi2 = ('<div class="card"><div class="kpi-l">预算使用 · 月度预算 ¥6,000</div>'
            '<div class="kpi-v">68<em>%</em></div>'
            '<div class="bar-track" style="margin:6px 0 4px"><div class="bar-fill mint" style="width:68%"></div></div>'
            '<div class="kpi-s">预警线 80% · 告警线 100%（各自仅触发一次）</div></div>')
    kpi3 = ('<div class="card"><div class="kpi-l">待处理</div>'
            '<div class="kpi-v">12<em>笔未分类</em></div>'
            '<div class="kpi-s">进「待分类收件箱」逐条归类或建规则</div></div>')

    bars = [(46, "6月"), (62, "7月"), (55, "8月"), (78, "9月"), (68, "10月"), (58, "11月")]
    axis = '<div class="axis">' + "".join(
        '<div class="b %s"><i style="height:%d%%"></i><u>%s</u></div>' % ("on" if i == 5 else "", h, m)
        for i, (h, m) in enumerate(bars)) + '</div>'

    trend = ('<div class="card"><div class="card-h"><div class="card-t">近 6 个月支出趋势</div>'
             + chip("单位：元", "") + '</div>' + axis +
             '<div class="row dim" style="font-size:9px;margin-top:8px;gap:14px">'
             '<span>柱状图 · 单系列</span><span>hover 显示当月分类明细</span>'
             '<span style="margin-left:auto">数据源 GET /stats/monthly</span></div></div>')

    legend = [("餐饮", "36%", "var(--coral)"), ("交通", "28%", "var(--mint)"),
              ("购物", "20%", "var(--lilac)"), ("其他", "16%", "#E8DCC8")]
    lg = "".join('<span><i style="background:%s"></i>%s<b style="margin-left:auto;font-weight:600">%s</b></span>'
                 % (c, n, p) for n, p, c in legend)
    donut = ('<div class="card"><div class="card-h"><div class="card-t">分类支出分布</div>'
             + chip("11 月", "") + '</div>'
             '<div class="row" style="gap:14px;align-items:center">'
             '<div class="donut"></div>'
             '<div class="legend" style="flex:1;gap:8px">' + lg + '</div></div></div>')

    budget_rows = [("餐饮", "78%", "warn"), ("购物", "92%", ""), ("交通", "41%", "mint")]
    br = "".join('<div class="col" style="gap:3px"><div class="row" style="font-size:10px">'
                 '<span>%s</span><span class="dim" style="margin-left:auto">%s</span></div>'
                 '<div class="bar-track"><div class="bar-fill %s" style="width:%s"></div></div></div>'
                 % (n, p, k, p) for n, p, k in budget_rows)
    bud = ('<div class="card"><div class="card-h"><div class="card-t">分类预算使用</div>'
           + btn("调整阈值", "ghost tiny", "settings") + '</div>'
           '<div class="col" style="gap:9px">' + br + '</div>'
           '<div class="hint">购物已达 92%，跨越 80% 预警线时已推送站内事件</div></div>')

    rows = [("11-24", "星巴克（国贸店）", "餐饮", "-38.00"),
            ("11-24", "滴滴出行", "交通", "-26.40"),
            ("11-23", "退款 · 退货", "餐饮", "+129.00"),
            ("11-23", "未识别商户 8821", "未分类", "-198.00")]
    tr = ""
    for d, m, c, v in rows:
        cls = "in" if v.startswith("+") else ""
        tag = chip(c, "" if c != "未分类" else "warn")
        tr += trow([d, m, tag, amt(v, cls)], ["40px", None, "56px", "62px"])
    recent = ('<div class="card"><div class="card-h"><div class="card-t">最近流水</div>'
              + chip("查看全部 →", "") + '</div>'
              + thead(["日期", "商户 / 名称", "分类", "金额"], ["40px", None, "56px", "62px"])
              + tr + '</div>')

    content = (banner + '<div class="grid g3">%s</div>' % (kpi1 + kpi2 + kpi3)
               + '<div class="grid g-2-1">%s</div>' % (trend + donut)
               + '<div class="grid g-2-1">%s</div>' % (recent + bud))
    return shell("/", "仪表盘", "2026 年 11 月 · 数据更新于 23:41",
                 inp("搜索商户 / 金额", "", "search", "150px") + btn("导入账单", "coral", "upload"),
                 content)


# --------------------------------------------------------------------------- W02
def w02():
    filters = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:8px;padding:8px 10px">'
               + inp("2026-11", "", "calendar", "86px")
               + '<div class="seg"><span class="on">全部来源</span><span>支付宝</span><span>微信</span>'
                 '<span>截图</span><span>手动</span></div>'
               + inp("全部分类", "", None, "82px")
               + inp("关键词", "", "search", "88px")
               + btn("筛选", "ghost tiny", "filter")
               + chip("更多筛选", "")
               + '<span style="margin-left:auto">' + btn("快捷填写", "coral", "plus") + '</span></div>')

    rows = [("11-24 18:20", "星巴克（国贸店）", "餐饮", "ALIPAY", "-38.00", "已分类"),
            ("11-24 12:05", "滴滴出行", "交通", "WECHAT", "-26.40", "已分类"),
            ("11-23 21:10", "退款 · 退货", "餐饮", "ALIPAY", "+129.00", "退款关联"),
            ("11-23 09:32", "未识别商户 8821", "未分类", "SCREENSHOT", "-198.00", "待归类"),
            ("11-22 20:14", "优衣库", "购物", "WECHAT", "-299.00", "已分类"),
            ("11-22 08:45", "地铁通勤", "交通", "ALIPAY", "-6.00", "已分类"),
            ("11-21 19:02", "未识别商户 4471", "未分类", "MANUAL", "-52.00", "待归类"),
            ("11-21 13:26", "美团外卖", "餐饮", "WECHAT", "-42.80", "已分类"),
            ("11-20 21:40", "京东 · 家居", "购物", "ALIPAY", "-158.00", "已分类"),
            ("11-20 12:12", "瑞幸咖啡", "餐饮", "WECHAT", "-19.90", "已分类"),
            ("11-19 09:05", "房租", "居住", "MANUAL", "-2,200.00", "已分类"),
            ("11-18 18:48", "网易云音乐", "娱乐", "ALIPAY", "-15.00", "已分类")]
    tr = ""
    for i, (d, m, c, s, v, st) in enumerate(rows):
        tag = chip(c, "warn" if c == "未分类" else "")
        state = chip(st, "warn" if st == "待归类" else ("mint" if st == "退款关联" else ""))
        tr += trow([
            '<div class="row" style="gap:6px">%s<span class="dim">%s</span></div>'
            % ('<span class="dot" style="background:var(--line)"></span>', d),
            '<b style="font-weight:600">%s</b>' % m, tag, '<span class="dim">%s</span>' % s,
            amt(v, "in" if v.startswith("+") else ""), state], [None, None, "56px", "74px", "66px", "60px"])
    table = ('<div class="card"><div class="card-h"><div class="card-t">流水明细'
             '<small>共 268 条 · 已剔除 3 笔转账</small></div>'
             + '<div class="row" style="gap:6px">' + chip("批量归类", "") + chip("导出", "") + '</div></div>'
             + thead(["时间", "商户 / 名称", "分类", "来源", "金额", "状态"],
                     [None, None, "56px", "74px", "66px", "60px"]) + tr
             + '<div class="row" style="justify-content:space-between;margin-top:9px;font-size:9.5px;color:var(--ink-4)">'
             + '<span class="dim">每页 20 条 · 1 / 14</span>'
             + '<span class="row" style="gap:5px"><span class="btn ghost tiny">上一页</span>'
               '<span class="btn ghost tiny">下一页</span></span></div></div>')

    side = ('<div class="card"><div class="card-h"><div class="card-t">本月概览</div></div>'
            '<div class="col" style="gap:8px;font-size:10px">'
            '<div class="row"><span class="dim">支出</span><span class="amt" style="margin-left:auto">¥4,286.50</span></div>'
            '<div class="row"><span class="dim">收入</span><span class="amt in" style="margin-left:auto">¥3,200.00</span></div>'
            '<div class="divider"></div>'
            '<div class="row"><span class="dim">未分类</span><span class="amt" style="margin-left:auto">12 笔</span></div>'
            '<div class="row"><span class="dim">疑似重复</span><span class="amt" style="margin-left:auto">1 笔</span></div>'
            '</div><div class="hint">金额入库为整数分</div></div>')

    content = filters + '<div class="grid" style="grid-template-columns:1fr 168px;align-items:start">%s</div>' % (table + side)
    return shell("/ledger", "账本", "全部来源 · 2026-11 · 268 条",
                 btn("导入账单", "coral", "upload"), content)


# --------------------------------------------------------------------------- W03
def w03():
    form = ('<div class="card"><div class="card-h"><div class="card-t">交易详情</div>'
            + '<div class="row" style="gap:6px">' + chip("ALIPAY", "coral") + chip("external_id 2026112422…") + '</div></div>'
            + '<div class="grid g2" style="gap:10px">'
            + field("金额（元）", '<div class="input focus" style="height:38px;font-size:17px;font-weight:700">38.00</div>',
                    "保存时 ×100 转为整数分，禁止浮点运算")
            + field("方向", '<div class="seg" style="align-self:flex-start"><span class="on">支出</span><span>收入</span></div>')
            + field("商户 / 名称", inp("星巴克（国贸店）", "focus"))
            + field("分类", '<div class="input focus">餐饮 %s</div>' % ico("chevron", 11))
            + field("交易时间", inp("2026-11-24 18:20", "", "calendar"))
            + field("来源", '<div class="input">ALIPAY（CSV 导入，只读）</div>')
            + '</div>'
            + field("备注", '<div class="input" style="height:52px;align-items:flex-start;padding-top:8px">'
                          '<span class="ph">例如：加班咖啡</span></div>')
            + '<div class="row" style="margin-top:10px;gap:6px">' + btn("保存修改", "coral", "check")
            + btn("取消", "ghost") + '<span style="margin-left:auto">' + btn("移入回收（软删除）", "ghost", "x") + '</span></div>'
            + '</div>')

    related = ('<div class="card"><div class="card-h"><div class="card-t">关联与审计</div></div>'
               '<div class="col" style="gap:8px;font-size:10px">'
               '<div class="rule-card"><div class="row">' + chip("退款关联", "mint")
               + '<span class="dim" style="margin-left:auto;font-size:9px">金额相反 · 7 天内</span></div>'
               '<div style="margin-top:5px;font-size:9.5px">11-25 收到 +38.00 退款，已自动从支出剔除</div></div>'
               '<div class="rule-card"><div class="row">' + chip("分类来源", "")
               + '<span class="dim" style="margin-left:auto;font-size:9px">规则命中</span></div>'
               '<div style="margin-top:5px;font-size:9.5px">关键词「星巴克」→ 餐饮（用户规则，优先级 1）</div></div>'
               '<div class="rule-card"><div class="row">' + chip("软删除", "warn")
               + '<span class="dim" style="margin-left:auto;font-size:9px">deleted_at</span></div>'
               '<div style="margin-top:5px;font-size:9.5px">财务记录不可物理删除，DELETE 请求由后端拦截</div></div>'
               '</div></div>')

    timeline = ('<div class="card"><div class="card-h"><div class="card-t">变更记录</div></div>'
                '<div class="col" style="gap:7px;font-size:9.5px" class="dim">'
                + "".join('<div class="row" style="gap:6px"><span class="dot" style="background:var(--line)"></span>'
                          '<span class="dim" style="width:64px">%s</span><span>%s</span></div>' % (t, s)
                          for t, s in [("11-24 23:41", "CSV 导入创建"), ("11-25 09:02", "修复分类 未分类 → 餐饮"),
                                       ("11-25 09:02", "关联退款交易 #8821")])
                + '</div></div>')

    content = ('<div class="grid" style="grid-template-columns:1fr 232px;align-items:start;gap:12px">%s</div>'
               % (form + '<div class="grid g1" style="gap:12px">' + related + '</div>' + timeline))
    # 两列：主表单跨行，右侧栏
    content = ('<div style="display:grid;grid-template-columns:1fr 226px;gap:12px;align-items:start">'
               '<div class="col" style="gap:12px">' + form + '</div>'
               '<div class="col" style="gap:12px">' + related + timeline + '</div></div>')
    return shell("/ledger/2026-11-24-001", "交易详情", "只读来源字段 · 编辑后写回审计日志",
                 btn("返回账本", "ghost", "arrow"), content)


# --------------------------------------------------------------------------- W04
def w04():
    def entry(icon, title, desc, chips, btn_label, accent):
        cs = "".join(chip(c, k) for c, k in chips)
        return ('<div class="card" style="gap:9px">'
                '<div class="row" style="gap:8px"><span style="width:30px;height:30px;border-radius:10px;display:flex;'
                'align-items:center;justify-content:center;background:%s">%s</span>'
                '<div class="card-t">%s</div></div>'
                '<div class="dim" style="font-size:10px;line-height:1.65">%s</div>'
                '<div class="row" style="flex-wrap:wrap;gap:4px">%s</div>'
                '<div style="margin-top:auto;padding-top:4px">%s</div></div>'
                % (accent, ico(icon, 15), title, desc, cs, btn(btn_label, "coral", "arrow")))

    e1 = entry("upload", "导入 CSV 账单", "支付宝 / 微信官方导出的 CSV，自动跳过表头、清洗乱码并幂等去重。",
               [("支付宝 24 行表头", ""), ("微信 16 行", ""), ("GBK", ""), ("1000 条内 ≤3s", "")], "选择文件", "var(--coral-50)")
    e2 = entry("image", "截图识别（本地 OCR）", "上传账单列表截图，浏览器本地识别，原图不上传服务端；识别结果可逐条校对。",
               [("最多 8 张", ""), ("PNG / JPG", ""), ("不上传原图", "mint")], "上传截图", "var(--mint-50)")
    e3 = entry("pen", "快捷填写", "无单号、无明细的一笔收支，30 秒录入；时间留空默认 12:00。",
               [("来源 MANUAL", ""), ("自动分类", ""), ("无需单号", "lilac")], "开始填写", "var(--lilac-50)")

    rows = [("11-24 23:41", "支付宝账单 2026-11.csv", "CSV", "成功 128 · 重复 6 · 失败 2", "mint"),
            ("11-23 20:12", "微信截图 ×3", "截图", "确认入账 6 条 · 排除疑似重复 1 条", "mint"),
            ("11-22 09:05", "微信支付账单.csv", "CSV", "解析失败：表头行数不匹配（已保留原文件）", "alert")]
    tr = ""
    for t, name, kind, res, k in rows:
        tr += trow([t, name, chip(kind, ""), chip(res, k), chip("详情 →", "")],
                   ["76px", None, "46px", "200px", "54px"])
    hist = ('<div class="card"><div class="card-h"><div class="card-t">最近导入记录<small>CSV 内容已脱敏写日志</small></div>'
            + '</div>' + thead(["时间", "文件", "方式", "结果", ""], ["76px", None, "46px", "200px", "54px"]) + tr + '</div>')

    content = ('<div class="grid g3">%s</div>' % (e1 + e2 + e3)) + hist + (
        '<div class="row" style="gap:8px;font-size:9.5px;color:var(--ink-4)">'
        + ico("alert", 12) + '<span>导入失败不会产生半成品数据：解析与入库在同一事务内完成，失败回滚并给出可读原因。</span></div>')
    return shell("/import", "导入账单", "三种入口 · 导入即可参与统计与预警",
                 btn("查看导入历史", "ghost"), content)


# --------------------------------------------------------------------------- W05
def w05():
    head = ('<div class="card flat" style="flex-direction:row;align-items:center;justify-content:space-between;padding:10px 14px">'
            + steps(["选择文件", "解析预览", "确认入账"], 1) + chip("文件：支付宝账单_20261124.csv · 1.2 MB", "") + '</div>')

    stats = ('<div class="grid g4">'
             + '<div class="card"><div class="kpi-l">识别流水</div><div class="kpi-v">128<em>条</em></div></div>'
             + '<div class="card"><div class="kpi-l">跳过表头 / 空行</div><div class="kpi-v">24<em>+3</em></div></div>'
             + '<div class="card"><div class="kpi-l">重复（幂等跳过）</div><div class="kpi-v">6<em>条</em></div></div>'
             + '<div class="card" style="border-color:#F6CDC6;background:var(--alert-50)"><div class="kpi-l">解析失败</div>'
             '<div class="kpi-v">2<em>条</em></div><div class="kpi-s">缺列 / 金额异常，不阻塞其余记录</div></div></div>')

    rows = [("2026-11-24 18:20:11", "星巴克（国贸店）", "餐饮", "-38.00", chip("新建", "mint")),
            ("2026-11-24 12:05:44", "滴滴出行", "交通", "-26.40", chip("新建", "mint")),
            ("2026-11-23 21:10:02", "退款 · 退货", "餐饮", "+129.00", chip("新建", "mint")),
            ("2026-11-22 20:14:31", "优衣库", "购物", "-299.00", chip("已存在 · 跳过", "")),
            ("2026-11-21 13:26:09", "美团外卖", "餐饮", "-42.80", chip("新建", "mint")),
            ("2026-11-20 —", "（第 118 行）列数不足", "—", "—", chip("解析失败", "alert"))]
    tr = ""
    for d, m, c, v, st in rows:
        cls = "in" if v.startswith("+") else ""
        tr += trow([d, m, chip(c, "") if c != "—" else '<span class="dim">—</span>', '<span class="dim">支付宝</span>',
                    amt(v, cls), st], ["112px", None, "52px", "62px", "76px", "88px"])
    table = ('<div class="card"><div class="card-h"><div class="card-t">解析结果预览<small>失败行可导出核对</small></div>'
             + '<div class="row" style="gap:6px">' + chip("全部 128", "coral") + chip("仅新建") + chip("仅失败") + '</div></div>'
             + thead(["交易时间", "商户 / 名称", "分类", "来源", "金额", "处理结果"],
                     ["112px", None, "52px", "62px", "76px", "88px"]) + tr + '</div>')

    note = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:10px;padding:8px 12px">'
            + ico("alert", 12)
            + '<span style="font-size:9.5px;color:var(--ink-2)">自动处理：跳过支付宝 24 行 / 微信 16 行表头 · '
              'GBK 编码转 UTF-8 · 清洗特殊符号与千分位 · 按 (来源, 外部单号) 幂等去重 · '
              '识别「退款」「转账」并打标，统计时剔除。</span></div>')

    foot = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:10px;padding:9px 14px">'
            + '<span style="font-size:10px">将写入 <b class="count">120</b> 条新流水（6 条重复将跳过，2 条失败不写入）</span>'
            + '<span class="dim" style="font-size:9px">解析 + 入库耗时 1.4s，满足 ≤3s 约束</span>'
            + '<span class="row" style="margin-left:auto;gap:6px">' + btn("上一步", "ghost") + btn("确认入账", "coral", "check") + '</span></div>')

    content = head + stats + table + note + foot
    return shell("/import/csv", "CSV 账单导入", "第 2 步：解析预览与去重结果确认",
                 btn("重新上传", "ghost"), content)


# --------------------------------------------------------------------------- W06
def w06():
    head = ('<div class="card flat" style="flex-direction:row;align-items:center;justify-content:space-between;padding:10px 14px">'
            + steps(["上传截图", "本地 OCR 识别", "校对候选", "确认入账"], 2)
            + chip("原图不上传 · 仅本地识别", "mint") + '</div>')

    thumbs = ('<div class="col" style="gap:8px">'
              + "".join('<div class="thn" style="width:76px;height:96px;position:relative">%s'
                        '<span class="chip %s" style="position:absolute;bottom:4px;left:4px;font-size:8px">%s</span></div>'
                        % (ico("image", 18), k, t) for t, k in [("已识别 5", "mint"), ("已识别 1", "mint"), ("识别失败", "alert")])
              + '<div class="thn" style="width:76px;height:52px;border-style:dashed">%s</div></div>' % ico("plus", 14))

    rows = [
        ("11-24 18:20", "星巴克（国贸店）", "38.00", chip("待核对", "")),
        ("11-24 12:05", "滴滴出行", "26.40", chip("疑似重复", "warn")),
        ("11-23 09:32", "未识别商户 8821", "198.00", chip("待核对", "")),
    ]
    tr = ""
    for i, (d, m, v, st) in enumerate(rows):
        cells = ['<div class="input" style="height:24px">%s</div>' % d,
                 '<div class="input focus" style="height:24px">%s</div>' % m,
                 '<div class="input" style="height:24px">%s</div>' % v,
                 st,
                 '<div class="row" style="gap:5px"><span class="chip">排除</span><span class="chip">删除</span></div>']
        tr += '<div class="trow" style="gap:6px">%s</div>' % "".join(
            '<div style="width:%s">%s</div>' % (w, c) for c, w in zip(cells, ["86px", None, "52px", "60px", "78px"]))

    table = ('<div class="card"><div class="card-h"><div class="card-t">候选流水（可逐条修改）'
             '<small>识别 6 条 · 疑似重复 1 条</small></div>'
             + '<div class="row" style="gap:6px">' + chip("全选", "") + chip("批量指定分类", "") + '</div></div>'
             + thead(["日期时间", "商户 / 名称", "金额（元）", "状态", "操作"],
                     ["86px", None, "52px", "60px", "78px"]) + tr
             + '<div class="rule-card" style="margin-top:8px;border-color:#F3DFC4;background:var(--warn-50)">'
               '<div class="row" style="gap:6px">' + ico("alert", 12)
             + '<span style="font-size:9.5px"><b>疑似重复：</b>同日同金额同商户已存在记录 11-24 滴滴出行 ¥26.40。</span>'
               '<span class="chip" style="margin-left:auto">默认保留 · 可排除</span></div></div>'
             + '<div class="row" style="margin-top:8px;justify-content:space-between">'
             + '<span class="dim" style="font-size:9px">置信度低于阈值的字段会标黄，可直接手改后入账，不影响其余行</span>'
             + btn("确认入账 6 条", "coral", "check") + '</div></div>')

    note = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:10px;padding:8px 12px">'
            + ico("alert", 12)
            + '<span style="font-size:9.5px;color:var(--ink-2)">约束：单次最多 8 张（PNG/JPG，总计 ≤20MB）· '
              '截图不要求交易单号，系统生成内部 external_id · 弱指纹（日期+金额+商户）仅用于标记疑似重复，'
              '绝不静默丢弃 · OCR 引擎不可用时整批退化为手动校对，并保留快捷填写入口。</span></div>')

    fallback = ('<div class="card flat" style="border-color:#F6CDC6;background:var(--alert-50);flex-direction:row;'
                'align-items:center;gap:10px;padding:9px 12px">' + ico("alert", 14)
                + '<div style="font-size:9.5px"><b>第 3 张图片识别失败（OCR 引擎不可用 / 图片质量过低）</b>'
                  '<div class="dim" style="margin-top:1px">原图仅留在本地，未上传；可重试、删除，或改用快捷填写兜底。</div></div>'
                + '<span class="row" style="margin-left:auto;gap:6px">' + btn("重试", "ghost tiny")
                + btn("快捷填写", "coral tiny") + '</span></div>')

    content = head + fallback + '<div class="row" style="gap:12px;align-items:flex-start">' + (
        '<div style="width:84px">' + thumbs + '</div>' + '<div style="flex:1;min-width:0">' + table + '</div>') + '</div>' + note
    return shell("/import/screenshot", "截图导入", "浏览器本地 OCR · 候选校对 · 疑似重复标记",
                 chip("示例截图 3 张", ""), content)


# --------------------------------------------------------------------------- W07
def w07():
    form = ('<div class="card"><div class="card-h"><div class="card-t">记一笔</div>'
            + chip("仅填名称 + 金额 + 日期即可入账", "mint") + '</div>'
            + '<div class="grid g2" style="gap:10px">'
            + field("商户 / 名称", '<div class="input focus" style="height:34px;font-size:12px">%s</div>' % "楼下便利店",
                    "必填 · 用于分类规则匹配")
            + field("金额（元）", '<div class="input focus" style="height:34px;font-size:15px;font-weight:700">24.50</div>',
                    "支持小数点后两位，入库为整数分")
            + field("分类（自动匹配，可改）", '<div class="row" style="gap:4px;flex-wrap:wrap">'
                                          + chip("餐饮 ✓ 自动", "coral") + chip("购物") + chip("交通") + chip("未分类") + '</div>',
                    "规则命中提示来源；未命中则进收件箱")
            + field("方向", '<div class="seg" style="align-self:flex-start"><span class="on">支出</span><span>收入</span></div>')
            + field("日期", inp("2026-11-26", "", "calendar"))
            + field("时间（可留空）", inp("留空按 12:00", "", "clock"))
            + '</div>'
            + field("备注", '<div class="input" style="height:44px;align-items:flex-start;padding-top:7px">'
                          '<span class="ph">可选，例如：加班夜宵</span></div>')
            + '<div class="row" style="margin-top:10px;gap:6px">' + btn("保存并继续记一笔", "coral", "check")
            + btn("取消", "ghost") + '<span style="margin-left:auto" class="dim" style="font-size:9px">%s</span></div></div>' % "⌘ + Enter 提交")

    preview = ('<div class="card flat"><div class="card-h"><div class="card-t">入账预览</div></div>'
               '<div class="row" style="gap:8px;align-items:center">' + ico("receipt", 16)
               + '<div><div style="font-size:11px;font-weight:600">楼下便利店</div>'
                 '<div class="dim" style="font-size:9px">11-26 12:00 · 餐饮 · MANUAL</div></div>'
               + '<span class="amt" style="margin-left:auto;font-size:14px">-24.50</span></div>'
               '<div class="divider" style="margin:9px 0"></div>'
               '<div class="col" style="gap:6px;font-size:9.5px">'
               '<div class="row"><span class="dim">来源</span><span style="margin-left:auto">MANUAL（系统生成 external_id）</span></div>'
               '<div class="row"><span class="dim">分类</span><span style="margin-left:auto">餐饮（关键词命中）</span></div>'
               '<div class="row"><span class="dim">合并</span><span style="margin-left:auto">不自动合并同商户同日同金额</span></div>'
               '</div></div>')
    tips = ('<div class="card flat"><div class="card-h"><div class="card-t">小提示</div></div>'
            '<div class="col" style="gap:7px;font-size:9.5px;color:var(--ink-2);line-height:1.6">'
            '<div>· 时间留空按 12:00 记录，不影响当月统计口径。</div>'
            '<div>· 分类可手动指定；未命中规则时进入「待分类收件箱」。</div>'
            '<div>· 保存后即时参与预算预警计算。</div></div></div>')

    content = ('<div style="display:grid;grid-template-columns:1fr 214px;gap:12px;align-items:start">'
               + form + '<div class="col" style="gap:12px">' + preview + tips + '</div></div>')
    return shell("/import/quick", "快捷填写", "无单号、无明细的一笔收支",
                 btn("切到 CSV 导入", "ghost"), content)


# --------------------------------------------------------------------------- W08
def w08():
    items = [("未识别商户 8821", "-198.00", "11-23 09:32", "SCREENSHOT"),
             ("未识别商户 4471", "-52.00", "11-21 19:02", "MANUAL"),
             ("便利店 6672", "-24.50", "11-20 08:12", "WECHAT"),
             ("未知转账方", "-320.00", "11-19 21:40", "ALIPAY"),
             ("未识别商户 1029", "-86.00", "11-18 12:03", "ALIPAY")]
    lis = ""
    for i, (m, v, d, s) in enumerate(items):
        on = "background:var(--sunken);border-color:var(--line)" if i == 0 else ""
        lis += ('<div class="rule-card" style="%s;margin-bottom:6px"><div class="row" style="gap:8px">'
                '<span class="dot" style="background:var(--warn)"></span>'
                '<div style="min-width:0"><div style="font-size:10.5px;font-weight:600">%s</div>'
                '<div class="dim" style="font-size:9px">%s · %s</div></div>'
                '<span class="amt" style="margin-left:auto">%s</span></div></div>' % (on, m, d, s, v))

    left = ('<div class="card"><div class="card-h"><div class="card-t">待分类收件箱<small>12 笔</small></div>'
            + chip("按日期", "") + '</div>' + lis
            + '<div class="hint">未命中任何规则的交易强制为 null，统一在此归类</div></div>')

    detail = ('<div class="card"><div class="card-h"><div class="card-t">归类操作</div>'
              + chip("SCREENSHOT · 2026-11-23 09:32", "") + '</div>'
              + '<div class="row" style="gap:8px;align-items:center;margin-bottom:9px">' + ico("receipt", 15)
              + '<div><div style="font-size:11px;font-weight:600">未识别商户 8821</div>'
                '<div class="dim" style="font-size:9px">-198.00 · 无规则命中</div></div></div>'
              + field("① 指定分类", '<div class="row" style="gap:4px;flex-wrap:wrap">' + chip("餐饮") + chip("购物", "coral")
                                     + chip("交通") + chip("娱乐") + chip("其他") + chip("新建分类", "") + '</div>')
              + '<div class="divider" style="margin:10px 0"></div>'
              + field("② 同时为该商户建立关键词规则（可选）",
                      '<div class="row" style="gap:6px">' + inp("关键词：8821", "focus") + inp("→ 购物", "", None, "78px") + '</div>',
                      "规则优先于内置词库；命中即自动分类，不再进收件箱")
              + '<div class="row" style="margin-top:10px;gap:6px">' + btn("确认归类", "coral", "check")
              + btn("仅本次", "ghost") + '<span style="margin-left:auto">' + btn("忽略", "ghost tiny") + '</span></div>'
              + '</div>')

    batch = ('<div class="card flat"><div class="card-h"><div class="card-t">批量处理</div></div>'
             '<div class="col" style="gap:6px;font-size:9.5px">'
             '<div class="row"><span class="dim">已选 3 笔</span><span class="chip" style="margin-left:auto">全选本页</span></div>'
             '<div class="row" style="gap:6px">' + chip("批量归类") + chip("批量忽略") + '</div></div></div>')

    content = ('<div style="display:grid;grid-template-columns:1fr 262px;gap:12px;align-items:start">'
               + left + '<div class="col" style="gap:12px">' + detail + batch + '</div></div>')
    return shell("/inbox", "待分类收件箱", "未匹配到分类的交易集中处理",
                 chip("12 笔待归类", "warn"), content)


# --------------------------------------------------------------------------- W09
def w09():
    cats = [("餐饮", "8", "var(--coral)"), ("交通", "5", "var(--mint)"), ("购物", "7", "var(--lilac)"),
            ("居住", "4", "#E8DCC8"), ("娱乐", "3", "#E8DCC8")]
    crows = ""
    for n, k, c in cats:
        crows += ('<div class="trow"><div class="row" style="gap:7px;flex:1">'
                  '<span class="dot" style="background:%s"></span><span>%s</span></div>'
                  '<span class="dim" style="font-size:9px">%s 条规则</span>'
                  '<span class="chip">编辑</span></div>' % (c, n, k))

    left = ('<div class="card"><div class="card-h"><div class="card-t">分类</div>'
            + btn("新建", "ghost tiny", "plus") + '</div>'
            + '<div class="seg" style="align-self:flex-start;margin-bottom:8px"><span class="on">支出 9</span><span>收入 3</span></div>'
            + crows + '</div>')

    rules = [("星巴克", "餐饮", "用户", "var(--coral-50)"),
             ("瑞幸", "餐饮", "用户", "var(--coral-50)"),
             ("滴滴", "交通", "用户", "var(--coral-50)"),
             ("美团", "餐饮", "内置", "var(--sunken)"),
             ("地铁", "交通", "内置", "var(--sunken)")]
    rrows = ""
    for kw, cat, src, bg in rules:
        rrows += ('<div class="trow"><div style="flex:1">%s</div><span class="chip">%s</span>'
                  '<span class="dim" style="font-size:9px">%s</span><span class="chip">删除</span></div>'
                  % (kw, cat, src))

    right = ('<div class="card"><div class="card-h"><div class="card-t">关键词规则<small>优先级：用户规则 &gt; 内置词库 &gt; 未分类</small></div>'
             + btn("新增规则", "coral tiny", "plus") + '</div>'
             + '<div class="row" style="gap:6px;margin-bottom:8px">' + inp("关键词", "", "search") + inp("→ 分类", "", None, "84px")
             + btn("添加", "ghost tiny") + '</div>'
             + thead(["关键词", "归类到", "来源", ""], [None, "58px", "44px", "44px"]) + rrows + '</div>')

    tester = ('<div class="card flat"><div class="card-h"><div class="card-t">规则测试器</div>'
              + chip("干跑，不写库", "mint") + '</div>'
              + '<div class="row" style="gap:6px">' + inp("输入商户名称，例如：星巴克臻选（国贸店）", "focus") + '</div>'
              + '<div class="row" style="margin-top:8px;gap:6px;font-size:9.5px">' + ico("check", 12)
              + '<span>命中规则「星巴克」→ <b>餐饮</b>；规则来源：用户自定义（优先级 1）</span></div></div>')

    content = ('<div style="display:grid;grid-template-columns:222px 1fr;gap:12px;align-items:start">'
               + left + '<div class="col" style="gap:12px">' + right + tester + '</div></div>')
    return shell("/categories", "分类与规则", "分类体系与自动匹配规则 · 双向可维护",
                 btn("查看待分类", "ghost", "inbox"), content)


# --------------------------------------------------------------------------- W10
def w10():
    setter = ('<div class="card"><div class="card-h"><div class="card-t">月度预算与双阈值</div>'
              + chip("按月生效", "") + '</div>'
              + '<div class="grid g2" style="gap:10px">'
              + field("月度预算总额（元）", '<div class="input focus" style="height:32px;font-size:14px;font-weight:700">6,000.00</div>')
              + field("预算作用域", '<div class="input">全部分类（可下钻单分类）%s</div>' % ico("chevron", 11))
              + '</div>'
              + '<div class="divider" style="margin:10px 0"></div>'
              + field("预警线 warnThreshold", '<div class="row" style="gap:8px"><div class="bar-track" style="flex:1">'
                                             '<div class="bar-fill warn" style="width:80%"></div></div>'
                                             '<div class="input" style="width:62px">80 %</div></div>',
                      "默认 80%，跨线时产生一条 WARN 事件")
              + '<div style="height:8px"></div>'
              + field("告警线 alertThreshold", '<div class="row" style="gap:8px"><div class="bar-track" style="flex:1">'
                                              '<div class="bar-fill" style="width:100%"></div></div>'
                                              '<div class="input" style="width:62px">100 %</div></div>',
                      "默认 100%，跨线时产生一条 ALERT 事件")
              + '<div class="row" style="margin-top:10px;gap:6px">' + btn("保存设置", "coral", "check") + btn("恢复默认", "ghost") + '</div>'
              + '</div>')

    gauge = ('<div class="card flat"><div class="card-h"><div class="card-t">本月进度</div></div>'
             '<div class="row" style="gap:12px;align-items:center">'
             '<div style="position:relative;width:104px;height:104px;border-radius:50%;'
             'background:conic-gradient(var(--mint) 0 68%,var(--sunken) 68% 100%)">'
             '<div style="position:absolute;inset:14px;background:#FFFDF9;border-radius:50%;display:flex;'
             'flex-direction:column;align-items:center;justify-content:center">'
             '<div style="font-size:16px;font-weight:700">68%</div><div class="dim" style="font-size:8px">¥4,086 / ¥6,000</div>'
             '</div></div>'
             '<div class="col" style="gap:6px;font-size:9.5px;flex:1">'
             '<div class="row"><span class="dim">剩余可用</span><span class="amt" style="margin-left:auto">¥1,914.00</span></div>'
             '<div class="row"><span class="dim">日均可用</span><span class="amt" style="margin-left:auto">¥63.80</span></div>'
             '<div class="row"><span class="dim">下次触发</span><span style="margin-left:auto">距 80% 还差 ¥714</span></div>'
             '</div></div></div>')

    events = [("11-19 21:40", "ALERT", "本月支出达到预算 100%（¥6,000）", "alert"),
              ("11-14 10:22", "WARN", "本月支出达到预算 80%（¥4,800）", "warn"),
              ("10-28 19:05", "WARN", "10 月支出达到预算 80%（¥4,800）", "warn")]
    erows = ""
    for t, lv, txt, k in events:
        erows += ('<div class="trow"><span class="dim" style="width:66px;font-size:9px">%s</span>%s'
                  '<span style="flex:1;font-size:9.5px">%s</span></div>' % (t, chip(lv, k), txt))
    hist = ('<div class="card"><div class="card-h"><div class="card-t">预警事件<small>同一阈值每周期仅触发一次</small></div>'
            + chip("全部 →", "") + '</div>' + erows + '</div>')

    content = ('<div style="display:grid;grid-template-columns:1fr 250px;gap:12px;align-items:start">'
               + '<div class="col" style="gap:12px">' + setter + hist + '</div>'
               + '<div class="col" style="gap:12px">' + gauge + '</div></div>')
    return shell("/budget", "预算与预警", "双阈值 · 跨线即触发一次事件",
                 btn("查看事件流", "ghost", "alert"), content)


# --------------------------------------------------------------------------- W11
def w11():
    def wcard(name, price, days, cost, color):
        return ('<div class="card" style="padding:9px;gap:7px">'
                '<div class="thn" style="width:100%%;height:66px;border-radius:10px;background:%s">%s</div>'
                '<div style="font-size:11px;font-weight:600">%s</div>'
                '<div class="row" style="font-size:9px"><span class="dim">购入 ¥%s</span>'
                '<span class="dim" style="margin-left:auto">已穿 %s 天</span></div>'
                '<div class="rule-card" style="padding:5px 8px;background:var(--mint-50);border-color:var(--mint-100)">'
                '<div class="row" style="font-size:9px"><span class="dim">日均成本</span>'
                '<b style="margin-left:auto;font-size:11px">¥%s</b></div></div></div>' % (color, ico("shirt", 16), name, price, days, cost))

    grid = ('<div class="grid g3" style="gap:10px">'
            + wcard("羊毛大衣 · 燕麦色", "1,299", 92, "14.12", "var(--sunken)")
            + wcard("通勤乐福鞋", "599", 41, "14.61", "#F3EDE3")
            + wcard("条纹针织衫", "259", 7, "37.00", "var(--sunken)")
            + wcard("帆布托特包", "189", 210, "0.90", "#F3EDE3")
            + wcard("羽绒服 · 短款", "899", 3, "299.67", "var(--sunken)")
            + wcard("丝绸衬衫", "459", 0, "459.00", "#F3EDE3")
            + '</div>')

    head = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:8px;padding:8px 10px">'
            + inp("全部", "", "filter", "70px") + inp("搜索物品", "", "search", "130px")
            + '<div class="seg">' + '<span class="on">按时间</span><span>按日均成本</span><span>按分类</span></div>'
            + chip("共 24 件 · 本月新增 3 件", "")
            + '<span style="margin-left:auto">' + btn("建档", "coral", "plus") + '</span></div>')

    empty = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:8px;padding:8px 12px">'
             + ico("spark", 13) + '<span style="font-size:9.5px">「日均成本」= 价格 ÷ max(1, 首穿至今天数)，'
               '用于把一次性支出摊平成每天的真实代价。</span></div>')

    insight = ('<div class="grid g3">'
               + '<div class="card flat"><div class="kpi-l">最贵的一天</div>'
                 '<div class="kpi-v" style="font-size:16px">¥299.67<em>/天</em></div>'
                 '<div class="kpi-s">羽绒服 · 短款（已穿 3 天）</div></div>'
               + '<div class="card flat"><div class="kpi-l">最耐穿</div>'
                 '<div class="kpi-v" style="font-size:16px">¥0.90<em>/天</em></div>'
                 '<div class="kpi-s">帆布托特包（已穿 210 天）</div></div>'
               + '<div class="card flat"><div class="kpi-l">建档后未穿着</div>'
                 '<div class="kpi-v" style="font-size:16px">1<em>件</em></div>'
                 '<div class="kpi-s">丝绸衬衫 · 首穿日期待补</div></div></div>')

    content = head + empty + grid + insight
    return shell("/wardrobe", "衣橱物品", "P1 消费档案 · 24 件",
                 btn("时间线视图", "ghost", "clock"), content)


# --------------------------------------------------------------------------- W12
def w12():
    form = ('<div class="card"><div class="card-h"><div class="card-t">物品建档</div>'
            + chip("P1 · 可整体禁用", "") + '</div>'
            + '<div class="row" style="gap:12px;align-items:flex-start">'
            + '<div class="col" style="gap:6px;align-items:center">'
              '<div class="thn" style="width:96px;height:96px;border-style:dashed">%s</div>'
              '<span class="dim" style="font-size:8.5px;text-align:center;line-height:1.4">拖拽或点击上传<br>建议 1:1</span>'
              '</div>'
            + '<div style="flex:1" class="col">'
            + '<div class="grid g2" style="gap:10px">'
            + field("物品名称", '<div class="input focus" style="height:30px">羊毛大衣 · 燕麦色</div>')
            + field("购入价格（元）", '<div class="input focus" style="height:30px">1299.00</div>')
            + field("购买时间", inp("2026-08-26", "", "calendar"))
            + field("分类", '<div class="input">外套 %s</div>' % ico("chevron", 11))
            + '</div>'
            + field("首次穿着日期（可留空）", inp("2026-08-30", "", "calendar"),
                    "留空或晚于今天时，日均成本按 max(1, 天数) 兜底，不报错")
            + '</div></div>'
            + '<div class="rule-card" style="margin-top:10px;background:var(--mint-50);border-color:var(--mint-100)">'
              '<div class="row" style="gap:6px">' + ico("check", 12)
            + '<span style="font-size:9.5px">图片按 SHA-256 去重：检测到相同图片，已复用已有存储，不重复占用空间。</span></div></div>'
            + '<div class="row" style="margin-top:10px;gap:6px">' + btn("保存档案", "coral", "check") + btn("取消", "ghost")
            + '<span style="margin-left:auto">' + btn("保存并再建一件", "ghost") + '</span></div></div>')

    preview = ('<div class="card flat"><div class="card-h"><div class="card-t">即时反馈预览</div></div>'
               '<div class="rule-card" style="background:var(--coral-50);border-color:var(--coral-100);font-size:10px;line-height:1.7">'
               '「这件大衣已经陪你 92 天，今天是 ¥14.12 一天 —— 比一杯咖啡还便宜。」</div>'
               '<div class="hint">由 FeedbackToneProvider 提供随机文案；关闭反馈不影响建档与记账主流程</div></div>')

    cost = ('<div class="card flat"><div class="card-h"><div class="card-t">派生字段预览</div></div>'
            '<div class="col" style="gap:6px;font-size:9.5px">'
            '<div class="row"><span class="dim">daysSince(firstWornAt)</span><span style="margin-left:auto">92 天</span></div>'
            '<div class="row"><span class="dim">dailyCost</span><span style="margin-left:auto">¥14.12 / 天</span></div>'
            '<div class="row"><span class="dim">边界：首穿为空</span><span style="margin-left:auto">按 1 天计</span></div>'
            '</div></div>')

    content = ('<div style="display:grid;grid-template-columns:1fr 232px;gap:12px;align-items:start">'
               + form + '<div class="col" style="gap:12px">' + cost + preview + '</div></div>')
    return shell("/wardrobe/new", "物品建档", "记录已购物品 · 派生日均成本",
                 btn("返回列表", "ghost", "arrow"), content)


# --------------------------------------------------------------------------- W13
def w13():
    head = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:8px;padding:8px 10px">'
            + '<div class="seg"><span class="on">全部 9</span><span>冷静中 3</span><span>待决策 2</span>'
              '<span>已决策 4</span></div>'
            + inp("搜索物品", "", "search", "120px")
            + '<span style="margin-left:auto">' + btn("新建意图", "coral", "plus") + '</span></div>')

    rows = [("降噪耳机 · Sony XM6", "¥2,499", "冷静中", "剩余 31h 12m", "lilac", "已存 12 小时"),
            ("一次性相机", "¥399", "冷静中", "剩余 44h 05m", "lilac", "已存 4 小时"),
            ("亚麻衬衫（米白）", "¥459", "待决策", "已到期 · 11-24 18:20", "warn", "已存 48 小时"),
            ("机械键盘", "¥899", "已决策", "放弃 · 11-20", "", "省下 ¥899"),
            ("跑步机", "¥3,299", "已决策", "买入 · 11-02", "mint", "已入账")]
    tr = ""
    for n, p, st, sub, k, note in rows:
        tr += ('<div class="trow" style="gap:9px;padding:9px 2px">'
               '<div class="thn" style="width:38px;height:38px;border-radius:9px">%s</div>'
               '<div style="flex:1;min-width:0"><div style="font-size:10.5px;font-weight:600">%s</div>'
               '<div class="dim" style="font-size:9px">%s · %s</div></div>'
               '<span class="amt">%s</span>%s<span class="chip" style="width:74px;justify-content:center">%s</span>'
               '</div>' % (ico("target", 14), n, sub, note, p, chip(st, k), "查看 →"))
    table = ('<div class="card"><div class="card-h"><div class="card-t">意图清单</div>'
             + '<div class="row" style="gap:6px">' + chip("按到期时间") + chip("按价格") + '</div></div>' + tr + '</div>')

    stat = ('<div class="grid g3">'
            + '<div class="card"><div class="kpi-l">冷静期拦截率</div><div class="kpi-v">46<em>%</em></div>'
              '<div class="kpi-s">4 件中放弃 2 件，共省下 ¥1,358</div></div>'
            + '<div class="card"><div class="kpi-l">平均冷静时长</div><div class="kpi-v">38<em>h</em></div>'
              '<div class="kpi-s">默认 48h，可延期一次</div></div>'
            + '<div class="card" style="background:var(--lilac-50);border-color:var(--lilac-100)"><div class="kpi-l">到期提醒</div>'
              '<div class="kpi-v">2<em>件</em></div><div class="kpi-s">站内卡片提醒，不依赖推送</div></div></div>')

    content = head + stat + table
    return shell("/intents", "购买意图", "P2 干预 · 冷静期与决策台账",
                 btn("站内提醒设置", "ghost", "clock"), content)


# --------------------------------------------------------------------------- W14
def w14():
    form = ('<div class="card"><div class="card-h"><div class="card-t">新建购买意图</div>'
            + chip("生成后状态 CREATED", "") + '</div>'
            + '<div class="row" style="gap:12px;align-items:flex-start">'
            + '<div class="thn" style="width:84px;height:84px;border-style:dashed">%s</div>' % ico("camera", 16)
            + '<div style="flex:1" class="col">'
            + '<div class="grid g2" style="gap:10px">'
            + field("想买什么", '<div class="input focus" style="height:32px;font-size:12px">降噪耳机 · Sony XM6</div>')
            + field("价格（元）", '<div class="input focus" style="height:32px;font-size:13px;font-weight:700">2499.00</div>')
            + '</div>'
            + field("商品链接 / 店铺（可选）", inp("https://…", "", "link"))
            + field("为什么想买（可选，用于 AI 劝阻）",
                    '<div class="input" style="height:46px;align-items:flex-start;padding-top:7px">'
                    '<span class="ph">例如：现在的耳机通勤时漏音</span></div>')
            + '</div></div>'
            + '<div class="row" style="margin-top:10px;gap:6px">' + btn("进入冷静期 48h", "coral", "clock")
            + btn("取消", "ghost") + '<span style="margin-left:auto" class="dim" style="font-size:9px">%s</span></div></div>' % "立即比对衣橱档案")

    match = ('<div class="card" style="border-color:var(--lilac-100);background:var(--lilac-50)">'
             '<div class="card-h"><div class="card-t">衣橱里可能有相似物品<small>元数据粗筛 + CLIP 精排</small></div>'
             + chip("2 个匹配", "lilac") + '</div>'
             '<div class="rule-card" style="background:#fff;margin-bottom:6px"><div class="row" style="gap:8px">'
             '<div class="thn" style="width:40px;height:40px">%s</div>'
             '<div style="flex:1"><div style="font-size:10px;font-weight:600">降噪耳机 · Sony XM5</div>'
             '<div class="dim" style="font-size:9px">同款不同代 · 相似度 92% · 2024-03 购入 ¥1,999</div></div>'
             '<div class="col" style="align-items:flex-end;gap:2px"><span class="amt">¥2.28/天</span>'
             '<span class="dim" style="font-size:8.5px">已用 730 天</span></div></div></div>'
             '<div class="rule-card" style="background:#fff"><div class="row" style="gap:8px">'
             '<div class="thn" style="width:40px;height:40px">%s</div>'
             '<div style="flex:1"><div style="font-size:10px;font-weight:600">头戴式耳机（米白）</div>'
             '<div class="dim" style="font-size:9px">视觉高度相似 · 相似度 88% · 2025-11 购入 ¥899</div></div>'
             '<div class="col" style="align-items:flex-end;gap:2px"><span class="amt">¥8.40/天</span>'
             '<span class="dim" style="font-size:8.5px">已用 107 天</span></div></div></div></div>')

    ai = ('<div class="card flat"><div class="card-h"><div class="card-t">接下来会发生什么</div></div>'
          '<div class="col" style="gap:7px;font-size:9.5px;color:var(--ink-2);line-height:1.6">'
          '<div class="row" style="gap:6px">%s<span>进入 48 小时冷静期（COOLING_DOWN）</span></div>'
          '<div class="row" style="gap:6px">%s<span>到期后 AI 劝阻：结合相似物品与工时换算</span></div>'
          '<div class="row" style="gap:6px">%s<span>你决策：买下 / 放弃 / 延期（不可逆，除延期）</span></div>'
          '</div></div>' % (ico("clock", 11), ico("spark", 11), ico("check", 11)))

    content = ('<div style="display:grid;grid-template-columns:1fr 262px;gap:12px;align-items:start">'
               + form + '<div class="col" style="gap:12px">' + match + ai + '</div></div>')
    return shell("/intents/new", "新建购买意图", "录入想买的东西 · 立刻与已有档案比对",
                 btn("返回意图列表", "ghost", "arrow"), content)


# --------------------------------------------------------------------------- W15
def w15():
    hero = ('<div class="card" style="background:var(--lilac-50);border-color:var(--lilac-100);flex-direction:row;'
            'align-items:center;gap:12px">'
            '<div class="thn" style="width:52px;height:52px;background:#fff">%s</div>'
            '<div><div style="font-size:13px;font-weight:700">降噪耳机 · Sony XM6</div>'
            '<div class="dim" style="font-size:9.5px;margin-top:2px">¥2,499.00 · 创建于 11-24 18:20 · 状态 COOLING_DOWN</div></div>'
            '<div style="margin-left:auto;text-align:right"><div class="kpi-l">冷静期剩余</div>'
            '<div style="font-size:20px;font-weight:700;font-variant-numeric:tabular-nums">31:12:04</div>'
            '<div class="dim" style="font-size:8.5px">到期 11-26 18:20</div></div></div>' % ico("target", 18))

    story = ('<div class="card"><div class="card-h"><div class="card-t">状态机</div>'
             + chip("不可逆（除延期）", "") + '</div>'
             + '<div class="row" style="gap:4px;font-size:8.5px;flex-wrap:wrap">'
             + chip("CREATED ✓", "mint") + '<span class="dim">→</span>' + chip("COOLING_DOWN ●", "lilac")
             + '<span class="dim">→</span>' + chip("BOUGHT / ABANDONED / DEFERRED") + '</div>'
             + '<div class="hint">放弃记录沉淀为「拦截有效性」统计</div></div>')

    ai = ('<div class="card"><div class="card-h"><div class="card-t">AI 劝阻<small>只接收 PurchaseIntent</small></div>'
          + '<div class="row" style="gap:4px">' + chip("直言", "coral") + chip("委婉") + chip("理性") + '</div></div>'
          + '<div class="rule-card" style="background:var(--coral-50);border-color:var(--coral-100);font-size:10.5px;'
            'line-height:1.85;color:var(--ink)">'
            '你 2024 年买过一副 XM5，到现在用了 730 天，日均 ¥2.28。这副 XM6 相似度 92%%，'
            '主要差别是降噪与续航。<br><br>'
            '按你的时薪 ¥45，这 ¥2,499 等于 <b>55.5 小时</b>的工作。'
            '<span class="dim">（工时换算来自设置页时薪；未设置时 Prompt 不含工时）</span></div>'
          + '<div class="row" style="margin-top:8px;gap:6px;font-size:8.5px;color:var(--ink-4)">'
          + '<span class="dim">%s 文案由服务端生成，前端不接触密钥</span></div></div>' % ico("spark", 10))

    match = ('<div class="card flat"><div class="card-h"><div class="card-t">相似物品（P1 档案）</div></div>'
             '<div class="trow" style="gap:8px"><div class="thn" style="width:34px;height:34px">%s</div>'
             '<div style="flex:1"><div style="font-size:10px">降噪耳机 · Sony XM5</div>'
             '<div class="dim" style="font-size:8.5px">相似度 92%% · 日均 ¥2.28</div></div>'
             '<span class="chip">查看</span></div>'
             '<div class="trow" style="gap:8px"><div class="thn" style="width:34px;height:34px">%s</div>'
             '<div style="flex:1"><div style="font-size:10px">头戴式耳机（米白）</div>'
             '<div class="dim" style="font-size:8.5px">相似度 88%% · 日均 ¥8.40</div></div>'
             '<span class="chip">查看</span></div></div>' % (ico("shirt", 12), ico("shirt", 12)))

    decide = ('<div class="card flat" style="flex-direction:row;align-items:center;gap:8px">'
              + '<span style="font-size:10px">决策后不可回退</span>'
              + '<span class="row" style="margin-left:auto;gap:6px">' + btn("买下 BOUGHT", "ghost")
              + btn("放弃 ABANDONED", "coral") + btn("延期 DEFERRED", "ghost") + '</span></div>')

    effect = ('<div class="card flat"><div class="card-h"><div class="card-t">决策分支与副作用</div>'
              + '<div class="row" style="gap:6px">' + chip("仅延期可重复一次", "warn") + '</div></div>'
              + '<div class="grid g3" style="gap:10px">'
              + '<div class="rule-card"><div class="row" style="gap:6px">' + chip("BOUGHT", "mint")
              + '</div><div class="dim" style="font-size:9px;margin-top:5px;line-height:1.6">'
                '预填快捷填写表单（名称/金额/日期已带出），确认后成为一笔 MANUAL 交易</div></div>'
              + '<div class="rule-card"><div class="row" style="gap:6px">' + chip("ABANDONED", "coral")
              + '</div><div class="dim" style="font-size:9px;margin-top:5px;line-height:1.6">'
                '不产生交易，计入「省下金额 / 拦截率」统计，沉淀为干预有效性数据</div></div>'
              + '<div class="rule-card"><div class="row" style="gap:6px">' + chip("DEFERRED", "")
              + '</div><div class="dim" style="font-size:9px;margin-top:5px;line-height:1.6">'
                '冷静期顺延 48h（仅允许一次），到期后仍须做出最终决策</div></div>'
              + '</div></div>')

    content = ('<div style="display:grid;grid-template-columns:1fr 250px;gap:12px;align-items:start">'
               + '<div class="col" style="gap:12px">' + hero + ai + decide + '</div>'
               + '<div class="col" style="gap:12px">' + story + match + '</div></div>' + effect)
    return shell("/intents/2026-11-0007", "购买意图详情", "冷静期倒计时 · AI 劝阻 · 决策",
                 chip("提醒已开启", "mint"), content)


# --------------------------------------------------------------------------- W16
def w16():
    tabs = [("基础", "on"), ("AI 人设与时薪", ""), ("模块开关", ""), ("数据与隐私", ""), ("关于", "")]
    tl = "".join('<div class="nav-item %s">%s<span>%s</span></div>'
                 % (t[1], ico(ic, 13), t[0]) for ic, t in zip(["user", "spark", "settings", "link", "alert"], tabs))
    left = '<div class="card" style="padding:8px">%s</div>' % tl

    form = ('<div class="card"><div class="card-h"><div class="card-t">时薪与劝阻人设</div>'
            + chip("仅服务端使用", "mint") + '</div>'
            + '<div class="grid g2" style="gap:10px">'
            + field("时薪（元 / 小时）", '<div class="input focus" style="height:30px">45.00</div>',
                    "用于把价格换算成「工作 X 小时」注入 AI Prompt")
            + field("默认人设", '<div class="input">直言不讳 %s</div>' % ico("chevron", 11))
            + '</div>'
            + '<div class="divider" style="margin:10px 0"></div>'
            + '<div class="col" style="gap:8px">'
            + '<div class="row" style="font-size:10px"><span>消费档案（P1）</span>'
              '<span class="chip mint" style="margin-left:auto">已启用</span></div>'
            + '<div class="row" style="font-size:10px"><span>购买意图与干预（P2）</span>'
              '<span class="chip mint" style="margin-left:auto">已启用</span></div>'
            + '<div class="row" style="font-size:10px"><span>即时正向反馈文案</span>'
              '<span class="chip" style="margin-left:auto">已关闭</span></div>'
            + '</div><div class="hint">关闭 P1/P2 仅隐藏入口，不影响 P0 记账、统计与预警</div></div>')

    privacy = ('<div class="card flat"><div class="card-h"><div class="card-t">数据与隐私</div></div>'
               '<div class="col" style="gap:6px;font-size:9.5px;color:var(--ink-2);line-height:1.6">'
               '<div>· 截图原图不上传服务端，日志不保存图片，仅本地 OCR。</div>'
               '<div>· CSV 原始内容脱敏（遮蔽部分单号）后才写入日志。</div>'
               '<div>· 财务记录软删除，DELETE 硬删除由后端拦截。</div>'
               '<div>· DeepSeek 密钥仅存于后端环境变量，前端网络请求不含密钥。</div></div></div>')

    content = ('<div style="display:grid;grid-template-columns:170px 1fr;gap:12px;align-items:start">'
               + left + '<div class="col" style="gap:12px">' + form + privacy + '</div></div>')
    return shell("/settings", "设置", "基础偏好 · 模块开关 · 隐私说明",
                 btn("保存", "coral", "check"), content)


# --------------------------------------------------------------------------- W17
def w17():
    def phone_ledger():
        return ('<div class="phone"><div class="ph-top"><span>9:41</span><span>ledger-guard</span>'
                '<span>100%%</span></div><div class="ph-body">'
                '<div class="row" style="gap:6px">' + inp("2026-11", "", "calendar", "92px")
                + '<div class="seg" style="flex:1"><span class="on">支出</span><span>收入</span></div></div>'
                '<div class="card" style="padding:9px 11px"><div class="kpi-l">本月总支出</div>'
                '<div class="kpi-v" style="font-size:19px">¥4,286.50</div>'
                '<div class="bar-track" style="margin-top:6px"><div class="bar-fill mint" style="width:68%%"></div></div>'
                '<div class="kpi-s">预算 68%% · 预警线 80%%</div></div>'
                '<div class="card" style="padding:8px 10px"><div class="card-t" style="font-size:10.5px">最近流水</div>'
                + "".join('<div class="trow" style="padding:6px 0"><div style="flex:1;min-width:0">'
                          '<div style="font-size:9.5px;font-weight:600;overflow:hidden;text-overflow:ellipsis;'
                          'white-space:nowrap">%s</div><div class="dim" style="font-size:8px">%s</div></div>'
                          '<span class="amt" style="font-size:10px">%s</span></div>' % (m, d, v)
                          for m, d, v in [("星巴克（国贸店）", "餐饮 · 11-24", "-38.00"),
                                          ("滴滴出行", "交通 · 11-24", "-26.40"),
                                          ("未识别商户 8821", "未分类 · 11-23", "-198.00"),
                                          ("优衣库", "购物 · 11-22", "-299.00"),
                                          ("网易云音乐", "娱乐 · 11-18", "-15.00")])
                + '</div>'
                '<div class="rule-card" style="background:var(--lilac-50);border-color:var(--lilac-100);padding:6px 9px">'
                '<div class="row" style="font-size:8.5px"><span>2 个意图冷静期已到期</span>'
                '<span class="chip lilac" style="margin-left:auto">去决策</span></div></div>'
                '<div class="row" style="margin-top:auto;gap:6px">'
                + btn("快捷记一笔", "coral", "pen") + '<span style="margin-left:auto">' + chip("导入", "mint") + '</span></div>'
                '</div><div class="tabbar"><div class="on">%s<span>仪表盘</span></div>'
                '<div>%s<span>账本</span></div><div>%s<span>导入</span></div>'
                '<div>%s<span>收件箱</span></div><div>%s<span>我的</span></div></div></div>'
                % (ico("home", 14), ico("receipt", 14), ico("upload", 14), ico("inbox", 14), ico("user", 14)))

    def phone_capture():
        return ('<div class="phone"><div class="ph-top"><span>9:41</span><span>截图导入</span>'
                '<span>100%%</span></div><div class="ph-body">'
                + steps(["上传", "识别", "校对"], 2)
                + '<div class="card" style="padding:8px 10px"><div class="card-t" style="font-size:10.5px">候选 6 条</div>'
                + "".join('<div class="trow" style="padding:6px 0"><div style="flex:1;min-width:0">'
                          '<div style="font-size:9.5px;font-weight:600">%s</div>'
                          '<div class="dim" style="font-size:8px">%s</div></div>%s'
                          '<span class="amt" style="font-size:10px;width:48px;text-align:right">%s</span></div>'
                          % (m, d, chip(st, k), v)
                          for m, d, v, st, k in [("星巴克（国贸店）", "11-24 18:20", "-38.00", "核对", ""),
                                                 ("滴滴出行", "11-24 12:05", "-26.40", "疑似重复", "warn"),
                                                 ("未识别商户 8821", "11-23 09:32", "-198.00", "核对", ""),
                                                 ("瑞幸咖啡", "11-22 09:10", "-19.90", "核对", ""),
                                                 ("美团外卖", "11-21 20:02", "-42.80", "核对", "")])
                + '</div>'
                '<div class="rule-card" style="background:var(--warn-50);border-color:#F3DFC4;font-size:8.5px;line-height:1.5">'
                  '疑似重复仅标记，默认保留，可手动排除</div>'
                '<div class="dim" style="font-size:8px;line-height:1.5">原图仅本地识别，不上传服务端</div>'
                '<div style="margin-top:auto">' + btn("确认入账 6 条", "coral", "check") + '</div>'
                '</div><div class="tabbar"><div>%s<span>仪表盘</span></div>'
                '<div>%s<span>账本</span></div><div class="on">%s<span>导入</span></div>'
                '<div>%s<span>收件箱</span></div><div>%s<span>我的</span></div></div></div>'
                % (ico("home", 14), ico("receipt", 14), ico("upload", 14), ico("inbox", 14), ico("user", 14)))

    wrap = ('<div class="mobile-wrap">'
            + '<div style="display:flex;flex-direction:column;align-items:center;gap:8px">' + phone_ledger()
            + '<div class="dim" style="font-size:9.5px">375 × 812 · 仪表盘（侧栏收进底部 Tab）</div></div>'
            + '<div style="display:flex;flex-direction:column;align-items:center;gap:8px">' + phone_capture()
            + '<div class="dim" style="font-size:9.5px">375 × 812 · 截图校对（表格改为卡片行）</div></div>'
            + '</div>')
    return wrap


def d01():
    def node(t, s, k=""):
        return '<div class="node %s">%s<small>%s</small></div>' % (k, t, s)

    arw = '<div class="arw">→</div>'
    spacer = '<span style="flex:1"></span>'

    lane1 = (
        '<div class="lane"><div class="lane-h">记账闭环 · P0'
        '<small>导入 → 清洗 → 分类 → 账本 → 统计；未命中的交易进入收件箱并沉淀为规则</small></div>'
        '<div class="flow-row">'
        + node("导入 CSV / 截图", "支付宝 24 行 · 微信 16 行 · 截图 ≤8 张")
        + arw + node("解析 + 幂等去重", "唯一键（来源, 外部单号）")
        + arw + node("分类引擎", "用户规则 &gt; 内置词库 &gt; 未分类", "accent")
        + arw + node("账本 / 流水", "筛选 · 编辑 · 软删除")
        + arw + node("统计与预算", "80% 预警 · 100% 告警", "mint")
        + '</div>'
        '<div class="sub-row">'
        '<div class="sub-node">快捷填写<small>无单号 · 时间留空按 12:00</small></div>'
        '<span class="sub-arw">→</span><span class="sub-label">直接入账，跳过解析与去重</span>'
        + spacer +
        '<div class="sub-node" style="background:var(--warn-50);border-color:#F3DFC4">'
        '未匹配分类<small>categoryId = null，不静默归类</small></div>'
        '<span class="sub-arw">→</span>'
        '<div class="sub-node">待分类收件箱<small>逐条归类 · 批量 · 可忽略</small></div>'
        '<span class="sub-arw">→</span>'
        '<div class="sub-node">沉淀关键词规则<small>回流至分类引擎，后续自动命中</small></div>'
        '</div></div>')

    lane2 = (
        '<div class="lane"><div class="lane-h">干预闭环 · P1 + P2'
        '<small>想买 → 比对已有档案 → 冷静期 → AI 劝阻 → 决策；任一步失败都不阻塞记账主流程</small></div>'
        '<div class="flow-row">'
        + node("想买点什么", "用户主动，不打扰")
        + arw + node("意图录入", "状态 CREATED", "lilac")
        + arw + node("相似度比对", "元数据粗筛 + CLIP 精排（P1 档案）", "lilac")
        + arw + node("冷静期 48h", "COOLING_DOWN · 到期站内提醒", "lilac")
        + arw + node("AI 劝阻", "人设 + 工时换算；8s 超时降级模板", "lilac")
        + arw + node("决策", "不可逆（除延期）", "accent")
        + '</div>'
        '<div class="sub-row">'
        '<div class="sub-node">买下 BOUGHT<small>预填快捷填写，确认后成为一笔账</small></div>'
        '<span class="sub-arw">·</span>'
        '<div class="sub-node">放弃 ABANDONED<small>不产生交易，计入拦截率与省下金额</small></div>'
        '<span class="sub-arw">·</span>'
        '<div class="sub-node">延期 DEFERRED<small>顺延 48h，仅允许一次</small></div>'
        + spacer +
        '<span class="sub-label">P1/P2 关闭时：入口隐藏，'\
        'P0 记账、统计与预警不受影响</span>'
        '</div></div>')

    lane3 = (
        '<div class="lane"><div class="lane-h">全局三态与降级 · 横切 F12'
        '<small>每个数据页面都要有加载、空、错误三态；每项外部能力都要有「能力缺失仍可记账」的兜底</small></div>'
        '<div class="flow-row">'
        + node("加载", "shimmer 骨架，形状与真实内容同构；禁止 spinner")
        + arw + node("空态", "柔色几何插画 + 一句引导 + 一个主动作")
        + arw + node("错误", "卡片级内联错误 + 重试；仅首屏失败才整页错误")
        + arw + node("降级：OCR 不可用", "整批提示 + 改用快捷填写")
        + arw + node("降级：AI 超时 8s", "模板文案 + 「模板」标记，不阻塞决策")
        + arw + node("降级：模块关闭", "入口隐藏 + 直访路由 403", "warn")
        + '</div></div>')

    return '<div class="lane-wrap">' + lane1 + lane2 + lane3 + '</div>'


PAGES = [    dict(no="W01", route="/", title="仪表盘", pr="P0", body=w01, notes=[
        "顶部横幅：冷静期到期提醒，直接跳 P2 决策，不打断记账。",
        "三张 KPI 卡：总支出（已剔除退款/转账）、预算使用率、待处理事项。",
        "中部：单系列柱状趋势 + 分类分布环形图，颜色复用全局语义色。",
        "底部：分类预算进度 + 最近流水，均可点击下钻。",
        "首屏 1.5s 内完成；数据未就绪时用 shimmer 骨架屏占位。"]),
    dict(no="W02", route="/ledger", title="账本列表", pr="P0", body=w02, notes=[
        "筛选器常驻：月份、来源、分类、方向、关键词，URL 携带全部筛选项，可分享/刷新保持。",
        "行内呈现「分类 + 状态」双标签，未分类与疑似重复高亮为黄色系。",
        "列表密度：桌面表格行高 34px；移动端切换为卡片行（见 W17）。",
        "空态、错误态、加载态见 §5.2 状态矩阵，禁止转圈 spinner。",
        "金额右对齐、tabular-nums 等宽数字，避免列抖动。"]),
    dict(no="W03", route="/ledger/[id]", title="交易详情 / 编辑", pr="P0", body=w03, notes=[
        "来源与 external_id 只读，避免篡改幂等键。",
        "金额输入以「元」展示，提交时 ×100 转整数分；禁止浮点运算。",
        "右栏固定三块：退款关联、分类来源、软删除说明 —— 让数据血缘可见。",
        "删除按钮文案为「移入回收（软删除）」，二次确认后调用软删接口。",
        "底部变更记录只读展示，供对账与排查。"]),
    dict(no="W04", route="/import", title="导入中心", pr="P0", body=w04, notes=[
        "三条入口并列：CSV / 截图 OCR / 快捷填写，各自标注关键约束（表头行数、8 张上限、无需单号）。",
        "入口卡片的按钮是页面唯一主动作，视觉上使用珊瑚粉强调。",
        "最近导入记录暴露失败原因，便于用户自助排查。",
        "底部固定提示：解析与入库同事务，失败回滚。"]),
    dict(no="W05", route="/import/csv", title="CSV 导入结果", pr="P0", body=w05, notes=[
        "四步流程中的第 2 步，顶部步骤条常驻，可回退。",
        "四个统计卡：识别 / 跳过表头空行 / 重复跳过 / 解析失败。",
        "预览表逐条给出处理结果，失败行可单独导出核对。",
        "底部汇总「将写入 N 条」并给出耗时，回应 ≤3s 的性能约束。",
        "解析失败不阻塞其余记录：部分成功也要有明确的入账口径。"]),
    dict(no="W06", route="/import/screenshot", title="截图导入（OCR 校对）", pr="P0", body=w06, notes=[
        "左列缩略图带识别状态标签，单张失败不影响整批。",
        "候选表格每个字段都是可编辑输入，商户/金额高亮为待核对。",
        "疑似重复用「同日同金额同商户」弱指纹标记，默认保留、由用户排除，绝不静默丢弃。",
        "识别失败提示条常驻：重试 / 删除 / 快捷填写兜底三条出路。",
        "全流程在浏览器本地完成，原图不上传服务端。"]),
    dict(no="W07", route="/import/quick", title="快捷填写", pr="P0", body=w07, notes=[
        "最少字段：名称 + 金额 + 日期即可入账，其余可留空。",
        "时间留空时提示「按 12:00 记录」，避免用户犹豫。",
        "分类默认自动匹配并显式标注来源（规则命中 / 未分类）。",
        "右栏实时预览最终入账结果，降低误录成本。",
        "明确提示：同商户同日同金额不自动合并。"]),
    dict(no="W08", route="/inbox", title="待分类收件箱", pr="P0", body=w08, notes=[
        "左列待归类清单，右侧为当前选中项的操作面板。",
        "归类动作分两层：仅本次指定分类，或同时沉淀为关键词规则。",
        "规则输入框预填商户中的数字片段，降低用户输入成本。",
        "支持批量归类/忽略，避免逐条处理的疲劳。"]),
    dict(no="W09", route="/categories", title="分类与规则", pr="P0", body=w09, notes=[
        "左栏分类（支出/收入切换），显示每个分类的规则条数。",
        "右栏规则表，显式展示优先级：用户规则 > 内置词库 > 未分类。",
        "规则测试器为「干跑」，可直接验证输入商户的命中结果。",
        "新增规则表单内联在列表顶部，一次两步即可完成。"]),
    dict(no="W10", route="/budget", title="预算与预警", pr="P0", body=w10, notes=[
        "预算金额 + 双阈值（warn 80% / alert 100%）集中在一张卡内。",
        "右侧环形进度给出剩余可用与日均可用，比百分比更可执行。",
        "事件流按时间倒序，明确「同一阈值每周期仅触发一次」。",
        "阈值保存后立即参与下次统计计算，无需重新导入。"]),
    dict(no="W11", route="/wardrobe", title="衣橱物品列表", pr="P1", body=w11, notes=[
        "卡片网格展示物品、购入价、已穿天数与日均成本。",
        "日均成本是核心信息，使用薄荷绿底强调，占据卡片视觉重心。",
        "排序支持时间 / 日均成本 / 分类，帮助识别「买了很少穿」的物品。",
        "P1 关闭时，本入口与相关卡片整块隐藏，不影响 P0。"]),
    dict(no="W12", route="/wardrobe/new", title="物品建档", pr="P1", body=w12, notes=[
        "左表单右预览：建档即看到「日均成本 + 鼓励文案」反馈。",
        "首穿日期可留空，对应 max(1, 天数) 兜底逻辑，页面不报错。",
        "图片上传后提示哈希去重结果（复用已有存储）。",
        "反馈文案区域可整体关闭，关闭不影响保存流程。"]),
    dict(no="W13", route="/intents", title="购买意图列表", pr="P2", body=w13, notes=[
        "顶部三张统计卡：拦截率、平均冷静时长、到期提醒数。",
        "列表按状态分组筛选，行内显示倒计时或决策结果。",
        "放弃记录展示「省下 ¥N」，把干预效果可视化。",
        "到期提醒走站内卡片，不依赖系统推送。"]),
    dict(no="W14", route="/intents/new", title="新建意图 + 相似匹配", pr="P2", body=w14, notes=[
        "录入同时实时调用相似度检测，结果并置在右侧。",
        "匹配卡突出「同款不同代 / 视觉相似 + 相似度 + 日均成本」三点。",
        "底部说明接下来的三步（冷静期 → AI 劝阻 → 决策），管理预期。",
        "P2 关闭时，入口隐藏，P0 记账与统计不受影响。"]),
    dict(no="W15", route="/intents/[id]", title="意图详情与决策", pr="P2", body=w15, notes=[
        "顶部倒计时是本页视觉焦点，秒级刷新但不阻塞交互。",
        "AI 劝阻卡：人设切换 + 工时换算 + 相似物品对比，超时降级为模板文案。",
        "决策三选一（买下/放弃/延期），明确「不可逆，除延期」。",
        "状态机与相似物品放在右栏，作为决策依据而非干扰。"]),
    dict(no="W16", route="/settings", title="设置", pr="全局", body=w16, notes=[
        "左侧分页签，右侧内容区，移动端折叠为分组列表。",
        "时薪是 P2 工时换算的唯一来源，标注「仅服务端使用」。",
        "模块开关（P1/P2/反馈文案）在此集中，关闭只隐藏入口。",
        "隐私说明区把四条安全红线写成可读文案，而非埋在文档里。"]),
    dict(no="W17", route="≤ 375px", title="移动端关键视图", pr="响应式", body=w17, notes=[
        "侧栏收起为底部 5 项 Tab：仪表盘 / 账本 / 导入 / 收件箱 / 我的。",
        "375px 下表格改为卡片行，金额右对齐，无横向滚动条。",
        "主操作按钮固定在内容底部，拇指可达。",
        "图表缩小但保留坐标与图例，不做横滑。"]),
]
