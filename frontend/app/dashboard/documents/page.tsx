"use client";

import {
  FileText,
  Search,
  Upload,
  Trash2,
  Loader2,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Card from "@/components/ui/Card";
import { apiFetch, apiUpload } from "@/lib/api";
import type {
  Document,
  DocumentSearchResult,
} from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>(
    [],
  );

  const [results, setResults] = useState<
    DocumentSearchResult[]
  >([]);

  const [query, setQuery] = useState("");

  const [uploading, setUploading] = useState(false);

  const [searching, setSearching] = useState(false);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [deletingId, setDeletingId] =
    useState<number | null>(null);

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);

    try {
      setError("");

      const data = await apiFetch<Document[]>(
        "/api/documents",
      );

      setDocuments(
        Array.isArray(data) ? data : [],
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load documents.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();

      formData.append("file", file);

      await apiUpload<Document>(
        "/api/documents/upload",
        formData,
      );

      setResults([]);

      setQuery("");

      await loadDocuments();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Document upload failed.",
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function searchDocuments() {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setResults([]);
      return;
    }

    setSearching(true);
    setError("");

    try {
      const data =
        await apiFetch<DocumentSearchResult[]>(
          `/api/documents/search?q=${encodeURIComponent(
            trimmedQuery,
          )}`,
        );

      setResults(
        Array.isArray(data) ? data : [],
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Document search failed.",
      );
    } finally {
      setSearching(false);
    }
  }

  async function deleteDocument(
    document: Document,
  ) {
    const confirmed = window.confirm(
      `Are you sure you want to delete this document?\n\n"${document.filename}"\n\nThis will permanently remove the document and its stored chunks.`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(document.id);
    setError("");

    try {
      await apiFetch<void>(
        `/api/documents/${document.id}`,
        {
          method: "DELETE",
        },
      );

      // Remove deleted document from the UI.
      setDocuments((current) =>
        current.filter(
          (item) => item.id !== document.id,
        ),
      );

      // Remove search results belonging to deleted document.
      setResults((current) =>
        current.filter(
          (item) =>
            item.document_id !== document.id,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to delete document.",
      );
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <DashboardShell>
      <div className="space-y-6">
        <section>
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
              <FileText size={21} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Documents
              </h1>

              <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                Upload your knowledge and search it using
                semantic retrieval.
              </p>
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        <Card className="p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <Upload size={18} />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Upload Document
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                Supported files: TXT, MD, CSV, JSON and PDF.
                Maximum size: 10 MB.
              </p>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.csv,.json,.pdf"
            onChange={handleUpload}
            className="hidden"
          />

          <button
            type="button"
            onClick={() =>
              fileInputRef.current?.click()
            }
            disabled={uploading}
            className="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? (
              <Loader2
                size={17}
                className="animate-spin"
              />
            ) : (
              <Upload size={17} />
            )}

            {uploading
              ? "Uploading..."
              : "Choose Document"}
          </button>
        </Card>

        <Card className="p-5">
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Semantic Document Search
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Search across your uploaded document chunks.
            </p>
          </div>

          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <div className="relative min-w-0 flex-1">
              <Search
                size={17}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                type="text"
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    void searchDocuments();
                  }
                }}
                placeholder="Search your documents..."
                className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 dark:focus:ring-blue-950"
              />
            </div>

            <button
              type="button"
              onClick={() =>
                void searchDocuments()
              }
              disabled={searching}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
            >
              {searching ? (
                <Loader2
                  size={16}
                  className="animate-spin"
                />
              ) : (
                <Search size={16} />
              )}

              {searching
                ? "Searching..."
                : "Search"}
            </button>
          </div>

          {results.length > 0 && (
            <div className="mt-5 space-y-3">
              {results.map((result, index) => (
                <div
                  key={`${result.document_id}-${result.chunk_index}-${index}`}
                  className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {result.filename}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        Chunk {result.chunk_index}
                      </p>
                    </div>

                    <span className="w-fit shrink-0 rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
                      Similarity{" "}
                      {Number(
                        result.similarity,
                      ).toFixed(3)}
                    </span>
                  </div>

                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {result.content}
                  </p>
                </div>
              ))}
            </div>
          )}

          {!searching &&
            query.trim() &&
            results.length === 0 && (
              <div className="mt-5 rounded-xl border border-dashed border-slate-200 p-6 text-center dark:border-slate-800">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No matching document chunks found.
                </p>
              </div>
            )}
        </Card>

        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 p-5 dark:border-slate-800">
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Your Documents
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Documents available to your persistent
              assistant.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center p-10">
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400" />

                Loading documents...
              </div>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-10 text-center">
              <FileText
                size={30}
                className="mx-auto text-slate-300 dark:text-slate-700"
              />

              <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                No documents uploaded yet.
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Upload your first document above.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.map((document) => (
                <div
                  key={document.id}
                  className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      <FileText size={18} />
                    </div>

                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {document.filename}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {formatBytes(
                          document.file_size,
                        )}{" "}
                        · {document.chunks} chunks
                      </p>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-3">
                    <div className="text-xs text-slate-400">
                      {formatDate(
                        document.created_at,
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        void deleteDocument(
                          document,
                        )
                      }
                      disabled={
                        deletingId === document.id
                      }
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/60 dark:text-red-400 dark:hover:bg-red-950/30"
                    >
                      {deletingId ===
                      document.id ? (
                        <Loader2
                          size={15}
                          className="animate-spin"
                        />
                      ) : (
                        <Trash2 size={15} />
                      )}

                      {deletingId ===
                      document.id
                        ? "Deleting..."
                        : "Delete"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}