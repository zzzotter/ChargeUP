import { ButtonLink, EmptyArt } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-2 text-center">
      <EmptyArt />
      <p className="text-sm font-semibold">页面不存在</p>
      <p className="max-w-[24rem] text-[10px] leading-relaxed text-ink-4">
        地址可能写错了，或该页面还没开工。侧栏与底部 Tab 里的入口都已接通。
      </p>
      <ButtonLink href="/" variant="ghost" className="mt-2">
        返回仪表盘
      </ButtonLink>
    </div>
  );
}
