# -*- coding: utf-8 -*-
"""组装 DOCX 正文。"""
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt, RGBColor

from docx_base import (ASSETS, BODY_SIZE, CORAL, FONT, INK, INK2, INK3, MONO, OUT,
                       bottom_border, bullets, caption, cell_text, h1, h2, h3,
                       landscape, mono_block, note_box, para, portrait, rich,
                       set_run_font, shade, table, table_borders)
import pages as wf

DATE = "2026-11-26"


# --------------------------------------------------------------------------- 封面
def cover(doc):
    para(doc, "", after=70)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_run_font(p.add_run("ledger-guard"), FONT, 13, True, CORAL)
    para(doc, "智能记账与消费干预系统", FONT if False else 11, False, INK3, after=6)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    set_run_font(p.add_run("前端设计基线"), FONT, 34, True, INK)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    set_run_font(p.add_run("页面清单 · 用户流程 · 线框"), FONT, 18, False, INK2)
    bottom_border(p, "E9E0D2", 8)
    para(doc, "第 1 天交付物（前端）· 供三人当日互审", 10.5, False, INK3, after=30)

    rows = [
        ("文档编号", "FE-D1-001"),
        ("阶段 / 日期", "开发第 1 天 / %s" % DATE),
        ("所属项目", "ledger-guard（个人自托管 Web 应用，Docker Compose 部署）"),
        ("编写", "前端负责人"),
        ("互审对象", "后端负责人（实体·状态·API 约定）、集成负责人（验收项·测试数据）"),
        ("依据文档", "README.docx（软件需求规格说明书 SRS）：P0 记账 / P1 消费档案 / P2 购买意图"),
        ("依据计划", "后端-前端-集成开发计划分工.xlsx：第 1 天「梳理页面清单、用户流程与线框」"),
        ("版本", "v1.0（初稿，待当日评审会签）"),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.autofit = False
    table_borders(t, "E9E0D2")
    for k, v in rows:
        cells = t.add_row().cells
        cells[0].width = Cm(3.4)
        cells[1].width = Cm(13.2)
        shade(cells[0], "FBF7F0")
        cell_text(cells[0], k, 8.5, True, INK3)
        cell_text(cells[1], v, 9, False, INK2)

    para(doc, "", after=26)
    para(doc, "", after=10)
    items = [
        ("交付 3 件", "① 页面清单（17 路由 + 状态矩阵）　② 用户流程（12 条）　③ 线框 17 张 + D01 流程总览"),
        ("线框构成", "P0 10 · P1 2 · P2 3 · 设置 1 · 移动端 1，共 17 张；另附流程总览 1 张（D01）"),
        ("附加 5 件", "④ 设计令牌　⑤ 接口草案（DTO / 枚举 / 错误码）　⑥ 组件清单"),
        ("", "⑦ 互审清单与待确认问题 Q1–Q10　⑧ 第 2–21 天任务映射"),
    ]
    for head, body in items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.2)
        if head:
            set_run_font(p.add_run(head + "："), FONT, 9, True, INK3)
        set_run_font(p.add_run(body), FONT, 9, False, INK2)


