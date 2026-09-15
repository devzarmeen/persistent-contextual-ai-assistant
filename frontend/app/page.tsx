"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";
import Loading from "@/components/ui/Loading";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;

    router.replace(user ? "/dashboard" : "/login");
  }, [loading, user, router]);

  return <Loading text="Opening ContextAI..." />;
}