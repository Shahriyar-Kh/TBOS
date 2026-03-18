// ============================================================
// app/auth/layout.tsx — Auth pages layout
// ============================================================

import type { Metadata } from "next";
import Link from "next/link";
import { GraduationCap } from "lucide-react";

export const metadata: Metadata = {
  title: { default: "Auth", template: "%s | TechBuilt Open School" },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      {/* ── Left panel — Brand ─── */}
      <div className="relative hidden w-[45%] flex-col justify-between overflow-hidden bg-slate-950 p-12 lg:flex">
        {/* Background pattern */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `radial-gradient(circle at 20% 80%, rgba(30,184,229,0.3) 0%, transparent 50%),
                              radial-gradient(circle at 80% 20%, rgba(14,148,194,0.2) 0%, transparent 50%)`,
          }}
        />
        {/* Grid texture */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)`,
            backgroundSize: "48px 48px",
          }}
        />

        {/* Logo */}
        <Link href="/" className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 shadow-lg">
            <GraduationCap className="h-5 w-5 text-white" />
          </div>
          <span className="font-display text-xl font-bold text-white tracking-tight">
            TechBuilt<span className="text-brand-400">OS</span>
          </span>
        </Link>

        {/* Hero copy */}
        <div className="relative space-y-6">
          <blockquote className="space-y-3">
            <p className="font-display text-3xl font-bold leading-snug text-white">
              "Education is the most powerful weapon which you can use to change
              the world."
            </p>
            <footer className="text-sm text-slate-400">— Nelson Mandela</footer>
          </blockquote>

          <div className="grid grid-cols-3 gap-4 pt-4">
            {[
              { value: "50k+", label: "Students" },
              { value: "200+", label: "Courses" },
              { value: "98%", label: "Satisfaction" },
            ].map(({ value, label }) => (
              <div
                key={label}
                className="rounded-xl border border-white/10 bg-white/5 p-4 text-center backdrop-blur-sm"
              >
                <p className="font-display text-2xl font-bold text-brand-400">
                  {value}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel — Form ─── */}
      <div className="flex flex-1 flex-col items-center justify-center bg-white px-6 py-12 dark:bg-slate-950 lg:px-16">
        {/* Mobile logo */}
        <Link href="/" className="mb-10 flex items-center gap-2.5 lg:hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500">
            <GraduationCap className="h-4 w-4 text-white" />
          </div>
          <span className="font-display text-lg font-bold tracking-tight">
            TechBuilt<span className="text-brand-500">OS</span>
          </span>
        </Link>

        <div className="w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  );
}