# --------------------------------------------------------------------------- 目录
def toc(doc):
    h1(doc, "0", "阅读指引与当页结论", new_page=True)
    para(doc,
         "本文档是前端第 1 天的唯一交付物，用于把 SRS 中的功能条目翻译成可施工的界面约定。"
         "它同时承担两份「契约」作用：对后端，冻结字段名、枚举与路由命名；对集成测试，给出可验收的页面状态与流程分支。"
         "文档中的每一条约定都可被第 2–12 天的实现直接引用，不产生二次解释。", after=10)

    t = doc.add_table(rows=1, cols=3)
    table_borders(t)
    hdr = t.rows[0].cells
    for i, htxt in enumerate(["章节", "内容", "主要读者"]):
        shade(hdr[i], "F7F2EA")
        cell_text(hdr[i], htxt, 8.5, True, INK)
    contents = [
        ("1–3", "设计令牌与视觉基线、信息架构与导航", "前端 / 集成"),
        ("4", "页面清单（17 个路由）与页面状态矩阵（加载·空·错误）", "三人"),
        ("5", "用户流程 F1–F12：主干、失败分支、降级策略", "三人"),
        ("6", "线框索引与 17 张线框图（横向页）", "三人"),
        ("7", "接口约定草案：端点、DTO、枚举、错误码、金额与时区规范", "后端 / 前端"),
        ("8", "共享组件清单与复用边界", "前端 / 集成"),
        ("9", "互审清单、待确认问题（含默认决策）、测试数据清单", "三人"),
        ("10–11", "第 2–12 天任务映射、第 1 天完成定义自检", "前端"),
    ]
    for a, b, c in contents:
        cells = t.add_row().cells
        cells[0].width = Cm(1.6)
        cells[1].width = Cm(11.4)
        cells[2].width = Cm(3.6)
        cell_text(cells[0], a, 8.5, True, CORAL)
        cell_text(cells[1], b, 8.5, False, INK2)
        cell_text(cells[2], c, 8.5, False, INK3)

    h3(doc, "当天结论（供互审会直接表决）")
    bullets(doc, [
        ("页面边界已定：", "17 个路由，P0 占 10 个，P1/P2 各 3 个，设置 1 个；P1/P2 关闭后仅隐藏入口，不影响 P0。"),
        ("交互基线已定：", "所有数据页面必须实现加载（shimmer 骨架）、空（插画 + 引导 + 主动作）、错误（内联重试）三态，禁止转圈 spinner。"),
        ("金额口径已定：", "前端表单以「元」输入、提交前转整数分；展示统一走 formatCents，禁止任何浮点累计。"),
        ("枚举已定：", "TxSource / Direction / IntentStatus / Decision / AlertLevel 等 7 组枚举见 §7.3，后端实现需保持一致。"),
        ("流程分支已定：", "CSV 部分失败可入账、截图 OCR 失败可兜底、AI 劝阻超时 8s 降级为模板文案，三条降级路径写进流程与线框。"),
    ])

    note_box(doc, "待互审表决",
             "§9 列出 10 个需要当日拍板的接口细节（分页方式、时区边界、疑似重复阈值、BOUGHT 是否自动建单等），"
             "每条都给了默认决策——若会上无人反对，即按默认决策进入第 2 天开发，避免阻塞。")


# --------------------------------------------------------------------------- 1 范围
def sec_scope(doc):
    h1(doc, "1", "交付范围与阅读约定")
    h2(doc, "1.1", "第 1 天做什么、不做什么")
    table(doc,
          ["事项", "第 1 天", "后续"],
          [("页面清单与路由命名", "完成（本文 §4）", "第 3 天起随实现微调，改一次记一次"),
           ("用户流程与失败分支", "完成（本文 §5）", "第 5–10 天联调时补充边界"),
           ("低保真线框", "完成 17 张（本文 §6）", "第 2 天起进入高保真实现"),
           ("设计令牌", "冻结取值（本文 §2）", "第 2 天落为 tailwind + CSS Variables"),
           ("接口约定", "草案（本文 §7）", "第 5 天对齐 OpenAPI，之后以后端 Swagger 为准"),
           ("代码实现", "不做", "第 2 天初始化工程")],
          [4.2, 6.2, 6.2], zebra="FDFBF7")

    h2(doc, "1.2", "阅读约定")
    bullets(doc, [
        ("P0 / P1 / P2：", "沿用 SRS 的模块优先级。P0 不可移除；P1（消费档案）、P2（购买意图）可整体禁用。"),
        ("W01–W17：", "线框编号，与 §4 页面清单的 P01–P17 一一对应，末尾 W17 为移动端关键视图。"),
        ("F1–F12：", "用户流程编号，其中 F12 为全局三态与降级，横切所有页面。"),
        ("Q1–Q10：", "待确认问题编号，见 §9.2；未确认前按「默认决策」执行。"),
        ("`等宽字体`：", "表示字段名、枚举值、路由、接口路径，实现时按字面拼写，不得改写大小写。"),
    ])


