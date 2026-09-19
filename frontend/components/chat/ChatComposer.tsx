"use client";

import {
  ArrowUp,
  FileText,
  Loader2,
  Paperclip,
  Sparkles,
  X,
} from "lucide-react";
import {
  ChangeEvent,
  FormEvent,
  KeyboardEvent,
  useRef,
  useState,
} from "react";

export interface UploadedChatDocument {
  id: number;
  filename: string;
  content_type: string;
  file_size: number;
  chunks: number;
  created_at: string | null;
}

interface ChatComposerProps {
  onSend: (message: string) => Promise<void>;
  onUpload: (
    file: File,
  ) => Promise<UploadedChatDocument>;
  disabled?: boolean;
}

const ACCEPTED_FILE_TYPES =
  ".txt,.md,.csv,.json,.pdf";

const MAX_FILE_SIZE =
  10 * 1024 * 1024;

export default function ChatComposer({
  onSend,
  onUpload,
  disabled = false,
}: ChatComposerProps) {
  const [message, setMessage] =
    useState("");

  const [uploading, setUploading] =
    useState(false);

  const [uploadedDocument, setUploadedDocument] =
    useState<UploadedChatDocument | null>(
      null,
    );

  const [uploadError, setUploadError] =
    useState("");

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  async function submit() {
    const value = message.trim();

    if (!value || disabled || uploading) {
      return;
    }

    setMessage("");

    try {
      await onSend(value);

      // The document has already been indexed
      // by the backend, so clear the temporary
      // attachment chip after sending the message.
      setUploadedDocument(null);
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

  function openFilePicker() {
    if (
      disabled ||
      uploading
    ) {
      return;
    }

    fileInputRef.current?.click();
  }

  async function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0];

    // Reset input so selecting the same
    // file again will trigger onChange.
    event.target.value = "";

    if (!file) {
      return;
    }

    setUploadError("");

    if (file.size === 0) {
      setUploadError(
        "The selected document is empty.",
      );
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setUploadError(
        "Maximum document size is 10 MB.",
      );
      return;
    }

    const filename =
      file.name.toLowerCase();

    const isSupported =
      filename.endsWith(".txt") ||
      filename.endsWith(".md") ||
      filename.endsWith(".csv") ||
      filename.endsWith(".json") ||
      filename.endsWith(".pdf");

    if (!isSupported) {
      setUploadError(
        "Unsupported file type. Use TXT, MD, CSV, JSON, or PDF.",
      );
      return;
    }

    setUploading(true);

    try {
      const document =
        await onUpload(file);

      setUploadedDocument(
        document,
      );
    } catch (err) {
      setUploadError(
        err instanceof Error
          ? err.message
          : "Document upload failed.",
      );
    } finally {
      setUploading(false);
    }
  }

  function removeAttachment() {
    setUploadedDocument(null);
    setUploadError("");
  }

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-4xl"
      >
        <div className="relative rounded-2xl border border-slate-200 bg-slate-50 shadow-sm transition focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-50">

          {/* ==================================================
              ATTACHMENT / UPLOAD STATUS
              ================================================== */}

          {uploadedDocument && (
            <div className="px-4 pt-3">
              <div className="inline-flex max-w-full items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700">

                <FileText
                  size={15}
                  className="shrink-0"
                />

                <span className="max-w-[240px] truncate font-medium">
                  {uploadedDocument.filename}
                </span>

                <span className="hidden text-blue-400 sm:inline">
                  {uploadedDocument.chunks} chunks
                </span>

                <button
                  type="button"
                  onClick={
                    removeAttachment
                  }
                  title="Remove attachment"
                  className="ml-1 rounded-md p-0.5 text-blue-400 transition hover:bg-blue-100 hover:text-blue-700"
                >
                  <X size={14} />
                </button>

              </div>
            </div>
          )}

          {uploading && (
            <div className="px-4 pt-3">
              <div className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">

                <Loader2
                  size={14}
                  className="animate-spin text-blue-600"
                />

                <span>
                  Processing document...
                </span>

              </div>
            </div>
          )}

          {uploadError && (
            <div className="px-4 pt-3">
              <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                {uploadError}
              </div>
            </div>
          )}

          {/* ==================================================
              MESSAGE INPUT
              ================================================== */}

          <textarea
            value={message}
            onChange={(event) =>
              setMessage(
                event.target.value,
              )
            }
            onKeyDown={handleKeyDown}
            disabled={
              disabled ||
              uploading
            }
            rows={3}
            placeholder={
              uploadedDocument
                ? "Ask something about this document..."
                : "Ask your assistant anything..."
            }
            className="w-full resize-none bg-transparent px-4 pb-14 pt-4 text-sm text-slate-800 outline-none placeholder:text-slate-400"
          />

          {/* ==================================================
              BOTTOM ACTIONS
              ================================================== */}

          <div className="absolute bottom-3 left-3 flex items-center gap-2">

            {/* Hidden native file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_FILE_TYPES}
              onChange={
                handleFileChange
              }
              className="hidden"
            />

            {/* Paperclip */}
            <button
              type="button"
              onClick={
                openFilePicker
              }
              disabled={
                disabled ||
                uploading
              }
              title={
                uploading
                  ? "Processing document..."
                  : "Attach document"
              }
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-blue-600 disabled:cursor-not-allowed disabled:text-slate-300"
            >
              {uploading ? (
                <Loader2
                  size={17}
                  className="animate-spin"
                />
              ) : (
                <Paperclip
                  size={17}
                />
              )}
            </button>

            <div className="hidden items-center gap-1 text-[11px] text-slate-400 sm:flex">
              <Sparkles
                size={13}
              />
              Persistent context enabled
            </div>

          </div>

          {/* ==================================================
              SEND
              ================================================== */}

          <button
            type="submit"
            disabled={
              disabled ||
              uploading ||
              message.trim().length === 0
            }
            className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <ArrowUp size={17} />
          </button>

        </div>

        <p className="mt-2 text-center text-[10px] text-slate-400">
          Enter to send · Shift + Enter for a new
          line · PDF, TXT, MD, CSV, JSON up to 10 MB
        </p>
      </form>
    </div>
  );
}