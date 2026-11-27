import Link from "next/link";
import type { ReactNode } from "react";

export function cx(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

/* ---------------------------------------------------------------- 页头 */

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-[15px] font-bold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 text-[11px] text-ink-3">{subtitle}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}

/* ---------------------------------------------------------------- 容器 */

export function Card({
  children,
  className,
  flat = false,
}: {
  children: ReactNode;
  className?: string;
  flat?: boolean;
}) {
  return (
    <section
      className={cx(
        "rounded-md border border-line",
        flat ? "bg-canvas" : "bg-surface shadow-1",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function CardHeader({
  title,
  hint,
  action,
}: {
  title: ReactNode;
  hint?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-2 px-4 pb-2.5 pt-3.5">
      <h2 className="text-[12px] font-semibold">
        {title}
        {hint ? <span className="ml-1.5 text-[10px] font-normal text-ink-4">{hint}</span> : null}
      </h2>
      {action ? <div className="flex shrink-0 items-center gap-1.5">{action}</div> : null}
    </div>
  );
}

/* ---------------------------------------------------------------- 按钮 */

const BTN_BASE =
  "press inline-flex items-center gap-1.5 rounded-pill text-[11px] font-semibold whitespace-nowrap";

const BTN_VARIANTS = {
  primary: "bg-coral px-3.5 py-2 text-ink-on-coral",
  dark: "bg-ink px-3.5 py-2 text-canvas",
  ghost: "border border-line bg-surface px-3 py-1.5 text-ink-2 hover:bg-sunken",
  tiny: "border border-line bg-surface px-2.5 py-1 text-[10px] text-ink-2 hover:bg-sunken",
} as const;

type Variant = keyof typeof BTN_VARIANTS;

export function Button({
  children,
  variant = "primary",
  className,
  type = "button",
  onClick,
}: {
  children: ReactNode;
  variant?: Variant;
  className?: string;
  type?: "button" | "submit";
  onClick?: () => void;
}) {
  return (
    <button type={type} onClick={onClick} className={cx(BTN_BASE, BTN_VARIANTS[variant], className)}>
      {children}
    </button>
  );
}

export function ButtonLink({
  href,
  children,
  variant = "primary",
  className,
}: {
  href: string;
  children: ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <Link href={href} className={cx(BTN_BASE, BTN_VARIANTS[variant], className)}>
      {children}
    </Link>
  );
}

/* ---------------------------------------------------------------- 标签 */

const CHIP_VARIANTS = {
  default: "border-line bg-sunken text-ink-2",
  coral: "border-coral-100 bg-coral-50 text-coral-ink",
  mint: "border-mint-100 bg-mint-50 text-mint-ink",
  lilac: "border-lilac-100 bg-lilac-50 text-lilac-ink",
  warn: "border-warn-100 bg-warn-50 text-warn-ink",
  alert: "border-alert-100 bg-alert-50 text-alert-ink",
} as const;

export function Chip({
  children,
  tone = "default",
  className,
}: {
  children: ReactNode;
  tone?: keyof typeof CHIP_VARIANTS;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-pill border px-2 py-0.5 text-[9.5px] whitespace-nowrap",
        CHIP_VARIANTS[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ---------------------------------------------------------------- 空态 / 骨架 */

export function EmptyArt() {
  return (
    <span className="relative mb-1 block h-14 w-24" aria-hidden>
      <span className="absolute bottom-0 left-2 h-8 w-14 rounded-md bg-coral-50" />
      <span className="absolute bottom-0 right-2 h-12 w-8 rounded-md bg-mint-50" />
      <span className="absolute right-7 top-0 h-6 w-6 rounded-full bg-lilac-50" />
    </span>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-1.5 px-6 py-10 text-center">
      <EmptyArt />
      <p className="text-xs font-semibold text-ink-2">{title}</p>
      <p className="max-w-[22rem] text-[10px] leading-relaxed text-ink-4">{description}</p>
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <span className={cx("skeleton block", className)} aria-hidden />;
}

/* ---------------------------------------------------------------- 其他 */

export function Divider({ className }: { className?: string }) {
  return <hr className={cx("border-0 border-t border-line-soft", className)} />;
}

export function DevNote({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-sm border border-dashed border-line bg-canvas px-3 py-2 text-[9.5px] leading-relaxed text-ink-4">
      {children}
    </p>
  );
}