# --------------------------------------------------------------------------- 2 令牌
def sec_tokens(doc):
    h1(doc, "2", "设计令牌与视觉基线")
    para(doc,
         "SRS 把视觉写成硬约束：浅色暖白手账风、禁止深色主题、主背景 #FDFBF7、禁止纯黑/纯灰阴影、"
         "五档圆角、三种语义强调色不可硬编码。下面把它落成一张可直接写进 tailwind.config / globals.css 的令牌表；"
         "所有页面与组件只允许引用令牌名，不允许出现十六进制字面量。", after=8)

    table(doc,
          ["类别", "令牌", "取值", "用途与约束"],
          [("画布", "canvas", "#FDFBF7", "全站底色；禁止纯白大底、禁止深色主题"),
           ("承载面", "surface", "#FFFFFF", "卡片、抽屉、弹层"),
           ("次级面", "sunken", "#F7F2EA", "分段控件底、进度条轨道、占位块"),
           ("描边", "line", "#E9E0D2", "1px 卡片描边；虚线用 #F3EBDD"),
           ("文字", "ink", "#241F1A", "标题、金额等主要信息"),
           ("文字", "ink-2 / ink-3 / ink-4", "#5C5348 / #8C8175 / #A79C8C", "正文 / 辅助 / 占位；禁止用纯灰 #999"),
           ("强调", "coral", "#FF8BA7", "主强调色：主动作按钮、当前导航、关键数字"),
           ("强调", "mint", "#7DD8C0", "正向语义：健康支出、日均成本、成功态"),
           ("强调", "lilac", "#B8A9E8", "干预语义：冷静期、意图提醒、AI 劝阻"),
           ("语义", "warn / alert", "#E0A45E / #DE6B5E", "80% 预警 / 100% 告警；不进常规图表配色"),
           ("圆角", "r-xs → r-xl", "6 / 10 / 14 / 20 / 28 px（+ pill 999）", "五档封顶；卡片默认 r-md，弹层 r-lg"),
           ("阴影", "sh-1 / sh-2", "0 2px 8px rgba(84,66,48,.06) / 0 10px 24px rgba(84,66,48,.10)",
            "暖棕投影，禁止纯黑或纯灰（SRS 4.1）"),
           ("动效", "hover / press / enter", "上浮 2px·180ms 缓出 / scale(.98)·120ms / 淡入 240ms", "缓动 cubic-bezier(.2,.8,.2,1)"),
           ("字体", "sans / mono", "系统中文栈（苹方/微软雅黑）+ Inter；等宽 Consolas", "金额与数字一律 tabular-nums"),
           ("字号", "11 / 12 / 13 / 15 / 22", "辅助 / 正文 / 卡片标题 / 页面标题 / 关键数字", "行高 1.5；不引入第四档字重"),
           ("栅格", "内容宽 / 侧栏 / 间距", "1200 / 232 / 8 的倍数", "断点 375 · 768 · 1024 · 1280；移动端最小 375 无横向滚动"),
           ("图标", "lucide", "16 / 20 / 24，stroke 1.75", "统一 Lucide 线性图标；严禁 emoji 充当图标")],
          [1.7, 3.0, 5.4, 6.5], zebra="FDFBF7")

    h3(doc, "反廉价红线（实现期逐条自检）")
    bullets(doc, [
        "禁止 emoji 充当图标；禁止使用图片 logo 代替文字品牌名。",
        "禁止原生未修饰的表单控件（input/select/date 必须套用统一描边、圆角、聚焦光晕）。",
        "禁止「暂无数据」四个字的干瘪空态：必须有柔色几何插画 + 一句引导文案 + 一个主动作。",
        "禁止转圈 spinner：加载一律 shimmer 骨架屏，且骨架形状要与真实内容同构。",
        "禁止硬编码色值：任何 #RRGGBB 只允许出现在 globals.css 的令牌定义处。",
        "禁止纯黑/纯灰阴影与纯黑文字；深色主题整体不做，避免与「手账」气质冲突。",
    ])


