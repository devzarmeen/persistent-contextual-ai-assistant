"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Mail,
  Search,
  ShieldCheck,
  Sparkles,
  Wrench,
  XCircle,
} from "lucide-react";

import ChatComposer from "./ChatComposer";
import ChatMessage from "./ChatMessage";
import ConversationList from "./ConversationList";

import { apiFetch } from "@/lib/api";

import type {
  AgentMetadata,
  ChatResponse,
  Conversation,
  ConversationDetail,
  Message,
} from "@/lib/types";


interface ChatWorkspaceProps {
  initialConversationId?: number;
  initialMessage?: string;
}


export default function ChatWorkspace({
  initialConversationId,
  initialMessage,
}: ChatWorkspaceProps) {
  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [activeConversationId, setActiveConversationId] =
    useState<number | undefined>(
      initialConversationId,
    );

  const [loadingConversations, setLoadingConversations] =
    useState(true);

  const [loadingMessages, setLoadingMessages] =
    useState(false);

  const [sending, setSending] =
    useState(false);

  const [error, setError] =
    useState("");

  const [agentActivity, setAgentActivity] =
    useState<AgentMetadata | null>(null);

  const scrollRef =
    useRef<HTMLDivElement>(null);

  const initialMessageSent =
    useRef(false);


  // ==========================================================
  // LOAD CONVERSATIONS
  // ==========================================================

  const loadConversations =
    useCallback(async () => {
      const data =
        await apiFetch<Conversation[]>(
          "/api/chat/conversations",
        );

      setConversations(data);

      return data;
    }, []);


  // ==========================================================
  // LOAD SINGLE CONVERSATION
  // ==========================================================

  const loadConversation =
    useCallback(
      async (conversationId: number) => {
        setLoadingMessages(true);
        setError("");

        try {
          const data =
            await apiFetch<ConversationDetail>(
              `/api/chat/conversations/${conversationId}`,
            );

          setMessages(data.messages);

          setActiveConversationId(
            data.id,
          );

        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load conversation.",
          );

        } finally {
          setLoadingMessages(false);
        }
      },
      [],
    );


  // ==========================================================
  // INITIALIZE CHAT
  // ==========================================================

  useEffect(() => {
    async function initialize() {
      try {
        const data =
          await loadConversations();

        if (initialConversationId) {
          await loadConversation(
            initialConversationId,
          );

        } else if (data.length > 0) {
          await loadConversation(
            data[0].id,
          );
        }

      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load conversations.",
        );

      } finally {
        setLoadingConversations(false);
      }
    }

    void initialize();
  }, [
    initialConversationId,
    loadConversations,
    loadConversation,
  ]);


  // ==========================================================
  // AUTO SCROLL
  // ==========================================================

  useEffect(() => {
    const element =
      scrollRef.current;

    if (!element) {
      return;
    }

    element.scrollTop =
      element.scrollHeight;

  }, [
    messages,
    sending,
    agentActivity,
  ]);


  // ==========================================================
  // INITIAL MESSAGE
  // ==========================================================

  useEffect(() => {
    if (
      !initialMessage ||
      activeConversationId ||
      sending ||
      initialMessageSent.current
    ) {
      return;
    }

    initialMessageSent.current =
      true;

    void sendMessage(
      initialMessage,
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    initialMessage,
    activeConversationId,
    sending,
  ]);


  // ==========================================================
  // SEND MESSAGE
  // ==========================================================

  async function sendMessage(
    message: string,
  ) {
    const trimmedMessage =
      message.trim();

    if (!trimmedMessage) {
      return;
    }

    setSending(true);
    setError("");
    setAgentActivity(null);

    const optimisticMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmedMessage,
      created_at:
        new Date().toISOString(),
    };

    setMessages((current) => [
      ...current,
      optimisticMessage,
    ]);

    try {
      const response =
        await apiFetch<ChatResponse>(
          "/api/chat",
          {
            method: "POST",

            body: JSON.stringify({
              message: trimmedMessage,

              conversation_id:
                activeConversationId ??
                null,
            }),
          },
        );

      // ------------------------------------------------------
      // Agent metadata
      // ------------------------------------------------------

      if (response.agent) {
        setAgentActivity(
          response.agent,
        );
      } else {
        setAgentActivity(null);
      }

      // ------------------------------------------------------
      // Conversation
      // ------------------------------------------------------

      setActiveConversationId(
        response.conversation_id,
      );

      await loadConversation(
        response.conversation_id,
      );

      const conversationData =
        await loadConversations();

      setConversations(
        conversationData,
      );

    } catch (err) {
      setMessages((current) =>
        current.filter(
          (item) =>
            item.id !==
            optimisticMessage.id,
        ),
      );

      setAgentActivity(null);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to send message.",
      );

      throw err;

    } finally {
      setSending(false);
    }
  }


  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-[620px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

      {/* ======================================================
          CONVERSATION SIDEBAR
          ====================================================== */}

      <div className="hidden md:flex">
        <ConversationList
          conversations={
            conversations
          }
          activeConversationId={
            activeConversationId
          }
        />
      </div>


      {/* ======================================================
          MAIN CHAT
          ====================================================== */}

      <section className="flex min-w-0 flex-1 flex-col">

        {/* ----------------------------------------------------
            HEADER
            ---------------------------------------------------- */}

        <header className="flex h-16 shrink-0 items-center border-b border-slate-200 px-5">

          <div className="flex items-center gap-3">

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <Sparkles size={18} />
            </div>

            <div>

              <h1 className="text-sm font-semibold text-slate-900">
                Persistent Assistant
              </h1>

              <p className="text-[11px] text-slate-400">
                Memory · Documents · Verified actions
              </p>

            </div>

          </div>

        </header>


        {/* ----------------------------------------------------
            MESSAGES
            ---------------------------------------------------- */}

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 p-4 md:p-6"
        >

          {loadingMessages ? (

            <div className="flex h-full items-center justify-center">

              <div className="flex items-center gap-2 text-sm text-slate-500">

                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />

                Loading conversation...

              </div>

            </div>

          ) : messages.length === 0 ? (

            <EmptyChat />

          ) : (

            <div className="mx-auto max-w-4xl space-y-5">

              {messages.map(
                (message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                  />
                ),
              )}


              {/* =================================================
                  AGENT ACTIVITY
                  ================================================= */}

              {agentActivity && (
                <AgentActivity
                  activity={
                    agentActivity
                  }
                />
              )}


              {/* =================================================
                  SENDING STATE
                  ================================================= */}

              {sending && (
                <div className="flex items-center gap-3">

                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
                    <Sparkles size={16} />
                  </div>

                  <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3">

                    <div className="flex items-center gap-2">

                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />

                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:100ms]" />

                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:200ms]" />

                      <span className="ml-1 text-xs text-slate-400">
                        ContextAI is working...
                      </span>

                    </div>

                  </div>

                </div>
              )}

            </div>
          )}


          {/* ==================================================
              ERROR
              ================================================== */}

          {error && (

            <div className="mx-auto mt-4 max-w-4xl rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

              {error}

            </div>
          )}

        </div>


        {/* ----------------------------------------------------
            COMPOSER
            ---------------------------------------------------- */}

        <ChatComposer
          onSend={sendMessage}
          disabled={
            sending ||
            loadingConversations
          }
        />

      </section>

    </div>
  );
}


