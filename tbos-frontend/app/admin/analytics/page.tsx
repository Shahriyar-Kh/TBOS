// ============================================================
// app/admin/analytics/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp, Users, DollarSign, BookOpen, GraduationCap,
  UserCheck, Star, BarChart3, Award, CalendarDays,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { DashboardStatSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import AnalyticsService from "@/services/analyticsService";
import { QUERY_KEYS } from "@/config/constants";
import { formatCurrency } from "@/lib/utils";

export default function AdminAnalyticsPage() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [applied, setApplied] = useState({ start: "", end: "" });

  const { data: analytics, isLoading, error, refetch } = useQuery({
    queryKey: QUERY_KEYS.analytics.admin(applied),
    queryFn: () =>
      AnalyticsService.getAdminDashboard({
        start_date: applied.start || undefined,
        end_date: applied.end || undefined,
      }),
  });

  const { data: revenue, isLoading: revenueLoading } = useQuery({
    queryKey: ["admin-revenue", applied],
    queryFn: () =>
      AnalyticsService.getRevenueAnalytics({
        start_date: applied.start || undefined,
        end_date: applied.end || undefined,
      }),
  });

  const PLATFORM_STATS = analytics
    ? [
        {
          label: "Total Users",
          value: analytics.total_users.toLocaleString(),
          icon: Users,
          color: "text-brand-500",
          bg: "bg-brand-50 dark:bg-brand-950/30",
        },
        {
          label: "Students",
          value: analytics.total_students.toLocaleString(),
          icon: GraduationCap,
          color: "text-emerald-500",
          bg: "bg-emerald-50 dark:bg-emerald-950/30",
        },
        {
          label: "Instructors",
          value: analytics.total_instructors.toLocaleString(),
          icon: UserCheck,
          color: "text-indigo-500",
          bg: "bg-indigo-50 dark:bg-indigo-950/30",
        },
        {
          label: "Total Courses",
          value: analytics.total_courses.toLocaleString(),
          icon: BookOpen,
          color: "text-violet-500",
          bg: "bg-violet-50 dark:bg-violet-950/30",
        },
        {
          label: "Enrollments",
          value: analytics.total_enrollments.toLocaleString(),
          icon: TrendingUp,
          color: "text-orange-500",
          bg: "bg-orange-50 dark:bg-orange-950/30",
        },
        {
          label: "Platform Revenue",
          value: formatCurrency(analytics.total_revenue),
          icon: DollarSign,
          color: "text-pink-500",
          bg: "bg-pink-50 dark:bg-pink-950/30",
        },
        {
          label: "Completion Rate",
          value: `${analytics.course_completion_rate}%`,
          icon: Award,
          color: "text-amber-500",
          bg: "bg-amber-50 dark:bg-amber-950/30",
        },
        {
          label: "Avg. Rating",
          value: analytics.average_platform_rating.toFixed(1),
          icon: Star,
          color: "text-yellow-500",
          bg: "bg-yellow-50 dark:bg-yellow-950/30",
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">Analytics</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Platform-wide performance metrics
          </p>
        </div>
      </div>

      {/* Date range filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              Date range
            </div>
            <Input
              type="date"
              label="From"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              containerClassName="max-w-[160px]"
            />
            <Input
              type="date"
              label="To"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              containerClassName="max-w-[160px]"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => setApplied({ start: startDate, end: endDate })}
              >
                Apply filter
              </Button>
              {(applied.start || applied.end) && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setStartDate("");
                    setEndDate("");
                    setApplied({ start: "", end: "" });
                  }}
                >
                  Clear
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <DashboardStatSkeleton key={i} />)
          : PLATFORM_STATS.map(({ label, value, icon: Icon, color, bg }) => (
              <div key={label} className="stat-card space-y-3">
                <div className="flex items-start justify-between">
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {label}
                  </p>
                  <div className={`rounded-xl p-2 ${bg}`}>
                    <Icon className={`h-4 w-4 ${color}`} />
                  </div>
                </div>
                <p className="font-display text-2xl font-bold text-foreground lg:text-3xl">
                  {value}
                </p>
              </div>
            ))}
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Revenue & rates */}
      {analytics && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Revenue card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-muted-foreground" />
                Revenue Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {revenueLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
                  ))}
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      {
                        label: "Total Revenue",
                        value: formatCurrency(
                          (revenue as { total_revenue?: string })?.total_revenue ?? "0"
                        ),
                      },
                      {
                        label: "Total Orders",
                        value: (revenue as { total_orders?: number })?.total_orders?.toLocaleString() ?? "0",
                      },
                      {
                        label: "Avg. Order Value",
                        value: formatCurrency(
                          (revenue as { average_order_value?: string })?.average_order_value ?? "0"
                        ),
                      },
                      {
                        label: "Platform Revenue",
                        value: formatCurrency(analytics.total_revenue),
                      },
                    ].map(({ label, value }) => (
                      <div
                        key={label}
                        className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900"
                      >
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                          {label}
                        </p>
                        <p className="mt-1 text-lg font-bold text-foreground">
                          {value}
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Completion rates */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-muted-foreground" />
                Platform Health
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {[
                {
                  label: "Course completion rate",
                  value: analytics.course_completion_rate,
                  color: "bg-emerald-500",
                  status:
                    analytics.course_completion_rate >= 70
                      ? "Excellent"
                      : analytics.course_completion_rate >= 50
                      ? "Good"
                      : "Needs improvement",
                },
                {
                  label: "Platform utilisation",
                  value: Math.min(
                    100,
                    (analytics.total_enrollments / Math.max(analytics.total_students, 1)) * 100
                  ),
                  color: "bg-brand-500",
                  status: "Enrollments per student",
                },
                {
                  label: "Average rating",
                  value: (analytics.average_platform_rating / 5) * 100,
                  color: "bg-amber-500",
                  status: `${analytics.average_platform_rating.toFixed(1)} / 5.0`,
                },
              ].map(({ label, value, color, status }) => (
                <div key={label} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="text-xs text-muted-foreground">{status}</span>
                  </div>
                  <Progress value={value} indicatorClassName={color} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Insights */}
      {analytics?.insights && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Most Popular Courses
              </CardTitle>
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

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Top Revenue Courses
              </CardTitle>
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
