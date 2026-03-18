// ============================================================
// app/instructor/students/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Users, TrendingUp, CheckCircle } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Progress } from "@/components/ui/Progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import EnrollmentService from "@/services/enrollmentService";
import { toInitials, formatDate, parseProgress } from "@/lib/utils";

export default function InstructorStudentsPage() {
  const [search, setSearch] = useState("");
  const [courseFilter, setCourseFilter] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["instructor-enrollments", courseFilter],
    queryFn: () =>
      EnrollmentService.listInstructorEnrollments(courseFilter || undefined),
  });

  const enrollments = data?.results ?? (Array.isArray(data) ? (data as unknown[]) : []);

  const filtered = (enrollments as Array<{
    id: string;
    student_email?: string;
    student_name?: string;
    course_detail?: { id: string; title: string };
    course?: string;
    enrollment_status: string;
    progress_percentage: string;
    completed_lessons_count: number;
    total_lessons_count: number;
    enrolled_at: string;
    last_accessed_at: string | null;
  }>).filter((e) => {
    if (!search) return true;
    const name = (e.student_name ?? "").toLowerCase();
    const email = (e.student_email ?? "").toLowerCase();
    const q = search.toLowerCase();
    return name.includes(q) || email.includes(q);
  });

  const totalStudents = filtered.length;
  const completedCount = filtered.filter(
    (e) => e.enrollment_status === "completed"
  ).length;
  const avgProgress =
    filtered.length > 0
      ? filtered.reduce((sum, e) => sum + parseProgress(e.progress_percentage), 0) /
        filtered.length
      : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Students</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Monitor student progress across your courses
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-brand-50 p-3 dark:bg-brand-950/30">
              <Users className="h-5 w-5 text-brand-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalStudents}</p>
              <p className="text-xs text-muted-foreground">Total students</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-emerald-50 p-3 dark:bg-emerald-950/30">
              <CheckCircle className="h-5 w-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{completedCount}</p>
              <p className="text-xs text-muted-foreground">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-violet-50 p-3 dark:bg-violet-950/30">
              <TrendingUp className="h-5 w-5 text-violet-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{Math.round(avgProgress)}%</p>
              <p className="text-xs text-muted-foreground">Avg. progress</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Input
        placeholder="Search students by name or email…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        leftIcon={<Search className="h-4 w-4" />}
        containerClassName="max-w-sm"
      />

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Table */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Student
                </th>
                <th className="hidden px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground md:table-cell">
                  Course
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Progress
                </th>
                <th className="hidden px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground lg:table-cell">
                  Enrolled
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 5 }).map((__, j) => (
                        <td key={j} className="px-5 py-4">
                          <Skeleton className="h-4 w-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-16 text-center">
                        <Users className="mx-auto mb-3 h-10 w-10 text-slate-300" />
                        <p className="text-sm text-muted-foreground">
                          {search ? "No students match your search" : "No students enrolled yet"}
                        </p>
                      </td>
                    </tr>
                  )
                : filtered.map((enrollment) => {
                    const progress = parseProgress(enrollment.progress_percentage);
                    const name = enrollment.student_name ?? "Unknown";
                    const email = enrollment.student_email ?? "";
                    const course = enrollment.course_detail;

                    return (
                      <tr
                        key={enrollment.id}
                        className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors"
                      >
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8 shrink-0">
                              <AvatarFallback className="text-xs">
                                {toInitials(name)}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-semibold text-foreground">{name}</p>
                              <p className="text-xs text-muted-foreground">{email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="hidden px-5 py-4 text-sm text-muted-foreground md:table-cell">
                          <p className="max-w-[200px] truncate">
                            {course?.title ?? "—"}
                          </p>
                        </td>
                        <td className="px-5 py-4">
                          <div className="space-y-1.5 min-w-[120px]">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">
                                {enrollment.completed_lessons_count}/{enrollment.total_lessons_count}
                              </span>
                              <span className="font-semibold">{progress}%</span>
                            </div>
                            <Progress
                              value={progress}
                              className="h-1.5"
                              indicatorClassName={
                                enrollment.enrollment_status === "completed"
                                  ? "bg-emerald-500"
                                  : "bg-brand-500"
                              }
                            />
                          </div>
                        </td>
                        <td className="hidden px-5 py-4 text-right text-xs text-muted-foreground lg:table-cell">
                          {formatDate(enrollment.enrolled_at)}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Badge
                            variant={
                              enrollment.enrollment_status === "completed"
                                ? "success"
                                : enrollment.enrollment_status === "cancelled"
                                ? "destructive"
                                : "default"
                            }
                            className="text-[10px] capitalize"
                          >
                            {enrollment.enrollment_status}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
