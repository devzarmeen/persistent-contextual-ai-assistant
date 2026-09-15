"use client";

import {
  CheckCircle2,
  Clock3,
  Mail,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type {
  VerificationAction,
} from "@/lib/types";

export default function EmailPage() {
  const [actions, setActions] = useState<
    VerificationAction[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    void loadEmailActions();
  }, []);

  async function loadEmailActions() {
    try {
      setError("");

      const data = await apiFetch<
        VerificationAction[] | {
          actions: VerificationAction[];
        }
      >(
        "/api/verification/actions?tool_name=send_email",
      );

      const normalized = Array.isArray(data)
        ? data
        : Array.isArray(data.actions)
          ? data.actions
          : [];

      setActions(normalized);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load email actions.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <section>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
              <Mail size={21} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Email
              </h1>

              <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                Review Gmail actions and their verification
                evidence.
              </p>
            </div>
          </div>
        </section>

        <Card className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
              <ShieldCheck size={18} />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Verified Email Actions
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                The assistant must receive approval before
                an email can be sent.
              </p>
            </div>
          </div>
        </Card>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-5 dark:border-slate-800">
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Email Action History
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Gmail operations processed through the
              verification workflow.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center p-10">
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400" />
                Loading email actions...
              </div>
            </div>
          ) : actions.length === 0 ? (
            <div className="p-10 text-center">
              <Mail
                size={30}
                className="mx-auto text-slate-300 dark:text-slate-700"
              />

              <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                No email actions yet.
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Email actions created by the assistant
                will appear here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {actions.map((action) => (
                <EmailAction
                  key={action.id}
                  action={action}
                />
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}

function EmailAction({
  action,
}: {
  action: VerificationAction;
}) {
  const status = action.status;

  const statusConfig =
    status === "VERIFIED"
      ? {
          icon: <CheckCircle2 size={16} />,
          text: "Verified",
          className:
            "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
        }
      : status === "REJECTED"
        ? {
            icon: <XCircle size={16} />,
            text: "Rejected",
            className:
              "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
          }
        : status === "PENDING" ||
            status === "APPROVED"
          ? {
              icon: <Clock3 size={16} />,
              text:
                status === "PENDING"
                  ? "Pending approval"
                  : "Approved",
              className:
                "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
            }
          : {
              icon: <Clock3 size={16} />,
              text: status,
              className:
                "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
            };

  return (
    <div className="p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
              Email Send
            </p>

            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusConfig.className}`}
            >
              {statusConfig.icon}
              {statusConfig.text}
            </span>
          </div>

          <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-600 dark:bg-slate-950 dark:text-slate-300">
            {formatRequest(action.request)}
          </pre>
        </div>

        <div className="shrink-0 text-xs text-slate-400">
          {formatDate(action.created_at)}
        </div>
      </div>

      {action.result && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <p className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
            Result
          </p>

          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs leading-5 text-emerald-700 dark:text-emerald-400">
            {action.result}
          </pre>
        </div>
      )}

      {action.evidence && (
        <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
          <p className="text-xs font-semibold text-blue-800 dark:text-blue-300">
            Verification Evidence
          </p>

          <p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-blue-700 dark:text-blue-400">
            {action.evidence}
          </p>
        </div>
      )}
    </div>
  );
}

function formatRequest(value: string) {
  try {
    return JSON.stringify(
      JSON.parse(value),
      null,
      2,
    );
  } catch {
    return value;
  }
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}