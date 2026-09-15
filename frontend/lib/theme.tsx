"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(
  undefined,
);

const THEME_STORAGE_KEY = "context-ai-theme";

function applyTheme(theme: Theme, animate = false) {
  const root = document.documentElement;

  if (animate) {
    root.classList.add("theme-transition");

    window.setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 220);
  }

  root.classList.toggle("dark", theme === "dark");
  root.dataset.theme = theme;
}

export function ThemeProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [theme, setThemeState] = useState<Theme>("dark");

  useEffect(() => {
    const storedTheme = localStorage.getItem(
      THEME_STORAGE_KEY,
    ) as Theme | null;

    const initialTheme: Theme =
      storedTheme === "light" || storedTheme === "dark"
        ? storedTheme
        : "dark";

    setThemeState(initialTheme);
    applyTheme(initialTheme);
  }, []);

  function setTheme(nextTheme: Theme) {
    setThemeState(nextTheme);

    localStorage.setItem(
      THEME_STORAGE_KEY,
      nextTheme,
    );

    applyTheme(nextTheme, true);
  }

  function toggleTheme() {
    setTheme(theme === "dark" ? "light" : "dark");
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error(
      "useTheme must be used inside ThemeProvider",
    );
  }

  return context;
}