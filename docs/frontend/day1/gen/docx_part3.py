# -*- coding: utf-8 -*-
"""§6 线框、§7 接口草案、§8 组件、§9 互审、§10 映射、§11 自检。"""
import os

from docx.shared import Cm, Pt

from docx_base import (ASSETS, CORAL, FONT, INK, INK2, INK3, caption, cell_text,
                       h1, h2, h3, landscape, mono_block, note_box, para,
                       portrait, set_run_font, table, bullets)
import pages as wf

# 线框编号 → 页面编号
MAP = {"W01": "P01", "W02": "P02", "W03": "P03", "W04": "P04", "W05": "P05",
       "W06": "P06", "W07": "P07", "W08": "P08", "W09": "P09", "W10": "P10",
       "W11": "P11", "W12": "P12", "W13": "P14", "W14": "P15", "W15": "P16",
       "W16": "P17", "W17": "移动端"}


def wf_title(doc, no, route, title, pr, new_page=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    if new_page:
        p.paragraph_format.page_break_before = True
    set_run_font(p.add_run(no + "  "), FONT, 11, True, CORAL)
    set_run_font(p.add_run(title), FONT, 11, True, INK)
    set_run_font(p.add_run("　%s　·　%s" % (route, pr)), FONT, 8.5, False, INK3)


# --------------------------------------------------------------------------- 6 线框
def sec_wireframes(doc):
    h1(doc, "6", "线框（W01–W17）")
    para(doc,
         "线框采用桌面基准 1200px 画板（应用区 980px + 右侧说明栏），全部按暖白手账风绘制："
         "白色卡片浮在 #FDFBF7 底色上、1px 暖色描边、珊瑚粉/薄荷绿/丁香紫三种语义色仅用于强调，不做大面积铺色。"
         "线框中的图标为占位几何形，第 2 天起统一替换为 Lucide 线性图标。", after=8)
    note_box(doc, "关于线框的读法",
             "每张画板右侧窄栏是该页的线框说明（编号 ①②③…），与本表要点一一对应；"
             "线框只表达信息层级与交互位置，不表达最终视觉细节（间距、字号以 §2 令牌为准）。")

    h2(doc, "6.1", "线框索引与说明要点")
    rows = [("D01", "主流程总览",
             "记账闭环与干预闭环的全景图：实线为主干，虚线为旁路与回流；任何旁路失败都不阻塞记账主干；"
             "P1/P2 关闭时入口隐藏，P0 不受影响。")]
    for p in wf.PAGES:
        rows.append((p["no"], "%s %s" % (MAP[p["no"]], p["route"]),
                     "；".join(p["notes"][:3])))
    table(doc, ["编号", "对应页面", "说明要点"], rows,
          [1.15, 4.35, 11.1], size=7.0, zebra="FDFBF7", ls=1.1)
    caption(doc, "下一页起为横向画板：首张 D01 为流程总览，其后按 W01 → W17 顺序排列。")

    # ---- 横向画板
    landscape(doc)
    h2(doc, "6.2", "线框总览（横向画板）")
    wf_title(doc, "D01", "§5.1 / §6", "主流程总览", "P0–P2")
    doc.add_picture(os.path.join(ASSETS, "D01.png"), width=Cm(25.2))
    caption(doc, "D01 · 记账闭环（上）与干预闭环（下）· 对应流程 F1–F12（§5.2）", 8, INK3, after=0)

    for i, p in enumerate(wf.PAGES):
        wf_title(doc, p["no"], p["route"], p["title"], p["pr"], new_page=True)
        img = os.path.join(ASSETS, p["no"] + ".png")
        doc.add_picture(img, width=Cm(25.2))
        caption(doc, "%s · %s %s · 对应页面 %s"
                % (p["no"], p["route"], p["title"], MAP[p["no"]]), 8, INK3, after=0)

    portrait(doc)


# --------------------------------------------------------------------------- 7 接口
ENDPOINTS = [
    ("GET", "/api/v1/transactions", "账本分页列表", "month, source, categoryId, direction, q, page, pageSize, sort；返回 Page<Transaction>"),
    ("POST", "/api/v1/transactions", "快捷填写 / 手动新建", "body: TransactionInput；返回 Transaction（含生成的 externalId）"),
    ("GET", "/api/v1/transactions/{id}", "交易详情", "返回 Transaction（含退款关联与分类来源）"),
    ("PATCH", "/api/v1/transactions/{id}", "编辑分类/金额/时间/备注", "source 与 externalId 只读，传了也忽略"),
    ("DELETE", "/api/v1/transactions/{id}", "软删除（移入回收）", "写 deleted_at，返回 204；硬删除一律 405 HARD_DELETE_FORBIDDEN"),
    ("POST", "/api/v1/transactions/{id}/restore", "从回收恢复", "清空 deleted_at"),
    ("GET", "/api/v1/transactions/inbox", "待分类收件箱", "categoryId = null 且未删除；返回 Page<Transaction>"),
    ("POST", "/api/v1/transactions/batch-classify", "批量归类", "body: {ids[], categoryId, createRule?: {keyword}}"),
    ("GET", "/api/v1/categories", "分类列表", "type=EXPENSE|INCOME；含内置与自定义，标注 source"),
    ("POST", "/api/v1/categories", "新建分类", "name, type, color"),
    ("PATCH", "/api/v1/categories/{id}", "修改分类", "改名/改色/停用"),
    ("DELETE", "/api/v1/categories/{id}", "删除分类", "存在交易引用时 409，需先迁移"),
    ("GET", "/api/v1/categories/suggest", "分类建议（快捷填写用）", "name=商户名；返回 {categoryId, matchedBy, ruleKeyword}"),
    ("GET", "/api/v1/category-rules", "规则列表", "按优先级排序（用户 > 内置）"),
    ("POST", "/api/v1/category-rules", "新增规则", "keyword, categoryId；重复 409"),
    ("DELETE", "/api/v1/category-rules/{id}", "删除规则", "内置规则只读，返回 409"),
    ("POST", "/api/v1/category-rules/test", "规则干跑测试", "body: {name}；返回命中规则与分类，不写库"),
    ("POST", "/api/v1/imports/csv", "CSV 导入（解析 + 入库）", "multipart；≤10MB；返回 ImportReport；耗时 ≤3s（1000 条内）"),
    ("POST", "/api/v1/imports/screenshot-candidates", "截图候选批量入账", "body: {rows[], skippedClientIds[]}；source=SCREENSHOT"),
    ("GET", "/api/v1/imports", "导入历史", "Page<ImportRecord>；含结果统计与失败原因"),
    ("GET", "/api/v1/imports/{id}/report", "导入报告详情", "失败行明细（行号、原因、原始片段已脱敏）"),
    ("GET", "/api/v1/stats/summary", "仪表盘概要", "month；totalExpense, totalIncome, excludedRefundCount, excludedTransferCount, uncategorizedCount"),
    ("GET", "/api/v1/stats/monthly", "月度趋势", "months=6；返回 [{month, expense}]"),
    ("GET", "/api/v1/stats/categories", "分类分布", "month；返回 [{categoryId, name, amount, ratio}]，颜色由前端令牌映射"),
    ("GET", "/api/v1/budget", "预算与阈值", "month；返回 {amount, warnThreshold, alertThreshold}"),
    ("PUT", "/api/v1/budget", "保存预算与阈值", "校验 warn < alert，单位分"),
    ("GET", "/api/v1/alerts", "预警事件流", "Page<AlertEvent>；level、period、read"),
    ("PATCH", "/api/v1/alerts/{id}", "标记已读", "body: {read: true}"),
    ("GET", "/api/v1/wardrobe-items", "衣橱列表（P1）", "sort=purchasedAt|dailyCost|category, q, page"),
    ("POST", "/api/v1/wardrobe-items", "物品建档（P1）", "name, price, purchasedAt, categoryId, firstWornAt?, imageHash?"),
    ("GET", "/api/v1/wardrobe-items/{id}", "物品详情（P1）", "含 dailyCost, daysSince, wornTimeline"),
    ("PATCH", "/api/v1/wardrobe-items/{id}", "编辑物品（P1）", "同上字段；图片变更需重新哈希"),
    ("DELETE", "/api/v1/wardrobe-items/{id}", "软删除（P1）", "写 deleted_at"),
    ("GET", "/api/v1/purchase-intents", "意图列表（P2）", "status 过滤；返回倒计时与决策结果"),
    ("POST", "/api/v1/purchase-intents", "新建意图（P2）", "itemName, price, imageUrl?, link?, reason?；初始 CREATED"),
    ("GET", "/api/v1/purchase-intents/{id}", "意图详情（P2）", "含 coolingEndsAt、decision、deferredOnce"),
    ("POST", "/api/v1/purchase-intents/{id}/similar", "相似度检测（P2）", "元数据粗筛 + CLIP 精排；返回 [{itemId, name, similarity, dailyCost}]"),
    ("POST", "/api/v1/purchase-intents/{id}/persuasion", "生成 AI 劝阻（P2）", "body: {persona}；8s 超时返回模板文案 degraded=true"),
    ("POST", "/api/v1/purchase-intents/{id}/decision", "决策（P2）", "body: {decision}；非法流转 409；延期仅一次"),
    ("POST", "/api/v1/purchase-intents/{id}/defer", "延期 48h（P2）", "仅 COOLING_DOWN 可用，二次延期 409"),
    ("GET", "/api/v1/settings", "读取设置", "hourlyRate, persona, modules{wardrobe,intents,feedback}"),
    ("PATCH", "/api/v1/settings", "保存设置", "同上；hourlyRate 为空表示不参与工时换算"),
]

ENUMS = [
    ("TxSource", "ALIPAY · WECHAT · SCREENSHOT · MANUAL", "决定来源标签颜色与是否可编辑；SCREENSHOT/MANUAL 的 externalId 由系统生成"),
    ("Direction", "EXPENSE · INCOME · TRANSFER", "TRANSFER 不参与支出统计（F-P0-03）；前端不提供「转账」手动录入，仅由导入识别"),
    ("CategoryType", "EXPENSE · INCOME", "分类列表按此分栏"),
    ("IntentStatus", "CREATED · COOLING_DOWN · DECIDED", "状态机不可逆；延期时不回到 CREATED，而是保持 COOLING_DOWN 并置 deferredOnce"),
    ("Decision", "BOUGHT · ABANDONED · DEFERRED", "DEFERRED 为一次性延期，仍须最终决策为 BOUGHT/ABANDONED"),
    ("AlertLevel", "WARN · ALERT", "对应 80% / 100% 阈值；同周期同 level 只生成一条"),
    ("AlertStatus", "UNREAD · READ", "仪表盘角标只统计 UNREAD"),
    ("ModuleKey", "wardrobe · intents · feedback", "前端据此隐藏入口；关闭后直接访问路由 → 403"),
    ("Persona", "DIRECT · GENTLE · RATIONAL", "直白 / 委婉 / 理性，映射到 AI Prompt 与文案标签"),
    ("CategorySource", "RULE · BUILTIN · USER · null", "null 表示未命中，交易进入收件箱"),
]

TS = """// 金额一律为「分」的整数，禁止浮点
export type AmountCents = number;

export type TxSource = 'ALIPAY' | 'WECHAT' | 'SCREENSHOT' | 'MANUAL';
export type Direction = 'EXPENSE' | 'INCOME' | 'TRANSFER';
export type IntentStatus = 'CREATED' | 'COOLING_DOWN' | 'DECIDED';
export type Decision = 'BOUGHT' | 'ABANDONED' | 'DEFERRED';
export type AlertLevel = 'WARN' | 'ALERT';

export interface Transaction {
  id: string;
  source: TxSource;
  externalId: string;                // CSV 用外部单号；截图/手动为系统生成
  merchant: string;                  // 商户 / 名称
  amount: AmountCents;               // 非负整数，方向由 direction 决定
  direction: Direction;
  categoryId: string | null;         // null → 待分类收件箱
  occurredAt: string;                // ISO 8601 带时区 2026-11-24T18:20:11+08:00
  note: string | null;
  refundOfTransactionId: string | null;
  categorySource: CategorySource;
  deletedAt: string | null;
}

export interface TransactionInput {
  merchant: string;
  amount: AmountCents;
  direction: 'EXPENSE' | 'INCOME';
  occurredAt: string;
  categoryId?: string | null;
  note?: string | null;
}

export interface Page<T> {
  items: T[]; page: number; pageSize: number; total: number;
}

export interface ImportReport {
  importId: string;
  recognized: number; skippedHeaderRows: number;
  duplicated: number; failed: number;
  created: number;
  failures: { rowNumber: number; reason: string; raw?: string }[];  // raw 已脱敏
  durationMs: number;
}

export interface StatsSummary {
  month: string;
  totalExpense: AmountCents; totalIncome: AmountCents;
  excludedRefundCount: number; excludedTransferCount: number;
  uncategorizedCount: number;
}

export interface Budget {
  month: string; amount: AmountCents;
  warnThreshold: number;   // 0.8
  alertThreshold: number;  // 1.0
}

export interface AlertEvent {
  id: string; level: AlertLevel; period: string;
  threshold: number; actual: AmountCents; createdAt: string;
  read: boolean;
}

export interface WardrobeItem {
  id: string; name: string; price: AmountCents;
  purchasedAt: string; firstWornAt: string | null;
  categoryId: string | null; imageHash: string | null;
  dailyCost: AmountCents;   // price / max(1, daysSince(firstWornAt))
  daysSince: number;
  deletedAt: string | null;
}

export interface PurchaseIntent {
  id: string; itemName: string; price: AmountCents;
  imageUrl: string | null; link: string | null; reason: string | null;
  status: IntentStatus;
  coolingEndsAt: string | null;
  decision: Decision | null;
  deferredOnce: boolean;
  createdAt: string;
}

export interface SimilarMatch {
  itemId: string; name: string;
  similarity: number;       // 0..1
  dailyCost: AmountCents;
  purchasedAt: string;
}

export interface Persuasion {
  text: string;
  persona: 'DIRECT' | 'GENTLE' | 'RATIONAL';
  degraded: boolean;        // true = 模板文案（AI 超时降级）
  workHours: number | null; // 未设置时薪时为 null
}

export interface ApiError {
  code: string; message: string;
  details?: { field: string; reason: string }[];
}"""

ERRORS = [
    ("字段校验失败", "422", "VALIDATION_ERROR", "字段内联错误，聚焦第一个非法字段，不弹全局弹窗"),
    ("唯一约束冲突（重复交易/规则）", "409", "DUPLICATE_RESOURCE", "导入时静默跳过并计入「重复」；手动创建时提示已存在"),
    ("分类/交易/意图不存在", "404", "NOT_FOUND", "列表刷新；详情页展示「不存在或已移入回收」"),
    ("硬删除被拦截", "405", "HARD_DELETE_FORBIDDEN", "前端只提供「移入回收」，不出现永久删除文案"),
    ("模块已关闭", "409", "MODULE_DISABLED", "跳 403 页 + 返回仪表盘；入口本身已隐藏，属兜底"),
    ("意图状态非法流转", "409", "INVALID_STATE_TRANSITION", "提示「该意图已完成决策」，刷新详情"),
    ("AI 劝阻超时", "200", "DEGRADED_TEMPLATE", "persuasion.degraded=true，卡片标注「模板文案」，决策按钮照常可用"),
    ("OCR 引擎不可用", "—", "客户端能力缺失", "整批提示 + 「重试」「改用快捷填写」，不发送任何请求"),
]


def sec_api(doc):
    h1(doc, "7", "接口约定草案（联调用）")
    para(doc,
         "本节是前端向后端提出的最小契约：字段名、类型、枚举、错误码。第 5 天联调后以后端 Swagger（OpenAPI）为准，"
         "但在此之前，前端按本节生成 mock 与类型定义，后端按本节实现，避免第 5 天出现「字段对不上、名字不一致」的返工。", after=8)

    h2(doc, "7.1", "通用约定")
    bullets(doc, [
        ("前缀与格式：", "统一 /api/v1，JSON 传输，UTF-8；请求与响应字段使用 lowerCamelCase。"),
        ("金额：", "所有金额字段名为 amount / price / totalExpense 等，类型为整数「分」，单位写在字段注释里；响应不返回「元」字符串。"),
        ("时间：", "ISO 8601 带时区偏移（+08:00），不做本地化字符串传输；前端用 date-fns 格式化。"),
        ("分页：", "page 从 1 开始、pageSize 默认 20（上限 100），响应统一 {items, page, pageSize, total}。"),
        ("排序：", "sort 采用 `field,-field` 形式（负号降序），前端不拼接 SQL 语义。"),
        ("幂等：", "交易唯一键 (source, external_id)；CSV 导入按此幂等去重；截图/手动由服务端生成 external_id。"),
        ("软删除：", "DELETE 语义为软删除，返回 204；回收站数据默认不出现在列表与统计中。"),
        ("错误结构：", "{code, message, details?}；code 为稳定枚举，message 可展示给用户（中文）。"),
    ])

    h2(doc, "7.2", "端点清单（草案）")
    table(doc, ["方法", "路径", "用途", "关键约定"], ENDPOINTS,
          [1.25, 4.9, 3.5, 6.95], size=7.4, zebra="FDFBF7")
    caption(doc, "共 %d 个端点：P0 28 个、P1 5 个、P2 7 个、设置 2 个。P1/P2 端点在后端可用模块开关整体下线。"
                 % len(ENDPOINTS))

    h2(doc, "7.3", "枚举定义（冻结）")
    table(doc, ["枚举", "取值", "前端约定"], ENUMS,
          [2.5, 6.2, 7.9], size=7.8, zebra="FDFBF7")

    h2(doc, "7.4", "TypeScript 类型草案")
    para(doc, "以下类型将直接落到 src/types/api.ts，作为 mock 与真实接口的共同契约。", 9, False, INK3, after=4)
    mono_block(doc, TS, 7.2)

    h2(doc, "7.5", "错误码与前端处理")
    table(doc, ["场景", "HTTP", "code", "前端处理"], ERRORS,
          [4.3, 1.3, 4.6, 6.4], size=7.8, zebra="FDFBF7")

    h2(doc, "7.6", "前端技术决策（第 2 天起生效）")
    table(doc, ["主题", "决策", "理由"],
          [("框架", "Next.js App Router + TypeScript（严格模式）", "SRS 硬约束；RSC 让首屏直出，利于 1.5s 首屏指标"),
           ("样式", "Tailwind CSS + shadcn/ui，令牌以 CSS Variables 注入", "令牌与 Tailwind 主题同源，杜绝硬编码色值"),
           ("数据获取", "RSC 直取 GET；写操作走客户端 fetch 后 router.refresh()", "不做全局状态库，减少层数"),
           ("表单", "react-hook-form + zod", "金额/日期等边界校验与后端 Pydantic 规则对齐"),
           ("图表", "Recharts（shadcn/ui charts）", "柱状图/环形图/进度环一套库解决，颜色走令牌"),
           ("金额工具", "lib/money.ts：formatCents / parseYuanToCents（字符串拆分，整数运算）", "避免 parseFloat 带来的精度问题"),
           ("日期", "date-fns", "时区与月份边界显式处理，不用 dayjs 插件"),
           ("OCR", "tesseract.js（Web Worker，本地）", "满足「原图不上传」的硬约束；失败可降级"),
           ("图标", "lucide-react", "SRS 强制统一线性图标"),
           ("测试", "Playwright（关键流程 E2E）+ Vitest（工具函数与组件）", "与集成的契约测试互补")],
          [2.4, 7.6, 6.6], size=7.8, zebra="FDFBF7")


# --------------------------------------------------------------------------- 8 组件
def sec_components(doc):
    h1(doc, "8", "共享组件清单")
    para(doc,
         "下列组件的边界在第 1 天定死，避免第 3 天之后各页面重复造轮子。命名与目录按 shadcn/ui 习惯："
         "components/ui 放原子组件，components/domain 放业务组件。", after=8)
    table(doc, ["组件", "用途", "关键状态 / Props", "复用页面"],
          [("AppShell", "侧栏 + 顶栏 + 内容区外层，负责断点切换", "activeRoute, modules{}", "全部"),
           ("SideNav / MobileTabBar", "桌面侧栏与移动底部 Tab", "items, badges{inbox, intents}", "全部"),
           ("PageHeader", "页面标题 + 副标题 + 右侧唯一主动作", "title, subtitle, action", "全部"),
           ("Card / SectionCard", "白卡容器，统一描边/圆角/阴影", "title, extra, dense", "全部"),
           ("StatCard", "KPI 卡（标签 + 大数字 + 说明）", "label, value, unit, hint, tone", "P01 P11 P14"),
           ("AmountText", "金额格式化与等宽对齐", "cents, direction, size", "全部"),
           ("BudgetBar / BudgetGauge", "预算进度条与环形进度", "used, total, warn, alert", "P01 P10"),
           ("CategoryDonut / TrendBarChart", "分类分布环形图与月度柱状趋势", "data[], palette", "P01"),
           ("DataTable", "带表头、行高、分页的列表容器", "columns, rows, loading, empty, error", "P02 P05 P08"),
           ("Stepper", "多步导入流程的步骤条", "steps[], active", "P05 P06"),
           ("FileDropzone", "拖拽/点选上传，含格式与体积校验", "accept, maxFiles, maxSize, onFiles", "P05 P06 P12"),
           ("OcrCandidateRow", "截图表单行，字段可编辑 + 状态标签", "row, onChange, onExclude", "P06"),
           ("QuickEntryForm", "快捷填写表单（三处入口复用）", "defaults, onSubmit, mode", "P07"),
           ("RuleTester", "规则干跑测试器", "onTest, result", "P09"),
           ("EmptyState", "柔色几何插画 + 引导文案 + 主动作", "art, title, desc, action", "全部"),
           ("Shimmer", "骨架屏基元（行/块/卡三种形状）", "shape, width, height", "全部"),
           ("IntentCountdown", "冷静期倒计时（秒级，不阻塞交互）", "endsAt, onExpire", "P14 P16"),
           ("MatchCard", "相似物品卡（相似度 + 日均成本对照）", "match, onOpen", "P14 P15"),
           ("PersonaSwitch", "劝阻人设切换（直言/委婉/理性）", "value, onChange", "P16 P17"),
           ("ConfirmDialog / Toast", "二次确认与全局反馈", "title, desc, tone", "全部")],
          [3.3, 5.6, 5.2, 2.5], size=7.8, zebra="FDFBF7")


# --------------------------------------------------------------------------- 9 互审
QUESTIONS = [
    ("Q1", "分页用 offset 还是 cursor？", "offset（page/pageSize），账本按时间倒序，数据量个人级不构成性能问题", "P02/P05/P14 的列表实现"),
    ("Q2", "「月度」边界与时区？", "以服务端 Asia/Shanghai 的自然月为准，occurredAt 按该时区归档；跨月退款仍计入发生月", "P01/P10 统计与事件 period"),
    ("Q3", "CSV 导入是同步还是异步任务？", "同步；1000 条以内 ≤3s，直接返回 ImportReport；超时由后端拆批", "P05 四步流程是否需要轮询"),
    ("Q4", "截图候选如何入账？", "单接口批量 POST /transactions/batch-classify（含 skipClientIds），source=SCREENSHOT", "P06 底部汇总与入账按钮"),
    ("Q5", "疑似重复的判定与窗口？", "同 (date, amount, merchant) 且 7 天内；仅标记，不拦截；由用户显式排除", "P06 标黄逻辑与默认保留"),
    ("Q6", "BOUGHT 是否自动生成交易？", "不自动；前端预填快捷填写，由用户确认后落库，避免干预流程污染账本", "P16 决策分支"),
    ("Q7", "预算作用域与事件去重？", "默认仅总额预算，分类预算为可选扩展；事件按 (period, level) 去重", "P10 双阈值与事件流"),
    ("Q8", "AI 劝阻的失败形态？", "后端 200 + degraded=true 的模板文案（同时记录 504 日志）；前端只判 degraded", "P16 劝阻卡与「模板」标记"),
    ("Q9", "前端如何感知 P1/P2 关闭？", "GET /settings 返回 modules{wardrobe,intents,feedback}；导航与路由双层拦截", "全部导航与 403 兜底页"),
    ("Q10", "软删除数据是否可恢复？", "P0 提供恢复接口但不做回收站 UI（P12 之后视时间补）；列表与统计默认排除", "P03 详情页的删除入口"),
]

FIXTURES = [
    ("CSV 正常账单", "支付宝（24 行表头）、微信（16 行表头）各一份，含收入与支出", "解析成功、统计与人工核对一致"),
    ("CSV 坏账单", "空行、缺列、乱码（GBK）、金额带千分位、表头缺失", "不崩溃；坏行给出行号与原因；其余照常入账"),
    ("重复导入", "同一份 CSV 连续导入两次", "第二次 0 新增、全部计入「重复」"),
    ("退款与转账", "7 天内金额相反的退款对、跨 7 天退款、转账记录", "退款从支出剔除；转账不计入月度支出"),
    ("截图样例", "支付宝/微信账单列表各 1 张，另附 1 张低质量图", "金额/商户/日期识别正确；低质量图给出失败提示与快捷填写兜底"),
    ("疑似重复截图", "同商户同金额同日期的两张截图", "标记疑似重复且可排除，默认保留"),
    ("预算阈值", "构造使支出跨 80%、跨 100% 的数据", "各触发一次事件；重复导入不再触发"),
    ("P1 边界", "同图片两次上传、首穿日期为空、首穿日期为未来", "哈希去重提示；日均成本按 max(1, 天数) 兜底不报错"),
    ("P2 状态机", "合法：CREATED→COOLING_DOWN→DECIDED；非法：CREATED→DECIDED", "合法流转通过；非法流转 409 且前端提示"),
    ("P2 相似度", "同款不同色、视觉高度相似、完全无关各一组", "前两组返回匹配（含相似度与日均成本），第三组为空"),
]


def sec_review(doc):
    h1(doc, "9", "互审清单与待确认问题")
    para(doc,
         "按分工表，第 1 天需要「三人当天互审；确定接口约定、字段和枚举」。本节给出可执行的议程、"
         "需要拍板的问题清单（含默认决策）以及测试数据清单，会议只需逐条勾选即可产出结论。", after=8)

    h2(doc, "9.1", "互审议程（建议 60 分钟）")
    table(doc, ["时段", "内容", "产出"],
          [("00–10", "前端讲页面清单与状态矩阵（§4）", "确认 17 个路由与三态口径"),
           ("10–30", "前端讲用户流程与降级路径（§5），后端对每条流程指出实现风险", "确认 F2/F3/F11 三条降级路径"),
           ("30–45", "逐条过接口约定与枚举（§7）：字段名、金额单位、分页、错误码", "冻结 §7.3 枚举与 §7.2 端点命名"),
           ("45–55", "过待确认问题 Q1–Q10（§9.2），无异议即采用默认决策", "形成决议记录"),
           ("55–60", "集成给出测试数据清单确认与 P0 验收项补充（§9.3）", "确认 fixture 负责人与日期")],
          [1.8, 9.4, 5.4], size=8, zebra="FDFBF7")

    h2(doc, "9.2", "待确认问题（含默认决策）")
    para(doc, "会议未提出异议的条目，直接按「默认决策」进入第 2 天开发，并在决议表中记「默认通过」。", 9, False, INK3, after=4)
    table(doc, ["编号", "问题", "默认决策", "影响范围"], QUESTIONS,
          [1.1, 5.4, 7.1, 3.0], size=7.6, zebra="FDFBF7")

    h2(doc, "9.3", "测试数据清单（与集成共同维护）")
    table(doc, ["类别", "内容", "期望结果"], FIXTURES,
          [2.6, 8.4, 5.6], size=7.8, zebra="FDFBF7")

    h2(doc, "9.4", "互审决议记录（会中填写）")
    rows = [(str(i + 1), "", "", "") for i in range(10)]
    table(doc, ["序号", "议题 / 结论", "负责人", "状态"], rows,
          [1.2, 10.2, 2.6, 2.6], size=8, zebra="FDFBF7")
    caption(doc, "状态取值：默认通过 / 需修改 / 挂起（附期限）。会后 24 小时内由前端把结论回写到本文 §7 与 §9.2。")


# --------------------------------------------------------------------------- 10 映射
def sec_plan(doc):
    h1(doc, "10", "后续任务映射（第 2–21 天 · 前端列）")
    para(doc,
         "把分工表里前端那一列逐行对齐到本文档的输入，确保第 2 天开工时不再回头讨论「这页到底要什么」。", after=8)
    table(doc, ["天", "分工表前端任务", "本文档对应输入", "完成判定"],
          [("2", "初始化 Next.js、布局、设计令牌", "§2 令牌、§3 导航", "令牌可用、AppShell 三断点不破"),
           ("3", "做导航、账本列表和表单壳", "P02/P04/P07、W02/W04/W07", "导航可跳转，列表与表单含三态占位"),
           ("4", "实现快捷填写表单和账本列表", "W07/W02、F4", "校验与分类建议可用（mock 数据）"),
           ("5", "接入交易列表、快捷录入 API", "§7.2 交易端点", "mock 换真实数据，筛选与分页走 URL"),
           ("6", "完成导入页面与结果反馈", "W05/W06、F2/F3", "CSV 四步走通，失败行可导出"),
           ("7", "实现分类管理与待分类收件箱", "W08/W09、F5/F6", "归类后角标递减、规则测试器可用"),
           ("8", "实现账本筛选、交易详情与编辑", "W02/W03、F8", "URL 可分享，软删除走二次确认"),
           ("9", "实现仪表盘卡片与图表布局", "W01、§7.2 统计端点", "图表与库内数据一致，颜色走令牌"),
           ("10", "实现预算设置与预警展示", "W10、F7", "双阈值保存与事件展示正确"),
           ("11", "完善加载、空、错误状态和移动端布局", "§4.2、W17、F12", "每页三态齐全，375px 无横向滚动"),
           ("12", "修复 P0 页面联调问题，统一交互", "§4.2 与全文", "P0 页面无严重缺陷，交互一致"),
           ("13", "实现物品档案列表、录入和图片上传", "W11/W12、F9", "哈希去重提示、日均成本正确"),
           ("14", "展示物品时间线、日均成本及反馈文案", "P13、F9", "首穿缺失兜底，反馈可一键关闭"),
           ("15", "实现意图录入、列表和状态展示", "W13/W14、F10", "状态枚举与后端一致"),
           ("16", "实现冷静期倒计时与决策操作", "W15、F11", "48h 默认、延期一次、决策不可逆"),
           ("17", "实现相似匹配列表与购买意图详情", "W14/W15", "匹配卡含相似度与日均成本"),
           ("18", "实现劝阻文案、人设和工时展示", "W15、F11", "8s 超时降级为模板，前端无密钥"),
           ("19", "完成暖白视觉、图标、控件与响应式检查", "§2 与 §4.1", "无硬编码色值、无 emoji 图标"),
           ("20", "修复页面缺陷，检查桌面与手机核心流程", "全文", "桌面与移动核心流程各跑通一遍"),
           ("21", "完成演示流程和页面收尾", "§9.4 决议项", "演示脚本可完整走通")],
          [1.0, 6.0, 5.4, 4.2], size=7.6, zebra="FDFBF7")


# --------------------------------------------------------------------------- 11 自检
def sec_dod(doc):
    h1(doc, "11", "第 1 天完成定义自检")
    table(doc, ["交付项", "状态", "证据 / 位置"],
          [("页面清单（17 路由，含优先级与依赖接口）", "完成", "§4.1"),
           ("页面状态矩阵（加载/空/错误）", "完成", "§4.2"),
           ("用户流程 12 条（含失败与降级）", "完成", "§5.2、§5.1 主干图"),
           ("线框 17 张（P0 10 / P1 2 / P2 3 / 设置 1 / 移动端 1）+ 流程总览 D01", "完成", "§6.2 横向画板"),
           ("设计令牌与禁止清单", "完成", "§2"),
           ("接口草案（端点 / 枚举 / DTO / 错误码）", "完成", "§7"),
           ("共享组件清单", "完成", "§8"),
           ("互审议程与待确认问题（含默认决策）", "完成", "§9.1、§9.2"),
           ("测试数据清单", "完成", "§9.3"),
           ("第 2–21 天任务映射", "完成", "§10")],
          [8.6, 2.0, 5.9], size=8, zebra="FDFBF7")

    para(doc, "", after=10)
    note_box(doc, "下一步",
             "第 2 天按 §7.6 的技术决策初始化 Next.js 工程：先把 §2 的令牌落进 globals.css 与 tailwind.config，"
             "再按 §3 搭出 AppShell 与侧栏/底栏；第 3 天开始按 W02/W04/W07 做壳，不等后端接口。")
    para(doc, "", after=6)
    para(doc, "会签：前端 ________________　　后端 ________________　　集成 ________________　　日期 ________",
         9, False, INK3)
