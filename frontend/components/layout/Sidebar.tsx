"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Mail,
  MessageSquare,
  ShieldCheck,
  Settings,
  Sparkles,
} from "lucide-react";

const navigation = [
  {
    label: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "New Chat",
    href: "/dashboard/chat/new",
    icon: MessageSquare,
  },
  {
    label: "Memory",
    href: "/dashboard/memory",
    icon: Brain,
  },
  {
    label: "Documents",
    href: "/dashboard/documents",
    icon: FileText,
  },
  {
    label: "Calendar",
    href: "/dashboard/calendar",
    icon: CalendarDays,
  },
  {
    label: "Email",
    href: "/dashboard/email",
    icon: Mail,
  },
  {
    label: "Verification",
    href: "/dashboard/verification",
    icon: ShieldCheck,
  },
  {
    label: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white">
          <Sparkles size={19} />
        </div>

        <div>
          <p className="text-sm font-bold text-slate-900">
            ContextAI
          </p>
          <p className="text-[11px] text-slate-500">
            Persistent Assistant
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navigation.map((item) => {
          const Icon = item.icon;

          const active =
            pathname === item.href ||
            (item.href !== "/dashboard" &&
              pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              ].join(" ")}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 p-4">
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-semibold text-slate-700">
            Persistent Context
          </p>
          <p className="mt-1 text-[11px] leading-4 text-slate-500">
            Memories, documents and verified actions stay connected.
          </p>
        </div>
      </div>
    </aside>
  );
}