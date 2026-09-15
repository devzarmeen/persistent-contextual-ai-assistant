"use client";

import {
  Brain,
  Search,
  ShieldAlert,
  Sparkles,
  Trash2,
  Loader2,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import Loading from "@/components/ui/Loading";
import { apiFetch } from "@/lib/api";
import type {
  Memory,
  MemoryConflict,
  MemoryIntelligenceSummary,
  MemorySearchResponse,
} from "@/lib/types";

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [conflicts, setConflicts] = useState<
    MemoryConflict[]
  >([]);
  const [summary, setSummary] =
    useState<MemoryIntelligenceSummary | null>(
      null,
    );

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] =
    useState<MemorySearchResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [searching, setSearching] =
    useState(false);
  const [error, setError] = useState("");

  const [deletingId, setDeletingId] =
    useState<number | null>(null);

  useEffect(() => {
    void loadMemory();
  }, []);

  async function loadMemory() {
    setLoading(true);
    setError("");

    try {
      const [
        memoryData,
        conflictData,
        summaryData,
      ] = await Promise.all([
        apiFetch<Memory[]>("/api/memories"),

        apiFetch<
          MemoryConflict[] |
          { conflicts: MemoryConflict[] }
        >(
          "/api/memory-intelligence/conflicts",
        ),

        apiFetch<MemoryIntelligenceSummary>(
          "/api/memory-intelligence/summary",
        ),
      ]);

      setMemories(
        Array.isArray(memoryData)
          ? memoryData
          : [],
      );

      setConflicts(
        Array.isArray(conflictData)
          ? conflictData
          : Array.isArray(conflictData.conflicts)
            ? conflictData.conflicts
            : [],
      );

      setSummary(summaryData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load memory.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function searchMemory() {
    const trimmed = query.trim();

    if (!trimmed) {
      setSearchResults(null);
      return;
    }

    setSearching(true);
    setError("");

    try {
      const result =
        await apiFetch<MemorySearchResponse>(
          "/api/memories/search",
          {
            method: "POST",
            body: JSON.stringify({
              query: trimmed,
              limit: 10,
            }),
          },
        );

      setSearchResults(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Memory search failed.",
      );
    } finally {
      setSearching(false);
    }
  }

  async function deleteMemory(memory: Memory) {
    const confirmed = window.confirm(
      `Are you sure you want to forget this memory?\n\n"${memory.content}"\n\nThis action cannot be undone.`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(memory.id);
    setError("");

    try {
      await apiFetch<void>(
        `/api/memories/${memory.id}`,
        {
          method: "DELETE",
        },
      );

      // Remove from main memory list.
      setMemories((current) =>
        current.filter(
          (item) => item.id !== memory.id,
        ),
      );

      // Remove from current search results too.
      setSearchResults((current) => {
        if (!current) {
          return null;
        }

        return {
          ...current,
          results: current.results.filter(
            (item) => item.id !== memory.id,
          ),
        };
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to forget memory.",
      );
    } finally {
      setDeletingId(null);
    }
  }

  const activeMemories = memories.filter(
    (memory) => memory.is_active,
  );

  return (
    <DashboardShell>
      <div className="space-y-6">
        <section>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
              <Brain size={21} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Memory Intelligence
              </h1>

              <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                Explore the long-term context your assistant
                has learned and how conflicting memories are
                resolved.
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
          <Loading text="Loading memory intelligence..." />
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="Total Memories"
                value={memories.length}
                icon={<Brain size={18} />}
              />

              <MetricCard
                title="Active Memories"
                value={activeMemories.length}
                icon={<Sparkles size={18} />}
              />

              <MetricCard
                title="Conflicts"
                value={
                  summary?.total_conflicts ??
                  conflicts.length
                }
                icon={<ShieldAlert size={18} />}
              />

              <MetricCard
                title="New Memory Wins"
                value={
                  summary?.new_memory_wins ?? 0
                }
                icon={<Sparkles size={18} />}
              />
            </section>

            <Card className="p-5">
              <div>
                <h2 className="font-semibold text-slate-900 dark:text-white">
                  Search Memory
                </h2>

                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Search semantically across your persistent
                  memories.
                </p>
              </div>

              <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                <div className="relative flex-1">
                  <Search
                    size={17}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  />

                  <input
                    value={query}
                    onChange={(event) =>
                      setQuery(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        void searchMemory();
                      }
                    }}
                    placeholder="Search your memories..."
                    className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-blue-950"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => void searchMemory()}
                  disabled={searching}
                  className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {searching
                    ? "Searching..."
                    : "Search"}
                </button>
              </div>

              {searchResults && (
                <div className="mt-5 space-y-3">
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                    Results for "{searchResults.query}"
                  </p>

                  {searchResults.results.length === 0 ? (
                    <EmptyState text="No matching memories found." />
                  ) : (
                    searchResults.results.map(
                      (memory) => (
                        <MemoryCard
                          key={memory.id}
                          memory={memory}
                          deletingId={deletingId}
                          onDelete={deleteMemory}
                        />
                      ),
                    )
                  )}
                </div>
              )}
            </Card>

            <Card className="overflow-hidden">
              <div className="border-b border-slate-200 p-5 dark:border-slate-800">
                <h2 className="font-semibold text-slate-900 dark:text-white">
                  Stored Memories
                </h2>

                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Persistent facts, preferences, projects,
                  deadlines, and decisions.
                </p>
              </div>

              {memories.length === 0 ? (
                <EmptyState text="No memories have been stored yet." />
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {memories.map((memory) => (
                    <MemoryCard
                      key={memory.id}
                      memory={memory}
                      deletingId={deletingId}
                      onDelete={deleteMemory}
                    />
                  ))}
                </div>
              )}
            </Card>

            <Card className="overflow-hidden">
              <div className="border-b border-slate-200 p-5 dark:border-slate-800">
                <h2 className="font-semibold text-slate-900 dark:text-white">
                  Memory Conflicts
                </h2>

                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Previous and newer memories that required
                  resolution.
                </p>
              </div>

              {conflicts.length === 0 ? (
                <EmptyState text="No memory conflicts found." />
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {conflicts.map((conflict) => (
                    <ConflictCard
                      key={conflict.id}
                      conflict={conflict}
                    />
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

function MetricCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {title}
        </span>

        <span className="text-blue-600 dark:text-blue-400">
          {icon}
        </span>
      </div>

      <p className="mt-3 text-2xl font-bold text-slate-900 dark:text-white">
        {value}
      </p>
    </Card>
  );
}

function MemoryCard({
  memory,
  deletingId,
  onDelete,
}: {
  memory:
    | Memory
    | {
        id: number;
        memory_type: string;
        content: string;
        importance: number;
        confidence: number;
        confirmation_count: number;
        source_type: string;
        source_id: string | null;
        similarity_distance?: number | null;
      };

  deletingId: number | null;

  onDelete: (memory: Memory) => Promise<void>;
}) {
  const canDelete =
    "is_active" in memory;

  return (
    <div className="p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-semibold uppercase text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
              {memory.memory_type}
            </span>

            {"is_active" in memory && (
              <span
                className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                  memory.is_active
                    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                    : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                }`}
              >
                {memory.is_active
                  ? "Active"
                  : "Inactive"}
              </span>
            )}
          </div>

          <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-200">
            {memory.content}
          </p>

          <div className="mt-4 grid gap-3 text-xs sm:grid-cols-4">
            <Info
              label="Confidence"
              value={`${Math.round(
                memory.confidence * 100,
              )}%`}
            />

            <Info
              label="Importance"
              value={`${Math.round(
                memory.importance * 100,
              )}%`}
            />

            <Info
              label="Confirmed"
              value={String(
                memory.confirmation_count,
              )}
            />

            <Info
              label="Source"
              value={memory.source_type}
            />
          </div>
        </div>

        {canDelete && (
          <button
            type="button"
            onClick={() =>
              void onDelete(memory as Memory)
            }
            disabled={deletingId === memory.id}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/60 dark:text-red-400 dark:hover:bg-red-950/30"
          >
            {deletingId === memory.id ? (
              <Loader2
                size={15}
                className="animate-spin"
              />
            ) : (
              <Trash2 size={15} />
            )}

            {deletingId === memory.id
              ? "Forgetting..."
              : "Forget"}
          </button>
        )}
      </div>
    </div>
  );
}

function ConflictCard({
  conflict,
}: {
  conflict: MemoryConflict;
}) {
  return (
    <div className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold uppercase text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
          {conflict.conflict_type ??
            conflict.comparison_type}
        </span>

        <span className="text-xs text-slate-400">
          {new Date(
            conflict.created_at,
          ).toLocaleString()}
        </span>
      </div>

      <p className="mt-3 text-sm font-medium text-slate-800 dark:text-slate-200">
        Resolution: {conflict.resolution}
      </p>

      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        {conflict.reason}
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Info
          label="Old score"
          value={conflict.old_score.toFixed(3)}
        />

        <Info
          label="New score"
          value={conflict.new_score.toFixed(3)}
        />

        <Info
          label="Winner"
          value={
            conflict.winning_memory_id
              ? `Memory #${conflict.winning_memory_id}`
              : "Unresolved"
          }
        />
      </div>
    </div>
  );
}

function Info({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/70">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-1 truncate text-xs font-medium text-slate-700 dark:text-slate-200">
        {value}
      </p>
    </div>
  );
}

function EmptyState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="p-8 text-center text-sm text-slate-500 dark:text-slate-400">
      {text}
    </div>
  );
}