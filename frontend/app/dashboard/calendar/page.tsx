"use client";

import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  MapPin,
  Plus,
  ShieldCheck,
  X,
} from "lucide-react";

import { FormEvent, useEffect, useState } from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { VerificationAction } from "@/lib/types";

interface CalendarForm {
  summary: string;
  description: string;
  date: string;
  startTime: string;
  endTime: string;
  location: string;
  timezone: string;
}

const initialForm: CalendarForm = {
  summary: "",
  description: "",
  date: "",
  startTime: "",
  endTime: "",
  location: "",
  timezone: "Asia/Karachi",
};

export default function CalendarPage() {
  const [actions, setActions] = useState<
    VerificationAction[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showForm, setShowForm] = useState(true);

  const [form, setForm] =
    useState<CalendarForm>(initialForm);

  useEffect(() => {
    void loadCalendarActions();
  }, []);

  async function loadCalendarActions() {
    try {
      setError("");

      const data = await apiFetch<
        VerificationAction[] | {
          actions: VerificationAction[];
        }
      >(
        "/api/verification/actions?tool_name=create_calendar_event",
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
          : "Unable to load calendar actions.",
      );
    } finally {
      setLoading(false);
    }
  }

  function updateField(
    field: keyof CalendarForm,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function createReminder(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (
      !form.summary.trim() ||
      !form.date ||
      !form.startTime ||
      !form.endTime
    ) {
      setError(
        "Title, date, start time and end time are required.",
      );
      return;
    }

    const startTime =
      `${form.date}T${form.startTime}:00`;

    const endTime =
      `${form.date}T${form.endTime}:00`;

    if (endTime <= startTime) {
      setError(
        "End time must be after start time.",
      );
      return;
    }

    setSubmitting(true);

    try {
      /*
       * We create the same verification action that
       * the agent uses for calendar changes.
       *
       * IMPORTANT:
       * This does not directly call Google Calendar.
       * It creates a PENDING approval action.
       */
      await apiFetch(
        "/api/verification/actions",
        {
          method: "POST",
          body: JSON.stringify({
            tool_name:
              "create_calendar_event",
            arguments: {
              summary:
                form.summary.trim(),
              start_time: startTime,
              end_time: endTime,
              description:
                form.description.trim() ||
                null,
              location:
                form.location.trim() ||
                null,
              calendar_id: "primary",
              time_zone:
                form.timezone,
            },
          }),
        },
      );

      setSuccess(
        "Reminder created and sent for approval.",
      );

      setForm(initialForm);

      await loadCalendarActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create reminder.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function approveAndExecute(
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
        "Calendar event approved, created and verified.",
      );

      await loadCalendarActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Calendar action could not be completed.",
      );

      await loadCalendarActions();
    }
  }

  async function rejectAction(
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

      setSuccess("Calendar action rejected.");

      await loadCalendarActions();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to reject calendar action.",
      );
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        {/* Header */}
        <section>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
                  <CalendarDays size={21} />
                </div>

                <div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Calendar
                  </h1>

                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Create reminders and manage verified
                    calendar actions.
                  </p>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() =>
                setShowForm((current) => !current)
              }
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
            >
              {showForm ? (
                <X size={16} />
              ) : (
                <Plus size={16} />
              )}

              {showForm
                ? "Close"
                : "New Reminder"}
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

        {/* Create form */}
        {showForm && (
          <Card className="p-6">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Create Reminder
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Your reminder will require approval before
                Google Calendar is changed.
              </p>
            </div>

            <form
              onSubmit={createReminder}
              className="space-y-5"
            >
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Title *
                </label>

                <input
                  value={form.summary}
                  onChange={(event) =>
                    updateField(
                      "summary",
                      event.target.value,
                    )
                  }
                  placeholder="e.g. Project meeting"
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              <div className="grid gap-5 md:grid-cols-3">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Date *
                  </label>

                  <input
                    type="date"
                    value={form.date}
                    onChange={(event) =>
                      updateField(
                        "date",
                        event.target.value,
                      )
                    }
                    className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Start Time *
                  </label>

                  <input
                    type="time"
                    value={form.startTime}
                    onChange={(event) =>
                      updateField(
                        "startTime",
                        event.target.value,
                      )
                    }
                    className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    End Time *
                  </label>

                  <input
                    type="time"
                    value={form.endTime}
                    onChange={(event) =>
                      updateField(
                        "endTime",
                        event.target.value,
                      )
                    }
                    className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Location
                  </label>

                  <div className="relative">
                    <MapPin
                      size={15}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                    />

                    <input
                      value={form.location}
                      onChange={(event) =>
                        updateField(
                          "location",
                          event.target.value,
                        )
                      }
                      placeholder="Optional location"
                      className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Timezone
                  </label>

                  <input
                    value={form.timezone}
                    onChange={(event) =>
                      updateField(
                        "timezone",
                        event.target.value,
                      )
                    }
                    className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Description
                </label>

                <textarea
                  value={form.description}
                  onChange={(event) =>
                    updateField(
                      "description",
                      event.target.value,
                    )
                  }
                  rows={4}
                  placeholder="Optional reminder details..."
                  className="w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                <ShieldCheck size={16} />

                Approval is required before the event is
                created in Google Calendar.
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                    Creating...
                  </>
                ) : (
                  <>
                    <CalendarDays size={16} />
                    Create Reminder
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
              Calendar Action History
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Every calendar change is tracked through
              verification.
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
              <CalendarDays
                size={30}
                className="mx-auto text-slate-300"
              />

              <p className="mt-3 text-sm text-slate-500">
                No calendar actions yet.
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
                          Calendar Event
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
                            void approveAndExecute(
                              action.id,
                            )
                          }
                          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                        >
                          <CheckCircle2 size={14} />
                          Approve & Create
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() =>
                          void rejectAction(
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