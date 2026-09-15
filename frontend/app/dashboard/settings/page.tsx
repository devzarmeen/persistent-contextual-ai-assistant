"use client";

import {
  CalendarDays,
  Check,
  FileText,
  Mail,
  Moon,
  Palette,
  Settings,
  ShieldCheck,
  Sun,
} from "lucide-react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { useTheme } from "@/lib/theme";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <DashboardShell>
      <div className="space-y-6">
        <section>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
              <Settings size={21} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Settings
              </h1>

              <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                Manage your assistant preferences and
                external integrations.
              </p>
            </div>
          </div>
        </section>

        <Card className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <Palette size={18} />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Appearance
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Switch between light and dark mode.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setTheme("light")}
              className={`flex items-center justify-between rounded-xl border p-4 text-left transition ${
                theme === "light"
                  ? "border-blue-500 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30"
                  : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-amber-500 shadow-sm dark:bg-slate-900">
                  <Sun size={19} />
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    Light
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Bright interface
                  </p>
                </div>
              </div>

              {theme === "light" && (
                <Check
                  size={18}
                  className="text-blue-600"
                />
              )}
            </button>

            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={`flex items-center justify-between rounded-xl border p-4 text-left transition ${
                theme === "dark"
                  ? "border-blue-500 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30"
                  : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-blue-300 shadow-sm">
                  <Moon size={19} />
                </div>

                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    Dark
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Dark interface
                  </p>
                </div>
              </div>

              {theme === "dark" && (
                <Check
                  size={18}
                  className="text-blue-600"
                />
              )}
            </button>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
              <ShieldCheck size={18} />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Google Workspace
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Connect Google to allow the assistant to
                work with Gmail, Calendar and Drive through
                verified actions.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <IntegrationItem
              icon={<Mail size={18} />}
              title="Gmail"
              description="Available through Google"
            />

            <IntegrationItem
              icon={<CalendarDays size={18} />}
              title="Calendar"
              description="Available through Google"
            />

            <IntegrationItem
              icon={<FileText size={18} />}
              title="Drive"
              description="Available through Google"
            />
          </div>

          <GoogleConnectButton />
        </Card>

        <Card className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
              <ShieldCheck size={18} />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Verified Actions
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                The assistant does not silently send emails
                or create calendar events. External actions
                go through the verification workflow first.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </DashboardShell>
  );
}

function IntegrationItem({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-slate-600 shadow-sm dark:bg-slate-900 dark:text-slate-300">
        {icon}
      </div>

      <p className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
        {title}
      </p>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

function GoogleConnectButton() {
  async function connectGoogle() {
    try {
      const token =
        localStorage.getItem("access_token");

      const response = await fetch(
        "http://127.0.0.1:8000/api/integrations/google/connect",
        {
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to connect Google.",
        );
      }

      if (data.authorization_url) {
        window.location.href =
          data.authorization_url;
      }
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : "Unable to connect Google.",
      );
    }
  }

  return (
    <button
      type="button"
      onClick={connectGoogle}
      className="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
    >
      Connect Google
    </button>
  );
}
