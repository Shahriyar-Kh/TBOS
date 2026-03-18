// ============================================================
// components/layout/Navbar.tsx
// ============================================================
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Bell,
  Menu,
  X,
  ChevronDown,
  LogOut,
  User,
  LayoutDashboard,
  Settings,
  GraduationCap,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useLogout } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar";
import { toInitials, formatRelativeTime } from "@/lib/utils";
import { ROLE_ROUTES } from "@/config/constants";
import type { UserRole } from "@/types/auth";

const NAV_LINKS = [
  { label: "Courses", href: "/courses" },
  { label: "About", href: "/about" },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const pathname = usePathname();
  const { user, isAuthenticated } = useAuthStore();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close dropdowns on route change
  useEffect(() => {
    setMobileOpen(false);
    setProfileOpen(false);
  }, [pathname]);

  const dashboardHref = user?.role
    ? ROLE_ROUTES[user.role as UserRole]
    : "/auth/login";

  const fullName = user
    ? `${user.first_name} ${user.last_name}`.trim()
    : "";

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        isScrolled
          ? "border-b border-border bg-white/90 shadow-sm backdrop-blur-md dark:bg-slate-900/90"
          : "bg-transparent"
      )}
    >
      <nav className="section-container flex h-16 items-center justify-between">
        {/* ── Logo ─── */}
        <Link
          href="/"
          className="flex items-center gap-2.5 text-foreground transition-opacity hover:opacity-80"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500">
            <GraduationCap className="h-4.5 w-4.5 text-white" size={18} />
          </div>
          <span className="font-display text-lg font-700 tracking-tight hidden sm:block">
            TechBuilt<span className="text-brand-500">OS</span>
          </span>
        </Link>

        {/* ── Desktop Nav Links ─── */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                pathname === link.href
                  ? "text-brand-600 dark:text-brand-400"
                  : "text-slate-600 hover:text-foreground dark:text-slate-400 dark:hover:text-white"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* ── Right Side ─── */}
        <div className="flex items-center gap-2">
          {isAuthenticated && user ? (
            <>
              {/* Notifications Bell */}
              <Button
                variant="ghost"
                size="icon"
                className="relative text-slate-500 hover:text-foreground"
                asChild
              >
                <Link href="/notifications">
                  <Bell size={18} />
                  {/* Unread dot — hydrated dynamically */}
                  <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-brand-500 ring-2 ring-white dark:ring-slate-900" />
                </Link>
              </Button>

              {/* Dashboard shortcut */}
              <Button variant="ghost" size="sm" asChild className="hidden md:flex">
                <Link href={dashboardHref}>
                  <LayoutDashboard size={15} className="mr-1.5" />
                  Dashboard
                </Link>
              </Button>

              {/* Profile dropdown */}
              <div className="relative">
                <button
                  onClick={() => setProfileOpen((p) => !p)}
                  className="flex items-center gap-2 rounded-full p-1 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.profile?.avatar ?? ""} />
                    <AvatarFallback className="bg-brand-100 text-brand-700 text-xs font-semibold">
                      {toInitials(fullName || user.email)}
                    </AvatarFallback>
                  </Avatar>
                  <ChevronDown
                    size={14}
                    className={cn(
                      "hidden text-slate-400 transition-transform sm:block",
                      profileOpen && "rotate-180"
                    )}
                  />
                </button>

                {profileOpen && (
                  <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-border bg-white shadow-lg dark:bg-slate-900">
                    <div className="border-b border-border px-4 py-3">
                      <p className="text-sm font-semibold text-foreground truncate">
                        {fullName || "User"}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {user.email}
                      </p>
                      <span className="mt-1 inline-block rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                        {user.role}
                      </span>
                    </div>
                    <div className="py-1">
                      <DropdownLink href="/profile" icon={<User size={15} />}>
                        Profile
                      </DropdownLink>
                      <DropdownLink href={dashboardHref} icon={<LayoutDashboard size={15} />}>
                        Dashboard
                      </DropdownLink>
                      <DropdownLink href="/settings" icon={<Settings size={15} />}>
                        Settings
                      </DropdownLink>
                    </div>
                    <div className="border-t border-border py-1">
                      <button
                        onClick={() => logout()}
                        disabled={isLoggingOut}
                        className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
                      >
                        <LogOut size={15} />
                        {isLoggingOut ? "Signing out…" : "Sign out"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" asChild className="hidden sm:flex">
                <Link href="/auth/login">Sign in</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/auth/register">Get started</Link>
              </Button>
            </>
          )}

          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen((p) => !p)}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </Button>
        </div>
      </nav>

      {/* ── Mobile Menu ─── */}
      {mobileOpen && (
        <div className="border-t border-border bg-white px-4 py-4 shadow-lg dark:bg-slate-900 md:hidden">
          <div className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-foreground dark:text-slate-400 dark:hover:bg-slate-800"
              >
                {link.label}
              </Link>
            ))}
            {isAuthenticated ? (
              <Link
                href={dashboardHref}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Sign in
                </Link>
                <Link
                  href="/auth/register"
                  className="mt-1 rounded-lg bg-brand-500 px-3 py-2.5 text-center text-sm font-semibold text-white"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

function DropdownLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
    >
      <span className="text-slate-400">{icon}</span>
      {children}
    </Link>
  );
}
