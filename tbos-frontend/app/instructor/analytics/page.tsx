// ============================================================
// app/instructor/analytics/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp, Users, DollarSign, Star, BookOpen,
  BarChart3, Award, ChevronRight,
} from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { DashboardStatSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import AnalyticsService from "@/services/analyticsService";
import CourseService from "@/services/courseService";
import { QUERY_KEYS } from "@/config/constants";
import { formatCurrency } from "@/lib/utils";

export default function InstructorAnalyticsPage() {
  const {
    data: analytics,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.analytics.instructor,
    queryFn: AnalyticsService.getInstructorDashboard,
  });

  const { data: courses } = useQuery({
    queryKey: QUERY_KEYS.courses.instructorList,
    queryFn: CourseService.listInstructor,
  });

  const METRICS = analytics
    ? [
        {
          label: "Total Revenue",
          value: formatCurrency(analytics.total_revenue),
          icon: DollarSign,
          trend: "+12% this month",
          trendUp: true,
          color: "text-emerald-500",
          bg: "bg-emerald-50 dark:bg-emerald-950/30",
        },
        {
          label: "Total Students",
          value: analytics.total_students.toLocaleString(),
          icon: Users,
          trend: "+8% this month",
          trendUp: true,
          color: "text-brand-500",
          bg: "bg-brand-50 dark:bg-brand-950/30",
        },
        {
          label: "Average Rating",
          value: analytics.average_rating.toFixed(1),
          icon: Star,
          trend: `Across ${analytics.total_courses} courses`,
          trendUp: null,
          color: "text-amber-500",
          bg: "bg-amber-50 dark:bg-amber-950/30",
        },
        {
          label: "Total Courses",
          value: analytics.total_courses,
          icon: BookOpen,
          trend: "Active on platform",
          trendUp: null,
          color: "text-violet-500",
          bg: "bg-violet-50 dark:bg-violet-950/30",
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Analytics</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Track your performance across all courses
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => <DashboardStatSkeleton key={i} />)
          : METRICS.map(({ label, value, icon: Icon, trend, trendUp, color, bg }) => (
              <div key={label} className="stat-card space-y-3">
                <div className="flex items-start justify-between">
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {label}
                  </p>
                  <div className={`rounded-xl p-2 ${bg}`}>
                    <Icon className={`h-4 w-4 ${color}`} />
                  </div>
                </div>
                <p className="font-display text-3xl font-bold text-foreground">
                  {value}
                </p>
                {trend && (
                  <p
                    className={`text-xs ${
                      trendUp === true
                        ? "text-emerald-600 dark:text-emerald-400"
                        : trendUp === false
                        ? "text-red-500"
                        : "text-muted-foreground"
                    }`}
                  >
                    {trendUp === true && "↑ "}
                    {trendUp === false && "↓ "}
                    {trend}
                  </p>
                )}
              </div>
            ))}
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Performance metrics */}
      {analytics && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-muted-foreground" />
                Completion Rates
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {[
                {
                  label: "Course completion rate",
                  value: analytics.course_completion_rate,
                  color: "bg-emerald-500",
                },
                {
                  label: "Lesson completion rate",
                  value: analytics.lesson_completion_rate,
                  color: "bg-brand-500",
                },
                {
                  label: "Quiz pass rate",
                  value: analytics.quiz_performance,
                  color: "bg-violet-500",
                },
              ].map(({ label, value, color }) => (
                <div key={label} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="font-semibold">{value.toFixed(1)}%</span>
                  </div>
                  <Progress
                    value={value}
                    indicatorClassName={color}
                    className="h-2"
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Award className="h-5 w-5 text-muted-foreground" />
                Student Engagement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    label: "Assignment submissions",
                    value: analytics.assignment_submissions,
                    suffix: "total",
                  },
                  {
                    label: "Average quiz score",
                    value: `${analytics.quiz_performance.toFixed(1)}%`,
                    suffix: "per attempt",
                  },
                  {
                    label: "Students enrolled",
                    value: analytics.total_students.toLocaleString(),
                    suffix: "across all courses",
                  },
                ].map(({ label, value, suffix }) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-xl bg-slate-50 p-3 dark:bg-slate-900"
                  >
                    <p className="text-sm text-muted-foreground">{label}</p>
                    <div className="text-right">
                      <p className="font-bold text-foreground">{value}</p>
                      <p className="text-[10px] text-muted-foreground">{suffix}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Per-course breakdown */}
      {courses?.results && courses.results.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Per-Course Performance</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/instructor/courses">
                Manage courses <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Course
                    </th>
                    <th className="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Students
                    </th>
                    <th className="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground hidden md:table-cell">
                      Rating
                    </th>
                    <th className="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {courses.results.map((course) => (
                    <tr
                      key={course.id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
                    >
                      <td className="py-3">
                        <Link
                          href={`/instructor/courses/${course.id}`}
                          className="font-medium hover:text-brand-600 transition-colors"
                        >
                          {course.title.length > 50
                            ? course.title.slice(0, 50) + "…"
                            : course.title}
                        </Link>
                      </td>
                      <td className="py-3 text-right text-muted-foreground">
                        {course.total_enrollments.toLocaleString()}
                      </td>
                      <td className="py-3 text-right text-muted-foreground hidden md:table-cell">
                        <span className="flex items-center justify-end gap-1">
                          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                          {parseFloat(course.average_rating).toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <Badge
                          variant={
                            course.status === "published"
                              ? "success"
                              : course.status === "archived"
                              ? "secondary"
                              : "warning"
                          }
                          className="text-[10px] capitalize"
                        >
                          {course.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