# --------------------------------------------------------------------------- 3 信息架构
def sec_ia(doc):
    h1(doc, "3", "信息架构与导航")
    para(doc,
         "系统是单人自托管应用，没有多租户、没有登录后的角色差异，因此导航只围绕「今天花了多少 / 记一笔 / 该不该买」三条主线组织。"
         "桌面端用左侧固定侧栏（232px），移动端收成底部 5 项 Tab；P1/P2 的入口在模块关闭时整块消失，不出现灰化占位。", after=8)

    tree = [
        ("/", "仪表盘 · 月度总支出 / 预算进度 / 分类分布 / 趋势 / 待办"),
        ("/ledger", "账本 · 多条件筛选 + 分页列表"),
        ("　　└ /ledger/[id]", "交易详情与编辑 · 退款关联 · 软删除"),
        ("/import", "导入中心 · 三入口 + 导入历史"),
        ("　　├ /import/csv", "CSV 导入（四步：选文件 → 预览 → 入账 → 结果）"),
        ("　　├ /import/screenshot", "截图导入 · 本地 OCR 校对 · 疑似重复标记"),
        ("　　└ /import/quick", "快捷填写 · 无单号零散收支"),
        ("/inbox", "待分类收件箱 · 逐条归类 / 沉淀规则"),
        ("/categories", "分类与规则 · CRUD + 规则测试器"),
        ("/budget", "预算与预警 · 双阈值 + 事件流"),
        ("/wardrobe　(P1)", "衣橱物品 · 卡片网格 + 日均成本 + 洞察"),
        ("　　├ /wardrobe/new", "物品建档 · 图片哈希去重"),
        ("　　└ /wardrobe/[id]", "物品详情 · 穿着时间线"),
        ("/intents　(P2)", "购买意图 · 状态分组 + 拦截统计"),
        ("　　├ /intents/new", "新建意图 · 相似匹配"),
        ("　　└ /intents/[id]", "意图详情 · 冷静期 + AI 劝阻 + 决策"),
        ("/settings", "设置 · 时薪 / 人设 / 模块开关 / 隐私"),
    ]
    table(doc, ["路由", "页面职责"], tree, [4.6, 12.0], size=8.4, zebra="FDFBF7")

    h2(doc, "3.1", "导航配置")
    table(doc,
          ["一级入口", "桌面侧栏", "移动底部 Tab", "说明"],
          [("仪表盘", "是（默认）", "Tab 1", "进入应用的默认落地页"),
           ("账本", "是", "Tab 2", "含交易详情抽屉"),
           ("导入账单", "是", "Tab 3", "中心页 + 三个子路由"),
           ("待分类收件箱", "是（带数量角标）", "Tab 4", "角标 = 未分类条数，>99 显示 99+"),
           ("分类与规则", "是", "「我的」二级", "低频管理项，不进主 Tab"),
           ("预算与预警", "是", "「我的」二级 + 仪表盘入口", "仪表盘卡片可直达"),
           ("衣橱物品（P1）", "是", "「我的」二级", "模块关闭时整块隐藏"),
           ("购买意图（P2）", "是（到期角标）", "「我的」二级 + 仪表盘横幅", "冷静期到期数以角标呈现"),
           ("设置", "是", "Tab 5「我的」", "含模块开关与隐私说明")],
          [3.0, 4.0, 4.2, 5.4], zebra="FDFBF7")
    caption(doc, "注：移动端 5 个 Tab 为「仪表盘 / 账本 / 导入 / 收件箱 / 我的」；「我的」聚合设置、衣橱、意图与分类管理。")