// ============================================================
// AGENT ACTIVITY COMPONENT
// ============================================================

function AgentActivity({
  activity,
}: {
  activity: AgentMetadata;
}) {
  const toolName =
    activity.tool_name;

  const verificationRequired =
    activity.verification_required;

  const status =
    activity.verification_status ??
    activity.status ??
    "COMPLETED";


  // ----------------------------------------------------------
  // Verification
  // ----------------------------------------------------------

  if (verificationRequired) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">

        <div className="flex items-start gap-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
            <ShieldCheck size={18} />
          </div>

          <div className="min-w-0 flex-1">

            <div className="flex items-center gap-2">

              <p className="text-sm font-semibold text-amber-900">
                Approval required
              </p>

              <StatusBadge
                status={status}
              />

            </div>

            <p className="mt-1 text-xs leading-5 text-amber-800">
              ContextAI prepared this external
              action, but it will not execute it
              without your approval.
            </p>

            {toolName && (
              <div className="mt-3 flex items-center gap-2 text-xs text-amber-900">

                <Wrench size={13} />

                <span>
                  {formatToolName(
                    toolName,
                  )}
                </span>

              </div>
            )}

            {activity.verification_action_id && (
              <div className="mt-2 text-xs text-amber-700">
                Verification action #
                {activity.verification_action_id}
              </div>
            )}

          </div>

        </div>

      </div>
    );
  }


  // ----------------------------------------------------------
  // Tool execution
  // ----------------------------------------------------------

  if (
    activity.action === "tool" &&
    toolName
  ) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">

        <div className="flex items-center gap-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <ToolIcon
              toolName={toolName}
            />
          </div>

          <div className="min-w-0 flex-1">

            <p className="text-sm font-medium text-slate-800">
              ContextAI used{" "}
              {formatToolName(
                toolName,
              )}
            </p>

            <p className="mt-0.5 text-xs text-slate-400">
              Retrieved context and generated
              the response from tool evidence.
            </p>

          </div>

          <StatusBadge
            status={status}
          />

        </div>

      </div>
    );
  }


  // ----------------------------------------------------------
  // Direct answer
  // ----------------------------------------------------------

  if (
    activity.action ===
    "final_answer"
  ) {
    return (
      <div className="flex items-center gap-2 text-xs text-slate-400">

        <CheckCircle2
          size={14}
          className="text-green-500"
        />

        Response generated from
        conversational context.

      </div>
    );
  }


  return null;
}


