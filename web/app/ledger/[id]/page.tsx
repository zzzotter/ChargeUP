import { TransactionDetail } from "@/components/ledger/transaction-detail";

export default async function LedgerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <TransactionDetail id={id} />;
}
