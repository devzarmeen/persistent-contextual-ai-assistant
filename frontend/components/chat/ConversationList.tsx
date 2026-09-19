"use client";

import {
  Clock3,
  MessageSquare,
  Search,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import type { Conversation } from "@/lib/types";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId?: number;
  onSelect?: (conversationId: number) => void;
}

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelect,
}: ConversationListProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredConversations = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) {
      return conversations;
    }

    return conversations.filter((conversation) => {
      const title = conversation.title?.toLowerCase() ?? "";

      return (
        title.includes(query) ||
        String(conversation.id).includes(query)
      );
    });
  }, [conversations, searchQuery]);

  function handleConversationClick(
    conversationId: number,
  ) {
    onSelect?.(conversationId);

    if (!onSelect) {
      window.location.href =
        `/dashboard/chat/${conversationId}`;
    }
  }

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-200 p-4 dark:border-slate-800">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Conversations
            </h2>

            <p className="mt-0.5 text-[11px] text-slate-400">
              {conversations.length} conversation
              {conversations.length === 1 ? "" : "s"}
            </p>
          </div>

          <MessageSquare
            size={17}
            className="text-slate-400"
          />
        </div>

        {/* Search */}
        <div className="relative">
          <Search
            size={15}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />

          <input
            type="text"
            value={searchQuery}
            onChange={(event) =>
              setSearchQuery(event.target.value)
            }
            placeholder="Search conversations..."
            className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-9 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:border-blue-600 dark:focus:bg-slate-900 dark:focus:ring-blue-950"
          />

          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute right-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              aria-label="Clear conversation search"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Conversation list */}
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {filteredConversations.length === 0 ? (
          <div className="flex h-full min-h-40 items-center justify-center px-5 text-center">
            <div>
              <Search
                size={24}
                className="mx-auto text-slate-300 dark:text-slate-700"
              />

              <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-300">
                {searchQuery
                  ? "No conversations found"
                  : "No conversations yet"}
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-400">
                {searchQuery
                  ? "Try another search term."
                  : "Start a new conversation to see it here."}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredConversations.map(
              (conversation) => {
                const active =
                  conversation.id ===
                  activeConversationId;

                return (
                  <button
                    key={conversation.id}
                    type="button"
                    onClick={() =>
                      handleConversationClick(
                        conversation.id,
                      )
                    }
                    className={[
                      "w-full rounded-xl px-3 py-3 text-left transition",
                      active
                        ? "bg-blue-50 dark:bg-blue-950/30"
                        : "hover:bg-slate-50 dark:hover:bg-slate-900",
                    ].join(" ")}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={[
                          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                          active
                            ? "bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-300"
                            : "bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-400",
                        ].join(" ")}
                      >
                        <MessageSquare size={15} />
                      </div>

                      <div className="min-w-0 flex-1">
                        <p
                          className={[
                            "truncate text-sm font-medium",
                            active
                              ? "text-blue-900 dark:text-blue-200"
                              : "text-slate-800 dark:text-slate-200",
                          ].join(" ")}
                        >
                          {conversation.title ||
                            "Untitled conversation"}
                        </p>

                        <div className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-400">
                          <Clock3 size={11} />

                          {formatConversationDate(
                            conversation.updated_at,
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              },
            )}
          </div>
        )}
      </div>
    </aside>
  );
}

function formatConversationDate(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}