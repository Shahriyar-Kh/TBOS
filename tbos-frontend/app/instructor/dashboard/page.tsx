// ============================================================
// app/instructor/dashboard/page.tsx
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  BookOpen,
  Users,
  DollarSign,
  Star,
  TrendingUp,
  ChevronRight,
  PlusCircle,
  BarChart3,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DashboardStatSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { formatCurrency } from "@/lib/utils";
import AnalyticsService from "@/services/analyticsService";
import { QUERY_KEYS } from "@/config/constants";
import { useAuthStore } from "@/store/authStore";
import { useInstructorCourses } from "@/hooks/useCourses";

export default function InstructorDashboardPage() {
  const { user } = useAuthStore();

  const {
    data: analytics,
    isLoading: analyticsLoading,
    error: analyticsError,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.analytics.instructor,
    queryFn: AnalyticsService.getInstructorDashboard,
  });

  const { data: courses, isLoading: coursesLoading } = useInstructorCourses();

  const STATS = analytics
    ? [
        {
          label: "Total Courses",
          value: analytics.total_courses,
          icon: BookOpen,
          color: "text-brand-500",
          bg: "bg-brand-50 dark:bg-brand-950/30",
        },
        {
          label: "Total Students",
          value: analytics.total_students.toLocaleString(),
          icon: Users,
          color: "text-emerald-500",
          bg: "bg-emerald-50 dark:bg-emerald-950/30",
        },
        {
          label: "Total Revenue",
          value: formatCurrency(analytics.total_revenue),
          icon: DollarSign,
          color: "text-violet-500",
          bg: "bg-violet-50 dark:bg-violet-950/30",
        },
        {
          label: "Avg. Rating",
          value: analytics.average_rating.toFixed(1),
          icon: Star,
          color: "text-amber-500",
          bg: "bg-amber-50 dark:bg-amber-950/30",
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* ── Header ─── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">
            Instructor Dashboard
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your courses and track student progress
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/instructor/courses/new">
            <PlusCircle className="h-4 w-4" />
            Create course
          </Link>
        </Button>
      </div>

      {/* ── Stats ─── */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {analyticsLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <DashboardStatSkeleton key={i} />
            ))
          : analyticsError
          ? null
          : STATS.map(({ label, value, icon: Icon, color, bg }) => (
              <div key={label} className="stat-card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      {label}
                    </p>
                    <p className="mt-2 font-display text-2xl font-bold text-foreground lg:text-3xl">
                      {value}
                    </p>
                  </div>
                  <div className={`rounded-xl p-2.5 ${bg}`}>
                    <Icon className={`h-5 w-5 ${color}`} />
                  </div>
                </div>
              </div>
            ))}
      </div>

      {analyticsError && (
        <QueryError error={analyticsError as Error} onRetry={refetch} />
      )}

      {/* ── Performance row ─── */}
      {analytics && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-5 space-y-2">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Course Completion Rate
              </p>
              <p className="text-3xl font-bold">
                {analytics.course_completion_rate.toFixed(1)}%
              </p>
              <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{
                    width: `${analytics.course_completion_rate}%`,
                  }}
                />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 space-y-2">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Quiz Performance
              </p>
              <p className="text-3xl font-bold">
                {analytics.quiz_performance.toFixed(1)}%
              </p>
              <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{ width: `${analytics.quiz_performance}%` }}
                />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 space-y-2">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Assignment Submissions
              </p>
              <p className="text-3xl font-bold">
                {analytics.assignment_submissions}
              </p>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
                Total submissions received
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Courses table ─── */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
            Your Courses
          </CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/instructor/courses">
              View all
              <ChevronRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {coursesLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          ) : !courses?.results?.length ? (
            <div className="py-12 text-center">
              <BookOpen className="mx-auto mb-3 h-10 w-10 text-slate-300" />
              <p className="text-sm text-muted-foreground">
                You haven&apos;t created any courses yet.
              </p>
              <Button size="sm" className="mt-4" asChild>
                <Link href="/instructor/courses/new">Create your first course</Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 text-left font-semibold text-muted-foreground">
                      Course
                    </th>
                    <th className="pb-3 text-right font-semibold text-muted-foreground hidden sm:table-cell">
                      Students
                    </th>
                    <th className="pb-3 text-right font-semibold text-muted-foreground hidden md:table-cell">
                      Rating
                    </th>
                    <th className="pb-3 text-right font-semibold text-muted-foreground">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {courses.results.slice(0, 8).map((course) => (
                    <tr
                      key={course.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="py-3">
                        <Link
                          href={`/instructor/courses/${course.id}`}
                          className="font-medium text-foreground hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                        >
                          {course.title.length > 45
                            ? course.title.slice(0, 45) + "…"
                            : course.title}
                        </Link>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {course.total_lessons} lessons ·{" "}
                          {course.duration_hours}h
                        </p>
                      </td>
                      <td className="py-3 text-right text-muted-foreground hidden sm:table-cell">
                        {course.total_enrollments.toLocaleString()}
                      </td>
                      <td className="py-3 text-right hidden md:table-cell">
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
                          className="text-[10px]"
                        >
                          {course.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