// ============================================================
// TOOL ICON
// ============================================================

function ToolIcon({
  toolName,
}: {
  toolName: string;
}) {
  if (
    toolName.includes("calendar")
  ) {
    return (
      <CalendarDays size={17} />
    );
  }

  if (
    toolName.includes("email") ||
    toolName.includes("mail")
  ) {
    return (
      <Mail size={17} />
    );
  }

  if (
    toolName.includes("memory")
  ) {
    return (
      <Search size={17} />
    );
  }

  if (
    toolName.includes("document")
  ) {
    return (
      <Search size={17} />
    );
  }

  return <Wrench size={17} />;
}


// ============================================================
// STATUS BADGE
// ============================================================

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const normalized =
    status.toUpperCase();

  if (
    normalized === "VERIFIED" ||
    normalized === "COMPLETED"
  ) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-[10px] font-medium text-green-700">

        <CheckCircle2 size={11} />

        {normalized === "VERIFIED"
          ? "Verified"
          : "Completed"}

      </span>
    );
  }

  if (
    normalized === "PENDING" ||
    normalized === "AWAITING_APPROVAL"
  ) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700">

        <Clock3 size={11} />

        Approval pending

      </span>
    );
  }

  if (
    normalized === "FAILED" ||
    normalized === "REJECTED"
  ) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-1 text-[10px] font-medium text-red-700">

        <XCircle size={11} />

        {normalized === "REJECTED"
          ? "Rejected"
          : "Failed"}

      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-600">

      <Clock3 size={11} />

      {formatStatus(status)}

    </span>
  );
}


// ============================================================
// HELPERS
// ============================================================

function formatToolName(
  toolName: string,
): string {
  return toolName
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function formatStatus(
  status: string,
): string {
  return status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


// ============================================================
// EMPTY CHAT
// ============================================================

function EmptyChat() {
  return (
    <div className="flex h-full items-center justify-center">

      <div className="max-w-md text-center">

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <Sparkles size={25} />
        </div>

        <h2 className="mt-5 text-xl font-bold text-slate-900">
          What can I help you with?
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Ask questions, continue previous work,
          search your persistent context, or work
          with information you have already shared.
        </p>

      </div>

    </div>
  );
}