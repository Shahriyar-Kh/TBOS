// ============================================================
// app/admin/dashboard/page.tsx
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Users, BookOpen, DollarSign, Star,
  TrendingUp, ChevronRight, GraduationCap, UserCheck,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DashboardStatSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { formatCurrency } from "@/lib/utils";
import AnalyticsService from "@/services/analyticsService";
import { QUERY_KEYS } from "@/config/constants";

export default function AdminDashboardPage() {
  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.analytics.admin(),
    queryFn: () => AnalyticsService.getAdminDashboard(),
  });

  const STATS = analytics
    ? [
        { label: "Total Users", value: analytics.total_users.toLocaleString(), icon: Users, color: "text-brand-500", bg: "bg-brand-50 dark:bg-brand-950/30" },
        { label: "Students", value: analytics.total_students.toLocaleString(), icon: GraduationCap, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30" },
        { label: "Instructors", value: analytics.total_instructors.toLocaleString(), icon: UserCheck, color: "text-indigo-500", bg: "bg-indigo-50 dark:bg-indigo-950/30" },
        { label: "Courses", value: analytics.total_courses.toLocaleString(), icon: BookOpen, color: "text-violet-500", bg: "bg-violet-50 dark:bg-violet-950/30" },
        { label: "Enrollments", value: analytics.total_enrollments.toLocaleString(), icon: TrendingUp, color: "text-orange-500", bg: "bg-orange-50 dark:bg-orange-950/30" },
        { label: "Total Revenue", value: formatCurrency(analytics.total_revenue), icon: DollarSign, color: "text-pink-500", bg: "bg-pink-50 dark:bg-pink-950/30" },
        { label: "Completion Rate", value: `${analytics.course_completion_rate}%`, icon: Star, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30" },
        { label: "Avg. Rating", value: analytics.average_platform_rating.toFixed(1), icon: Star, color: "text-yellow-500", bg: "bg-yellow-50 dark:bg-yellow-950/30" },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">Platform Overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">Real-time metrics across TechBuilt Open School</p>
        </div>
        <Button size="sm" variant="outline" asChild>
          <Link href="/admin/analytics">
            <TrendingUp className="h-4 w-4" />
            Full analytics
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <DashboardStatSkeleton key={i} />)
          : error ? null
          : STATS.map(({ label, value, icon: Icon, color, bg }) => (
              <div key={label} className="stat-card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
                    <p className="mt-2 font-display text-2xl font-bold text-foreground lg:text-3xl">{value}</p>
                  </div>
                  <div className={`rounded-xl p-2.5 ${bg}`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                </div>
              </div>
            ))}
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Insights */}
      {analytics?.insights && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Popular courses */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Most Popular Courses</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/courses">View all <ChevronRight className="h-4 w-4" /></Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {analytics.insights.most_popular_courses.map((c, i) => (
                <div key={c.id} className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-slate-500 dark:bg-slate-800">
                    {i + 1}
                  </span>
                  <p className="flex-1 truncate text-sm font-medium">{c.title}</p>
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Users className="h-3.5 w-3.5" />
                    {c.student_count.toLocaleString()}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Revenue leaders */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Top Revenue Courses</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/admin/analytics">Details <ChevronRight className="h-4 w-4" /></Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {analytics.insights.highest_revenue_courses.map((c, i) => (
                <div key={c.id} className="flex items-center gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold text-slate-500 dark:bg-slate-800">
                    {i + 1}
                  </span>
                  <p className="flex-1 truncate text-sm font-medium">{c.title}</p>
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    {c.revenue ? formatCurrency(c.revenue) : "—"}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
