"use client";

import { Bot, User } from "lucide-react";

import type { Message } from "@/lib/types";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({
  message,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={[
        "flex gap-3",
        isUser ? "justify-end" : "justify-start",
      ].join(" ")}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white">
          <Bot size={17} />
        </div>
      )}

      <div
        className={[
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm md:max-w-[75%]",
          isUser
            ? "rounded-br-md bg-blue-600 text-white"
            : "rounded-bl-md border border-slate-200 bg-white text-slate-700",
        ].join(" ")}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content}
        </p>

        <p
          className={[
            "mt-2 text-[10px]",
            isUser
              ? "text-blue-100"
              : "text-slate-400",
          ].join(" ")}
        >
          {new Date(message.created_at).toLocaleTimeString(
            [],
            {
              hour: "2-digit",
              minute: "2-digit",
            },
          )}
        </p>
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-600">
          <User size={17} />
        </div>
      )}
    </div>
  );
}