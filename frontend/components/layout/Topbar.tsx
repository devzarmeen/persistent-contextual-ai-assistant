"use client";

import {
  Bell,
  CheckCircle2,
  Clock3,
  Menu,
  ShieldAlert,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import ThemeToggle from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { VerificationAction } from "@/lib/types";

interface TopbarProps {
  onMenuClick?: () => void;
}

export default function Topbar({
  onMenuClick,
}: TopbarProps) {
  const { user } = useAuth();

  const [notifications, setNotifications] =
    useState<VerificationAction[]>([]);

  const [open, setOpen] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const dropdownRef =
    useRef<HTMLDivElement>(null);

  const loadNotifications =
    useCallback(async () => {
      try {
        setLoading(true);

        const data = await apiFetch<
          VerificationAction[] | {
            actions: VerificationAction[];
          }
        >("/api/verification/actions");

        const actions = Array.isArray(data)
          ? data
          : Array.isArray(data.actions)
            ? data.actions
            : [];

        /*
         * Notifications are focused on actions that need
         * attention plus recently completed actions.
         */
        const sorted = [...actions]
          .sort(
            (a, b) =>
              new Date(b.created_at).getTime() -
              new Date(a.created_at).getTime(),
          )
          .slice(0, 20);

        setNotifications(sorted);
      } catch {
        setNotifications([]);
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    void loadNotifications();

    const interval = window.setInterval(
      () => {
        void loadNotifications();
      },
      15000,
    );

    return () => {
      window.clearInterval(interval);
    };
  }, [loadNotifications]);

  useEffect(() => {
    function handleOutsideClick(
      event: MouseEvent,
    ) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(
          event.target as Node,
        )
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );
    };
  }, []);

  const pendingCount =
    notifications.filter(
      (item) =>
        item.status === "PENDING" ||
        item.status === "APPROVED",
    ).length;

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 lg:px-6 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            aria-label="Open menu"
          >
            <Menu size={18} />
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

        {/* Notification */}
        <div
          ref={dropdownRef}
          className="relative"
        >
          <button
            type="button"
            onClick={() =>
              setOpen((current) => !current)
            }
            className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            title="Notifications"
            aria-label="Notifications"
          >
            <Bell size={17} />

            {pendingCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">
                {pendingCount > 9
                  ? "9+"
                  : pendingCount}
              </span>
            )}
          </button>

          {open && (
            <div className="absolute right-0 top-11 z-50 w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-950">
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    Notifications
                  </p>

                  <p className="text-[11px] text-slate-400">
                    Verification and action updates
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="max-h-[420px] overflow-y-auto">
                {loading ? (
                  <div className="flex items-center justify-center p-8">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <Bell
                      size={26}
                      className="mx-auto text-slate-300 dark:text-slate-700"
                    />

                    <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-300">
                      No notifications
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      You are all caught up.
                    </p>
                  </div>
                ) : (
                  notifications.map(
                    (notification) => (
                      <NotificationItem
                        key={
                          notification.id
                        }
                        notification={
                          notification
                        }
                      />
                    ),
                  )
                )}
              </div>
            </div>
          )}
        </div>

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

function NotificationItem({
  notification,
}: {
  notification: VerificationAction;
}) {
  const isPending =
    notification.status === "PENDING" ||
    notification.status === "APPROVED";

  const isVerified =
    notification.status === "VERIFIED";

  const isFailed =
    notification.status === "FAILED" ||
    notification.status === "REJECTED";

  let title = "Action update";

  if (
    notification.tool_name ===
    "create_calendar_event"
  ) {
    title = "Calendar action";
  } else if (
    notification.tool_name ===
    "send_email"
  ) {
    title = "Email action";
  }

  return (
    <div className="border-b border-slate-100 px-4 py-3 last:border-b-0 dark:border-slate-900">
      <div className="flex gap-3">
        <div
          className={[
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
            isPending
              ? "bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-300"
              : isVerified
                ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300"
                : isFailed
                  ? "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300"
                  : "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-300",
          ].join(" ")}
        >
          {isPending ? (
            <Clock3 size={16} />
          ) : isVerified ? (
            <CheckCircle2 size={16} />
          ) : (
            <ShieldAlert size={16} />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
              {title}
            </p>

            <span className="shrink-0 text-[10px] text-slate-400">
              #{notification.id}
            </span>
          </div>

          <p className="mt-1 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
            {getNotificationText(
              notification,
            )}
          </p>

          <p className="mt-1 text-[10px] text-slate-400">
            {formatDate(
              notification.created_at,
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

function getNotificationText(
  action: VerificationAction,
) {
  if (action.status === "PENDING") {
    return "Approval required before this external action can execute.";
  }

  if (action.status === "APPROVED") {
    return "Action approved and waiting for execution.";
  }

  if (action.status === "VERIFIED") {
    return "Action completed and verified successfully.";
  }

  if (action.status === "FAILED") {
    return (
      action.error ||
      "Action execution failed."
    );
  }

  if (action.status === "REJECTED") {
    return "Action was rejected.";
  }

  return `Action status: ${action.status}`;
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}