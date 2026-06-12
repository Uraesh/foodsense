"use client";

import Image from "next/image";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

const navItems = ["About", "How it works", "Blog"];

export default function Header() {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const stored = typeof window !== "undefined" && localStorage.getItem("theme");
    if (stored) setTheme(stored);
    else if (window?.matchMedia?.("(prefers-color-scheme: dark)").matches) setTheme("dark");
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <header className="w-full">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <Image
            src="/logo.png"
            alt="FoodSense logo"
            width={36}
            height={36}
            className="h-9 w-9 rounded-lg object-contain"
            priority
          />
          <span className="text-lg font-bold tracking-tight text-ink">
            FoodSense
          </span>
        </div>

        <nav className="flex items-center gap-7">
          {navItems.map((item) => (
            <a
              key={item}
              href={`/${item === "How it works" ? "how-it-works" : item.toLowerCase().replace(/\s+/g, "-")}`}
              className="text-sm font-medium text-slate-700 transition-colors hover:text-brand"
            >
              {item}
            </a>
          ))}
          <button
            aria-label="Toggle theme"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            className="rounded-full p-2 text-slate-600 transition-colors hover:bg-slate-100"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button className="rounded-full border border-brand/30 bg-white px-5 py-2 text-sm font-semibold text-brand shadow-sm transition-colors hover:bg-brand/5">
            Sign in
          </button>
        </nav>
      </div>
    </header>
  );
}
