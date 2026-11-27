import { Image as ImageIcon, PenLine, Upload } from "lucide-react";

import { ButtonLink, Card, Chip, PageHeader } from "@/components/ui";

const ENTRIES = [
  {
    icon: Upload,
    title: "导入 CSV 账单",
    description: "支付宝 / 微信官方导出的 CSV，自动跳过表头、清洗乱码并幂等去重。",
    chips: ["支付宝 24 行表头", "微信 16 行", "GBK", "1000 条内 ≤3s"],
    href: null,
    day: "第 6 天",
  },
  {
    icon: ImageIcon,
    title: "截图识别（本地 OCR）",
    description: "上传账单列表截图，浏览器本地识别，原图不上传服务端。",
    chips: ["最多 8 张", "PNG / JPG", "不上传原图"],
    href: null,
    day: "第 6 天",
  },
  {
    icon: PenLine,
    title: "快捷填写",
    description: "无单号、无明细的一笔收支，30 秒录入；时间留空默认 12:00。",
    chips: ["来源 MANUAL", "自动分类", "无需单号"],
    href: "/import/quick",
    day: null,
  },
];

export default function ImportPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="导入账单" subtitle="三种入口 · 导入即可参与统计与预警" />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ENTRIES.map((entry) => {
          const Icon = entry.icon;
          return (
            <Card key={entry.title} className="flex flex-col gap-2.5 p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-coral-50 text-coral-ink">
                  <Icon size={14} />
                </span>
                <h2 className="text-[12px] font-semibold">{entry.title}</h2>
              </div>
              <p className="text-[10px] leading-relaxed text-ink-3">{entry.description}</p>
              <div className="flex flex-wrap gap-1">
                {entry.chips.map((chip) => (
                  <Chip key={chip}>{chip}</Chip>
                ))}
              </div>
              <div className="mt-auto pt-1">
                {entry.href ? (
                  <ButtonLink href={entry.href}>开始填写</ButtonLink>
                ) : (
                  <Chip tone="warn">{entry.day}实现</Chip>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      <p className="rounded-sm border border-dashed border-line bg-canvas px-3 py-2 text-[9.5px] leading-relaxed text-ink-4">
        导入历史、解析预览与失败行导出在 W05 / W06 的流程里，第 6 天实现；本页当前只做入口壳。
      </p>
    </div>
  );
}
