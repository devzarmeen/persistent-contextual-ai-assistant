"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { Brain, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import Button from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, user, loading } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      await register(name, email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create account.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen bg-slate-50">
      <section className="hidden flex-1 bg-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-2.5">
            <Sparkles size={20} />
          </div>

          <div>
            <p className="font-bold">ContextAI</p>
            <p className="text-xs text-slate-400">
              Persistent Contextual AI
            </p>
          </div>
        </div>

        <div className="max-w-lg">
          <Brain size={42} className="text-blue-400" />

          <h1 className="mt-6 text-4xl font-bold leading-tight">
            Build a memory layer around your AI.
          </h1>

          <p className="mt-5 text-slate-400">
            Keep useful context across conversations, documents
            and verified workflows.
          </p>
        </div>

        <p className="text-xs text-slate-500">
          Persistent Contextual AI Assistant
        </p>
      </section>

      <section className="flex w-full items-center justify-center p-6 lg:w-[520px]">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Sparkles className="text-blue-600" />
            <h1 className="mt-3 text-xl font-bold">
              ContextAI
            </h1>
          </div>

          <h2 className="text-2xl font-bold text-slate-900">
            Create your account
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Start building your persistent AI workspace.
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-8 space-y-5"
          >
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Name
              </label>

              <input
                required
                value={name}
                onChange={(event) =>
                  setName(event.target.value)
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Email
              </label>

              <input
                type="email"
                required
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Password
              </label>

              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                placeholder="At least 8 characters"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <Button
              type="submit"
              loading={submitting}
              className="w-full"
              size="lg"
            >
              Create Account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Sign in
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}