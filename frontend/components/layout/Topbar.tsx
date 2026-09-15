"use client";

import {
  Bell,
  Menu,
} from "lucide-react";

import ThemeToggle from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth";

interface TopbarProps {
  onMenuClick?: () => void;
}

export default function Topbar({
  onMenuClick,
}: TopbarProps) {
  const { user } = useAuth();

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 md:hidden dark:text-slate-400 dark:hover:bg-slate-800"
          >
            <Menu size={19} />
          </button>
        )}

        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            ContextAI
          </p>
          <p className="hidden text-[11px] text-slate-400 sm:block">
            Persistent Contextual AI
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          title="Notifications"
        >
          <Bell size={17} />
        </button>

        <div className="hidden border-l border-slate-200 pl-3 sm:block dark:border-slate-800">
          <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
            {user?.name}
          </p>
          <p className="text-[11px] text-slate-400">
            {user?.email}
          </p>
        </div>
      </div>
    </header>
  );
}