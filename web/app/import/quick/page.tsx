import { PageHeader } from "@/components/ui";
import { QuickEntryForm } from "@/components/quick-entry-form";

export default function QuickEntryPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="快捷填写"
        subtitle="无单号、无明细的一笔收支 · 已接入 POST /transactions（当前为开发桩）"
      />
      <QuickEntryForm />
    </div>
  );
}
