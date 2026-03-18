// ============================================================
// app/instructor/layout.tsx
// ============================================================
"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Users,
  BarChart3,
  Bell,
  Settings,
  PlusCircle,
  ChevronRight,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { toInitials } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/instructor/dashboard", icon: LayoutDashboard },
  { label: "My Courses", href: "/instructor/courses", icon: BookOpen },
  { label: "Students", href: "/instructor/students", icon: Users },
  { label: "Analytics", href: "/instructor/analytics", icon: BarChart3 },
  { label: "Notifications", href: "/instructor/notifications", icon: Bell },
  { label: "Settings", href: "/instructor/settings", icon: Settings },
];

export default function InstructorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/auth/login?redirect=" + pathname);
      return;
    }
    if (user?.role !== "instructor") {
      router.replace("/auth/login");
    }
  }, [isAuthenticated, user, router, pathname]);

  if (!user || user.role !== "instructor") return null;

  const fullName = `${user.first_name} ${user.last_name}`.trim();

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* ── Sidebar ─── */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border bg-white dark:bg-slate-900 lg:flex">
        <div className="flex h-16 items-center gap-3 border-b border-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
            <GraduationCap className="h-4 w-4 text-white" />
          </div>
          <span className="font-display text-base font-bold tracking-tight">
            Instructor Hub
          </span>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <Link
            href="/instructor/courses/new"
            className="mb-4 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            <PlusCircle className="h-4 w-4" />
            Create Course
          </Link>

          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
            Navigation
          </p>
          <ul className="space-y-0.5">
            {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
              const isActive =
                pathname === href || pathname.startsWith(href + "/");
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                      isActive
                        ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                        : "text-slate-600 hover:bg-slate-50 hover:text-foreground dark:text-slate-400 dark:hover:bg-slate-800"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4 shrink-0",
                        isActive ? "text-indigo-500" : "text-slate-400"
                      )}
                    />
                    {label}
                    {isActive && (
                      <ChevronRight className="ml-auto h-3.5 w-3.5 text-indigo-400" />
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-border p-4">
          <div className="flex items-center gap-3 rounded-xl p-2 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
            <Avatar className="h-9 w-9">
              <AvatarImage src={user.profile?.avatar ?? ""} />
              <AvatarFallback className="bg-indigo-100 text-indigo-700 text-xs">
                {toInitials(fullName || user.email)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-semibold">{fullName}</p>
              <p className="truncate text-xs text-muted-foreground">
                {user.email}
              </p>
            </div>
            <Badge variant="instructor" className="text-[10px] shrink-0">
              Pro
            </Badge>
          </div>
        </div>
      </aside>

      <main className="flex-1 lg:pl-64">
        <div className="min-h-screen p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
