"use client";

import Link from "next/link";
import {
  MessageSquare,
  Plus,
  Search,
} from "lucide-react";

import type { Conversation } from "@/lib/types";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId?: number;
}

export default function ConversationList({
  conversations,
  activeConversationId,
}: ConversationListProps) {
  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-200 bg-white lg:w-72">
      <div className="border-b border-slate-200 p-4">
        <Link
          href="/dashboard/chat/new"
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          <Plus size={17} />
          New conversation
        </Link>

        <div className="relative mt-3">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />

          <input
            placeholder="Search conversations..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-xs outline-none focus:border-blue-400 focus:bg-white"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <MessageSquare
              size={28}
              className="mx-auto text-slate-300"
            />

            <p className="mt-3 text-sm font-medium text-slate-600">
              No conversations yet
            </p>

            <p className="mt-1 text-xs text-slate-400">
              Start a new conversation.
            </p>
          </div>
        ) : (
          conversations.map((conversation) => {
            const active =
              conversation.id === activeConversationId;

            return (
              <Link
                key={conversation.id}
                href={`/dashboard/chat?conversation=${conversation.id}`}
                className={[
                  "mb-1 block rounded-xl px-3 py-3 transition",
                  active
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-700 hover:bg-slate-50",
                ].join(" ")}
              >
                <p className="truncate text-sm font-medium">
                  {conversation.title}
                </p>

                <p className="mt-1 text-[11px] text-slate-400">
                  {new Date(
                    conversation.updated_at,
                  ).toLocaleDateString()}
                </p>
              </Link>
            );
          })
        )}
      </div>
    </aside>
  );
}