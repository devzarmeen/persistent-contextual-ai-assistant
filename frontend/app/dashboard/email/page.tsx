"use client";

import {
  CheckCircle2,
  Clock3,
  Mail,
  Plus,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { VerificationAction } from "@/lib/types";

interface EmailForm {
  to: string;
  subject: string;
  body: string;
}

const initialForm: EmailForm = {
  to: "",
  subject: "",
  body: "",
};

export default function EmailPage() {
  const [actions, setActions] = useState<
    VerificationAction[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showComposer, setShowComposer] =
    useState(true);

  const [form, setForm] =
    useState<EmailForm>(initialForm);

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

  function updateField(
    field: keyof EmailForm,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function createEmailAction(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (
      !form.to.trim() ||
      !form.subject.trim() ||
      !form.body.trim()
    ) {
      setError(
        "Recipient, subject and message are required.",
      );
      return;
    }

    setSending(true);

    try {
      /*
       * Create a PENDING verification action.
       *
       * We intentionally do NOT call Gmail directly from
       * the frontend.
       */
      await apiFetch(
        "/api/verification/actions",
        {
          method: "POST",
          body: JSON.stringify({
            tool_name: "send_email",
            arguments: {
              to: form.to.trim(),
              subject: form.subject.trim(),
              body: form.body.trim(),
            },
          }),
        },
      );

      setSuccess(
        "Email prepared and sent for approval.",
      );

      setForm(initialForm);

      await loadEmailActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to prepare email.",
      );
    } finally {
      setSending(false);
    }
  }

  async function approveAndSend(
    actionId: number,
  ) {
    setError("");
    setSuccess("");

    try {
      await apiFetch(
        `/api/verification/actions/${actionId}/approve`,
        {
          method: "POST",
        },
      );

      await apiFetch(
        `/api/verification/actions/${actionId}/execute`,
        {
          method: "POST",
        },
      );

      setSuccess(
        "Email approved, sent and verified successfully.",
      );

      await loadEmailActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Email could not be sent.",
      );

      await loadEmailActions();
    }
  }

  async function rejectEmail(
    actionId: number,
  ) {
    setError("");
    setSuccess("");

    try {
      await apiFetch(
        `/api/verification/actions/${actionId}/reject`,
        {
          method: "POST",
        },
      );

      setSuccess("Email action rejected.");

      await loadEmailActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reject email.",
      );
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <section>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
                <Mail size={21} />
              </div>

              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Email
                </h1>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Compose, review and send emails through
                  your connected Gmail account.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() =>
                setShowComposer(
                  (current) => !current,
                )
              }
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              {showComposer ? (
                <X size={16} />
              ) : (
                <Plus size={16} />
              )}

              {showComposer
                ? "Close"
                : "Compose Email"}
            </button>
          </div>
        </section>

        {/* Alerts */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
            <CheckCircle2 size={17} />
            {success}
          </div>
        )}

        {/* Compose */}
        {showComposer && (
          <Card className="p-6">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Compose Email
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Sending an email requires explicit
                approval before Gmail is called.
              </p>
            </div>

            <form
              onSubmit={createEmailAction}
              className="space-y-4"
            >
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  To *
                </label>

                <input
                  type="email"
                  value={form.to}
                  onChange={(event) =>
                    updateField(
                      "to",
                      event.target.value,
                    )
                  }
                  placeholder="recipient@example.com"
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Subject *
                </label>

                <input
                  type="text"
                  value={form.subject}
                  onChange={(event) =>
                    updateField(
                      "subject",
                      event.target.value,
                    )
                  }
                  placeholder="Email subject"
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Message *
                </label>

                <textarea
                  value={form.body}
                  onChange={(event) =>
                    updateField(
                      "body",
                      event.target.value,
                    )
                  }
                  rows={9}
                  placeholder="Write your email..."
                  className="w-full resize-y rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm leading-6 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                <ShieldCheck size={16} />

                This creates an approval request first.
                Gmail will only send the email after
                approval.
              </div>

              <button
                type="submit"
                disabled={sending}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {sending ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                    Preparing...
                  </>
                ) : (
                  <>
                    <Mail size={16} />
                    Prepare & Send
                  </>
                )}
              </button>
            </form>
          </Card>
        )}

        {/* History */}
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
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
                Loading...
              </div>
            </div>
          ) : actions.length === 0 ? (
            <div className="p-10 text-center">
              <Mail
                size={30}
                className="mx-auto text-slate-300"
              />

              <p className="mt-3 text-sm text-slate-500">
                No email actions yet.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {actions.map((action) => (
                <div
                  key={action.id}
                  className="p-5"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900 dark:text-white">
                          Email
                        </span>

                        <StatusBadge
                          status={action.status}
                        />
                      </div>

                      <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-600 dark:bg-slate-950 dark:text-slate-300">
                        {formatRequest(
                          action.request,
                        )}
                      </pre>
                    </div>

                    <div className="shrink-0 text-xs text-slate-400">
                      {formatDate(
                        action.created_at,
                      )}
                    </div>
                  </div>

                  {(action.status === "PENDING" ||
                    action.status === "APPROVED") && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {action.status === "PENDING" && (
                        <button
                          type="button"
                          onClick={() =>
                            void approveAndSend(
                              action.id,
                            )
                          }
                          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                        >
                          <CheckCircle2 size={14} />
                          Approve & Send
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() =>
                          void rejectEmail(
                            action.id,
                          )
                        }
                        className="inline-flex items-center gap-2 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 dark:border-red-900/60 dark:hover:bg-red-950/30"
                      >
                        Reject
                      </button>
                    </div>
                  )}

                  {action.result && (
                    <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                      <p className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                        Result
                      </p>

                      <pre className="mt-2 whitespace-pre-wrap text-xs leading-5 text-emerald-700 dark:text-emerald-400">
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
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  if (status === "VERIFIED") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
        <CheckCircle2 size={11} />
        Verified
      </span>
    );
  }

  if (status === "PENDING") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
        <Clock3 size={11} />
        Pending approval
      </span>
    );
  }

  if (status === "REJECTED") {
    return (
      <span className="rounded-full bg-red-50 px-2.5 py-1 text-[11px] font-semibold text-red-700 dark:bg-red-950/40 dark:text-red-300">
        Rejected
      </span>
    );
  }

  return (
    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
      {status}
    </span>
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