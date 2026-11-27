import {
  Gauge,
  Home,
  Inbox,
  Receipt,
  Settings,
  Shirt,
  Tags,
  Target,
  Upload,
  User,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  /** 需要动态角标的入口，值由对应数据源提供 */
  badgeKey?: "inbox";
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

/** 侧栏分组（§3.1）：记账 / 管理 / 消费档案 / 购买意图 / 系统 */
export const NAV_GROUPS: NavGroup[] = [
  {
    title: "记账",
    items: [
      { href: "/", label: "仪表盘", icon: Home },
      { href: "/ledger", label: "账本", icon: Receipt },
      { href: "/import", label: "导入账单", icon: Upload },
      { href: "/inbox", label: "待分类收件箱", icon: Inbox, badgeKey: "inbox" },
    ],
  },
  {
    title: "管理",
    items: [
      { href: "/categories", label: "分类与规则", icon: Tags },
      { href: "/budget", label: "预算与预警", icon: Gauge },
    ],
  },
  {
    title: "消费档案",
    items: [{ href: "/wardrobe", label: "衣橱物品", icon: Shirt }],
  },
  {
    title: "购买意图",
    items: [{ href: "/intents", label: "购买意图", icon: Target }],
  },
  {
    title: "系统",
    items: [{ href: "/settings", label: "设置", icon: Settings }],
  },
];

/** 移动端底部 5 项（§3.1） */
export const MOBILE_TABS: NavItem[] = [
  { href: "/", label: "仪表盘", icon: Home },
  { href: "/ledger", label: "账本", icon: Receipt },
  { href: "/import", label: "导入", icon: Upload },
  { href: "/inbox", label: "收件箱", icon: Inbox },
  { href: "/settings", label: "我的", icon: User },
];

export function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
