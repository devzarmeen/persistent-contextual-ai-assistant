"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { apiFetch } from "@/lib/api";
import type { AuthResponse, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (
    name: string,
    email: string,
    password: string,
  ) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("access_token");

    if (!savedToken) {
      setLoading(false);
      return;
    }

    setToken(savedToken);

    apiFetch<User>("/api/auth/me", {
      token: savedToken,
    })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("access_token");
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  async function login(
    email: string,
    password: string,
  ): Promise<User> {
    const response = await apiFetch<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    });

    localStorage.setItem("access_token", response.access_token);

    setToken(response.access_token);
    setUser(response.user);

    return response.user;
  }

  async function register(
    name: string,
    email: string,
    password: string,
  ): Promise<User> {
    const response = await apiFetch<AuthResponse>(
      "/api/auth/register",
      {
        method: "POST",
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      },
    );

    localStorage.setItem("access_token", response.access_token);

    setToken(response.access_token);
    setUser(response.user);

    return response.user;
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
    window.location.href = "/login";
  }

  async function refreshUser() {
    const savedToken = localStorage.getItem("access_token");

    if (!savedToken) {
      setUser(null);
      setToken(null);
      return;
    }

    const currentUser = await apiFetch<User>("/api/auth/me", {
      token: savedToken,
    });

    setUser(currentUser);
    setToken(savedToken);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}