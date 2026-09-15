"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import DashboardShell from "@/components/layout/DashboardShell";
import ChatWorkspace from "@/components/chat/ChatWorkspace";

function ChatPageContent() {
  const searchParams = useSearchParams();

  const conversationParam = searchParams.get("conversation");

  const conversationId = conversationParam
    ? Number(conversationParam)
    : undefined;

  return (
    <ChatWorkspace
      initialConversationId={
        Number.isFinite(conversationId)
          ? conversationId
          : undefined
      }
    />
  );
}

export default function ChatPage() {
  return (
    <DashboardShell>
      <Suspense
        fallback={
          <div className="flex h-[calc(100vh-8rem)] min-h-[620px] items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
              Loading chat...
            </div>
          </div>
        }
      >
        <ChatPageContent />
      </Suspense>
    </DashboardShell>
  );
}