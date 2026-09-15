"use client";

import {
  CheckCircle2,
  Clock3,
  Play,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type {
  VerificationAction,
} from "@/lib/types";

interface VerificationActionsResponse {
  actions: VerificationAction[];
}

export default function VerificationPage() {
  const [actions, setActions] =
    useState<VerificationAction[]>([]);
  const [loading, setLoading] =
    useState(true);
  const [busyId, setBusyId] =
    useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadActions();
  }, []);

  async function loadActions() {
    setLoading(true);

    try {
      const data = await apiFetch<
        VerificationAction[] |
        VerificationActionsResponse
      >("/api/verification/actions");

      const normalized =
        Array.isArray(data)
          ? data
          : Array.isArray(data.actions)
            ? data.actions
            : [];

      setActions(normalized);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load verification actions.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function updateAction(
    id: number,
    operation:
      | "approve"
      | "reject"
      | "execute",
  ) {
    setBusyId(id);
    setError("");

    try {
      await apiFetch(
        `/api/verification/actions/${id}/${operation}`,
        {
          method: "POST",
        },
      );

      await loadActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Unable to ${operation} action.`,
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <section>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
              <ShieldCheck size={21} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Verification Center
              </h1>

              <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                Review and verify external actions before they
                are executed.
              </p>
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <Card className="p-8 text-center text-sm text-slate-500">
            Loading verification actions...
          </Card>
        ) : actions.length === 0 ? (
          <Card className="p-10 text-center">
            <CheckCircle2
              size={32}
              className="mx-auto text-emerald-500"
            />

            <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">
              No actions waiting for verification
            </h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              External actions requested by the assistant will
              appear here before execution.
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {actions.map((action) => (
              <ActionCard
                key={action.id}
                action={action}
                busy={
                  busyId === action.id
                }
                onApprove={() =>
                  void updateAction(
                    action.id,
                    "approve",
                  )
                }
                onReject={() =>
                  void updateAction(
                    action.id,
                    "reject",
                  )
                }
                onExecute={() =>
                  void updateAction(
                    action.id,
                    "execute",
                  )
                }
              />
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

function ActionCard({
  action,
  busy,
  onApprove,
  onReject,
  onExecute,
}: {
  action: VerificationAction;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
  onExecute: () => void;
}) {
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-semibold uppercase text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
              {action.tool_name}
            </span>

            <StatusBadge status={action.status} />
          </div>

          <h2 className="mt-3 text-base font-semibold text-slate-900 dark:text-white">
            {action.action_type}
          </h2>

          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600 dark:text-slate-300">
            {action.request}
          </p>

          {action.result && (
            <div className="mt-4 rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Result
              </p>

              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">
                {action.result}
              </p>
            </div>
          )}

          {action.evidence && (
            <div className="mt-3 rounded-xl bg-emerald-50 p-4 dark:bg-emerald-950/30">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
                Verification Evidence
              </p>

              <p className="mt-2 whitespace-pre-wrap text-sm text-emerald-800 dark:text-emerald-200">
                {action.evidence}
              </p>
            </div>
          )}

          {action.error && (
            <div className="mt-3 rounded-xl bg-red-50 p-4 dark:bg-red-950/30">
              <p className="text-sm text-red-700 dark:text-red-300">
                {action.error}
              </p>
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {action.status === "PENDING" && (
            <>
              <button
                type="button"
                onClick={onReject}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-lg border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950/40"
              >
                <XCircle size={16} />
                Reject
              </button>

              <button
                type="button"
                onClick={onApprove}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                <CheckCircle2 size={16} />
                Approve
              </button>
            </>
          )}

          {action.status === "APPROVED" && (
            <button
              type="button"
              onClick={onExecute}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <Play size={16} />
              {busy
                ? "Executing..."
                : "Execute"}
            </button>
          )}
        </div>
      </div>

      <div className="border-t border-slate-100 px-5 py-3 dark:border-slate-800">
        <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
          <span>
            Created{" "}
            {new Date(
              action.created_at,
            ).toLocaleString()}
          </span>

          {action.approved_at && (
            <span>
              Approved{" "}
              {new Date(
                action.approved_at,
              ).toLocaleString()}
            </span>
          )}

          {action.completed_at && (
            <span>
              Completed{" "}
              {new Date(
                action.completed_at,
              ).toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const config: Record<
    string,
    {
      label: string;
      className: string;
    }
  > = {
    PENDING: {
      label: "Pending",
      className:
        "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
    },
    APPROVED: {
      label: "Approved",
      className:
        "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
    },
    EXECUTING: {
      label: "Executing",
      className:
        "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300",
    },
    VERIFIED: {
      label: "Verified",
      className:
        "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
    },
    REJECTED: {
      label: "Rejected",
      className:
        "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    },
    FAILED: {
      label: "Failed",
      className:
        "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
    },
  };

  const item =
    config[status] ?? {
      label: status,
      className:
        "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${item.className}`}
    >
      <Clock3 size={12} />
      {item.label}
    </span>
  );
}