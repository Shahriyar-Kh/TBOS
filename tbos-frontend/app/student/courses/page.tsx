// ============================================================
// app/student/courses/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BookOpen, Clock, CheckCircle, Search, ChevronRight, PlayCircle,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { useMyEnrollments } from "@/hooks/useEnrollments";
import { parseProgress, formatDate, cn } from "@/lib/utils";
import type { Enrollment } from "@/types/enrollment";

type TabFilter = "all" | "in_progress" | "completed";

const TAB_OPTIONS: { value: TabFilter; label: string }[] = [
  { value: "all", label: "All courses" },
  { value: "in_progress", label: "In progress" },
  { value: "completed", label: "Completed" },
];

export default function StudentCoursesPage() {
  const [tab, setTab] = useState<TabFilter>("all");
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch } = useMyEnrollments();

  const filtered = data?.results.filter((e) => {
    const matchesTab =
      tab === "all" ||
      (tab === "in_progress" && e.enrollment_status === "active") ||
      (tab === "completed" && e.enrollment_status === "completed");
    const matchesSearch =
      !search ||
      e.course_detail.title.toLowerCase().includes(search.toLowerCase()) ||
      (e.course_detail.instructor_name ?? "")
        .toLowerCase()
        .includes(search.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">My Courses</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.count ?? 0} course{data?.count !== 1 ? "s" : ""} enrolled
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/courses">
            <BookOpen className="h-4 w-4" />
            Browse more
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex rounded-xl border border-border overflow-hidden">
          {TAB_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setTab(value)}
              className={cn(
                "px-4 py-2 text-sm font-medium transition-colors",
                tab === value
                  ? "bg-brand-500 text-white"
                  : "text-muted-foreground hover:bg-slate-50 dark:hover:bg-slate-800"
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <Input
          placeholder="Search courses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
          containerClassName="max-w-xs"
        />
      </div>

      {/* Error */}
      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Loading */}
      {isLoading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-2xl border border-border bg-card overflow-hidden">
              <Skeleton className="aspect-video w-full" />
              <div className="p-4 space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-2 w-full rounded-full" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {!isLoading && !error && filtered?.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border py-20 text-center">
          <BookOpen className="h-12 w-12 text-slate-300" />
          <p className="font-semibold">No courses found</p>
          <p className="text-sm text-muted-foreground">
            {search
              ? "Try adjusting your search"
              : tab !== "all"
              ? "No courses in this category yet"
              : "You haven't enrolled in any courses yet"}
          </p>
          {!search && tab === "all" && (
            <Button size="sm" asChild>
              <Link href="/courses">Browse courses</Link>
            </Button>
          )}
        </div>
      )}

      {/* Course grid */}
      {!isLoading && filtered && filtered.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((enrollment) => (
            <EnrollmentCard key={enrollment.id} enrollment={enrollment} />
          ))}
        </div>
      )}
    </div>
  );
}

function EnrollmentCard({ enrollment }: { enrollment: Enrollment }) {
  const course = enrollment.course_detail;
  const progress = parseProgress(enrollment.progress_percentage);
  const isCompleted = enrollment.enrollment_status === "completed";

  return (
    <Link
      href={`/student/learn/${enrollment.id}`}
      className="group flex flex-col rounded-2xl border border-border bg-card overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:border-brand-200 dark:hover:border-brand-800"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video w-full overflow-hidden bg-slate-100 dark:bg-slate-800">
        {course.thumbnail ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={course.thumbnail}
            alt={course.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <BookOpen className="h-10 w-10 text-slate-300" />
          </div>
        )}
        {/* Play overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/20">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/90 opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
            <PlayCircle className="h-6 w-6 text-slate-900" />
          </div>
        </div>
        {isCompleted && (
          <div className="absolute right-2 top-2 flex items-center gap-1 rounded-full bg-emerald-500 px-2.5 py-1 text-xs font-semibold text-white shadow">
            <CheckCircle className="h-3.5 w-3.5" />
            Completed
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <p className="text-xs font-medium text-brand-500 mb-1">
            {course.category?.name ?? "Course"}
          </p>
          <h3 className="font-semibold text-foreground leading-snug line-clamp-2">
            {course.title}
          </h3>
          {course.instructor_name && (
            <p className="mt-1 text-xs text-muted-foreground">
              {course.instructor_name}
            </p>
          )}
        </div>

        {/* Progress bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {enrollment.completed_lessons_count}/{enrollment.total_lessons_count} lessons
            </span>
            <span className="font-semibold text-foreground">{progress}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                isCompleted ? "bg-emerald-500" : "bg-brand-500"
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="flex-1" />

        {/* Footer */}
        <div className="flex items-center justify-between gap-2 pt-2 border-t border-border">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            {enrollment.last_accessed_at
              ? `Last: ${formatDate(enrollment.last_accessed_at)}`
              : `Enrolled ${formatDate(enrollment.enrolled_at)}`}
          </div>
          <span className="text-xs font-semibold text-brand-600 dark:text-brand-400 group-hover:underline flex items-center gap-0.5">
            {isCompleted ? "Review" : "Continue"}
            <ChevronRight className="h-3.5 w-3.5" />
          </span>
        </div>
      </div>
    </Link>
  );
}
