// ============================================================
// app/student/dashboard/page.tsx
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Clock,
  Award,
  TrendingUp,
  Flame,
  Target,
  ChevronRight,
  Star,
} from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  DashboardStatSkeleton,
  CourseCardSkeleton,
} from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { parseProgress } from "@/lib/utils";
import AnalyticsService from "@/services/analyticsService";
import EnrollmentService from "@/services/enrollmentService";
import { QUERY_KEYS } from "@/config/constants";
import { useAuthStore } from "@/store/authStore";

export default function StudentDashboardPage() {
  const { user } = useAuthStore();

  const {
    data: analytics,
    isLoading: analyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: QUERY_KEYS.analytics.student,
    queryFn: AnalyticsService.getStudentDashboard,
  });

  const { data: enrollments, isLoading: enrollmentsLoading } = useQuery({
    queryKey: QUERY_KEYS.enrollments.list,
    queryFn: EnrollmentService.listMyEnrollments,
  });

  const overview = analytics?.overview;

  const STATS = overview
    ? [
        {
          label: "Courses Enrolled",
          value: overview.courses_enrolled,
          icon: BookOpen,
          color: "text-brand-500",
          bg: "bg-brand-50 dark:bg-brand-950/30",
        },
        {
          label: "Courses Completed",
          value: overview.courses_completed,
          icon: Award,
          color: "text-emerald-500",
          bg: "bg-emerald-50 dark:bg-emerald-950/30",
        },
        {
          label: "Learning Hours",
          value: `${overview.learning_hours}h`,
          icon: Clock,
          color: "text-violet-500",
          bg: "bg-violet-50 dark:bg-violet-950/30",
        },
        {
          label: "Day Streak",
          value: overview.learning_streak_days,
          icon: Flame,
          color: "text-orange-500",
          bg: "bg-orange-50 dark:bg-orange-950/30",
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* ── Header ─── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-foreground lg:text-3xl">
            Welcome back, {user?.first_name}! 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Track your learning progress and continue where you left off.
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/courses">
            <BookOpen className="h-4 w-4" />
            Browse courses
          </Link>
        </Button>
      </div>

      {/* ── Stat cards ─── */}
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
                    <p className="mt-2 font-display text-3xl font-bold text-foreground">
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

      {/* ── Analytics error ─── */}
      {analyticsError && (
        <QueryError
          error={analyticsError as Error}
          onRetry={refetchAnalytics}
        />
      )}

      {/* ── Additional stats ─── */}
      {overview && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-xl bg-sky-50 p-3 dark:bg-sky-950/30">
                <Target className="h-5 w-5 text-sky-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{overview.lessons_completed}</p>
                <p className="text-xs text-muted-foreground">Lessons completed</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-xl bg-purple-50 p-3 dark:bg-purple-950/30">
                <TrendingUp className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {overview.average_quiz_score}%
                </p>
                <p className="text-xs text-muted-foreground">Avg. quiz score</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-5">
              <div className="rounded-xl bg-amber-50 p-3 dark:bg-amber-950/30">
                <Star className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {overview.certificates_earned}
                </p>
                <p className="text-xs text-muted-foreground">
                  Certificates earned
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── In-progress courses ─── */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Continue Learning</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/student/courses">
              View all
              <ChevronRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {enrollmentsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-3 rounded-xl border border-border p-3">
                  <div className="h-14 w-20 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800 shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
                    <div className="h-2 w-full animate-pulse rounded-full bg-slate-100 dark:bg-slate-800" />
                    <div className="h-3 w-1/4 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
                  </div>
                </div>
              ))}
            </div>
          ) : !enrollments?.results?.length ? (
            <div className="py-10 text-center">
              <BookOpen className="mx-auto mb-3 h-10 w-10 text-slate-300" />
              <p className="text-sm text-muted-foreground">
                You haven&apos;t enrolled in any courses yet.
              </p>
              <Button size="sm" className="mt-4" asChild>
                <Link href="/courses">Find a course</Link>
              </Button>
            </div>
          ) : (
            enrollments.results.slice(0, 5).map((enrollment) => {
              const progress = parseProgress(enrollment.progress_percentage);
              const course = enrollment.course_detail;
              return (
                <Link
                  key={enrollment.id}
                  href={`/student/courses/${enrollment.id}`}
                  className="flex items-center gap-4 rounded-xl border border-border p-3 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-100">
                    {course.thumbnail && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={course.thumbnail}
                        alt={course.title}
                        className="h-full w-full object-cover"
                      />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {course.title}
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <div className="flex-1 rounded-full bg-slate-100 dark:bg-slate-700">
                        <div
                          className="h-1.5 rounded-full bg-brand-500 transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className="shrink-0 text-xs font-medium text-muted-foreground">
                        {progress}%
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge
                        variant={
                          enrollment.enrollment_status === "completed"
                            ? "success"
                            : "default"
                        }
                        className="text-[10px]"
                      >
                        {enrollment.enrollment_status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {enrollment.completed_lessons_count}/
                        {enrollment.total_lessons_count} lessons
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-slate-300" />
                </Link>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
