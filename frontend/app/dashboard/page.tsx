"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Brain,
  FileText,
  MessageSquare,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import Loading from "@/components/ui/Loading";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  Conversation,
  Document,
  Memory,
  MemoryIntelligenceSummary,
  VerificationAction,
} from "@/lib/types";

interface VerificationActionsResponse {
  actions: VerificationAction[];
}

export default function DashboardPage() {
  const { user } = useAuth();

  const [memories, setMemories] = useState<Memory[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [conversations, setConversations] = useState<
    Conversation[]
  >([]);
  const [actions, setActions] = useState<VerificationAction[]>(
    [],
  );
  const [summary, setSummary] =
    useState<MemoryIntelligenceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      return;
    }

    async function loadDashboard() {
      try {
        const [
          memoryData,
          documentData,
          conversationData,
          actionData,
          intelligence,
        ] = await Promise.all([
          apiFetch<Memory[]>("/api/memories"),

          apiFetch<Document[]>("/api/documents"),

          apiFetch<Conversation[]>(
            "/api/chat/conversations",
          ),

          apiFetch<
            VerificationAction[] | VerificationActionsResponse
          >("/api/verification/actions"),

          apiFetch<MemoryIntelligenceSummary>(
            "/api/memory-intelligence/summary",
          ),
        ]);

        setMemories(memoryData);
        setDocuments(documentData);
        setConversations(conversationData);

        // The verification endpoint may return either:
        //
        // 1. A raw array:
        //    [...]
        //
        // or:
        //
        // 2. A wrapped response:
        //    { actions: [...] }
        //
        // Normalize both formats so the dashboard always
        // works with VerificationAction[].
        const normalizedActions = Array.isArray(actionData)
          ? actionData
          : Array.isArray(actionData.actions)
            ? actionData.actions
            : [];

        setActions(normalizedActions);
        setSummary(intelligence);
      } catch (error) {
        console.error(
          "Dashboard loading failed:",
          error,
        );
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, [user]);

  return (
    <DashboardShell>
      {loading ? (
        <Loading text="Loading your workspace..." />
      ) : (
        <div className="space-y-6">
          <section>
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <p className="text-sm font-medium text-blue-600">
                  Persistent Contextual AI
                </p>

                <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 lg:text-3xl">
                  Welcome back, {user?.name}
                </h1>

                <p className="mt-2 max-w-2xl text-sm text-slate-500">
                  Your assistant remembers important context,
                  searches your knowledge, and verifies external
                  actions before execution.
                </p>
              </div>

              <Link
                href="/dashboard/chat/new"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                <Sparkles size={17} />
                Start New Chat
              </Link>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title="Memories"
              value={memories.length}
              icon={<Brain size={20} />}
              href="/dashboard/memory"
            />

            <StatCard
              title="Documents"
              value={documents.length}
              icon={<FileText size={20} />}
              href="/dashboard/documents"
            />

            <StatCard
              title="Conversations"
              value={conversations.length}
              icon={<MessageSquare size={20} />}
              href="/dashboard/chat"
            />

            <StatCard
              title="Pending Actions"
              value={
                actions.filter(
                  (action) => action.status === "PENDING",
                ).length
              }
              icon={<ShieldCheck size={20} />}
              href="/dashboard/verification"
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            <Card className="p-5 lg:col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-slate-900">
                    Recent Conversations
                  </h2>

                  <p className="mt-1 text-xs text-slate-500">
                    Continue where you left off.
                  </p>
                </div>

                <Link
                  href="/dashboard/chat"
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                >
                  View all
                </Link>
              </div>

              <div className="mt-5 divide-y divide-slate-100">
                {conversations.length === 0 ? (
                  <p className="py-8 text-center text-sm text-slate-500">
                    No conversations yet.
                  </p>
                ) : (
                  conversations
                    .slice(0, 5)
                    .map((conversation) => (
                      <Link
                        key={conversation.id}
                        href={`/dashboard/chat?conversation=${conversation.id}`}
                        className="flex items-center justify-between gap-4 py-4 hover:bg-slate-50"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-slate-800">
                            {conversation.title}
                          </p>

                          <p className="mt-1 text-xs text-slate-400">
                            {new Date(
                              conversation.updated_at,
                            ).toLocaleString()}
                          </p>
                        </div>

                        <ArrowRight
                          size={16}
                          className="shrink-0 text-slate-400"
                        />
                      </Link>
                    ))
                )}
              </div>
            </Card>

            <Card className="p-5">
              <h2 className="font-semibold text-slate-900">
                Memory Intelligence
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Conflict and memory consistency overview.
              </p>

              <div className="mt-5 space-y-4">
                <Metric
                  label="Total conflicts"
                  value={summary?.total_conflicts ?? 0}
                />

                <Metric
                  label="New memory wins"
                  value={summary?.new_memory_wins ?? 0}
                />

                <Metric
                  label="Existing memory wins"
                  value={
                    summary?.existing_memory_wins ?? 0
                  }
                />
              </div>

              <Link
                href="/dashboard/memory"
                className="mt-5 flex items-center justify-center gap-2 rounded-lg bg-slate-100 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-200"
              >
                Explore Memory
                <ArrowRight size={15} />
              </Link>
            </Card>
          </section>
        </div>
      )}
    </DashboardShell>
  );
}

function StatCard({
  title,
  value,
  icon,
  href,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  href: string;
}) {
  return (
    <Link href={href}>
      <Card className="p-5 transition hover:-translate-y-0.5 hover:shadow-md">
        <div className="flex items-center justify-between">
          <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
            {icon}
          </div>

          <ArrowRight
            size={16}
            className="text-slate-300"
          />
        </div>

        <p className="mt-5 text-2xl font-bold text-slate-900">
          {value}
        </p>

        <p className="mt-1 text-sm text-slate-500">
          {title}
        </p>
      </Card>
    </Link>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
      <span className="text-sm text-slate-600">
        {label}
      </span>

      <span className="font-semibold text-slate-900">
        {value}
      </span>
    </div>
  );
}
