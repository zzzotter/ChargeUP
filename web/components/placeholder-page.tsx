import { ButtonLink, Card, Chip, PageHeader } from "@/components/ui";

/** 未实现页的统一外壳：导航可达、给出计划与线框编号，避免死链 */
export function PlaceholderPage({
  title,
  subtitle,
  day,
  board,
  note,
}: {
  title: string;
  subtitle: string;
  day: string;
  board: string;
  note: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title={title} subtitle={subtitle} />
      <Card className="flex flex-col items-center gap-2 px-6 py-12 text-center">
        <Chip tone="lilac">{board}</Chip>
        <p className="mt-1 text-xs font-semibold text-ink-2">该页面在{day}实现</p>
        <p className="max-w-[26rem] text-[10px] leading-relaxed text-ink-4">{note}</p>
        <div className="mt-2 flex items-center gap-2">
          <ButtonLink href="/ledger" variant="ghost">
            去账本
          </ButtonLink>
          <ButtonLink href="/" variant="ghost">
            返回仪表盘
          </ButtonLink>
        </div>
      </Card>
    </div>
  );
}
