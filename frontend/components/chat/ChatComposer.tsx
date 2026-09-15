"use client";

import {
  ArrowUp,
  Paperclip,
  Sparkles,
} from "lucide-react";
import {
  FormEvent,
  KeyboardEvent,
  useState,
} from "react";

interface ChatComposerProps {
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
}

export default function ChatComposer({
  onSend,
  disabled = false,
}: ChatComposerProps) {
  const [message, setMessage] = useState("");

  async function submit() {
    const value = message.trim();

    if (!value || disabled) {
      return;
    }

    setMessage("");

    try {
      await onSend(value);
    } catch {
      setMessage(value);
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    await submit();
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-4xl"
      >
        <div className="relative rounded-2xl border border-slate-200 bg-slate-50 shadow-sm transition focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-50">
          <textarea
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={3}
            placeholder="Ask your assistant anything..."
            className="w-full resize-none bg-transparent px-4 pb-14 pt-4 text-sm text-slate-800 outline-none placeholder:text-slate-400"
          />

          <div className="absolute bottom-3 left-3 flex items-center gap-2">
            <button
              type="button"
              disabled
              title="Document attachments will be enabled in the Documents phase"
              className="rounded-lg p-2 text-slate-300"
            >
              <Paperclip size={17} />
            </button>

            <div className="hidden items-center gap-1 text-[11px] text-slate-400 sm:flex">
              <Sparkles size={13} />
              Persistent context enabled
            </div>
          </div>

          <button
            type="submit"
            disabled={
              disabled || message.trim().length === 0
            }
            className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <ArrowUp size={17} />
          </button>
        </div>

        <p className="mt-2 text-center text-[10px] text-slate-400">
          Enter to send · Shift + Enter for a new line
        </p>
      </form>
    </div>
  );
}