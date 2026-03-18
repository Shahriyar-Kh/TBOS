// ============================================================
// app/instructor/courses/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import Link from "next/link";
import {
  PlusCircle, Search, MoreHorizontal, BookOpen, Edit3,
  Eye, Archive, Trash2, Users, Star, BarChart3,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  Dropdown, DropdownTrigger, DropdownContent,
  DropdownItem, DropdownSeparator,
} from "@/components/ui/Dropdown";
import {
  Modal, ModalContent, ModalHeader, ModalTitle,
  ModalDescription, ModalFooter,
} from "@/components/ui/Modal";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import {
  useInstructorCourses, usePublishCourse,
  useArchiveCourse, useDeleteCourse,
} from "@/hooks/useCourses";
import { formatCurrency, cn } from "@/lib/utils";
import type { Course } from "@/types/course";

export default function InstructorCoursesPage() {
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Course | null>(null);

  const { data, isLoading, error, refetch } = useInstructorCourses();
  const { mutate: publish, isPending: publishing } = usePublishCourse();
  const { mutate: archive, isPending: archiving } = useArchiveCourse();
  const { mutate: deleteCourse, isPending: deleting } = useDeleteCourse();

  const courses = data?.results.filter(
    (c) =>
      !search ||
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      (c.category?.name ?? "").toLowerCase().includes(search.toLowerCase())
  );

  const STATUS_VARIANT: Record<
    string,
    "success" | "warning" | "secondary" | "default"
  > = {
    published: "success",
    draft: "warning",
    archived: "secondary",
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">My Courses</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.count ?? 0} course{data?.count !== 1 ? "s" : ""}
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/instructor/courses/new">
            <PlusCircle className="h-4 w-4" />
            New course
          </Link>
        </Button>
      </div>

      {/* Search */}
      <Input
        placeholder="Search courses…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        leftIcon={<Search className="h-4 w-4" />}
        containerClassName="max-w-sm"
      />

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 rounded-xl border border-border p-4">
              <Skeleton className="h-14 w-20 shrink-0 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <Skeleton className="h-7 w-20 rounded-full" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
          ))}
        </div>
      ) : !courses?.length ? (
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border py-20 text-center">
          <BookOpen className="h-12 w-12 text-slate-300" />
          <p className="font-semibold">
            {search ? "No courses match your search" : "No courses yet"}
          </p>
          {!search && (
            <Button size="sm" asChild>
              <Link href="/instructor/courses/new">Create your first course</Link>
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {courses.map((course) => (
            <div
              key={course.id}
              className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-sm"
            >
              {/* Thumbnail */}
              <div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
                {course.thumbnail ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={course.thumbnail}
                    alt={course.title}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <BookOpen className="h-5 w-5 text-slate-400" />
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <Link
                  href={`/instructor/courses/${course.id}`}
                  className="font-semibold text-foreground hover:text-brand-600 dark:hover:text-brand-400 transition-colors line-clamp-1"
                >
                  {course.title}
                </Link>
                <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" />
                    {course.total_enrollments.toLocaleString()} students
                  </span>
                  {parseFloat(course.average_rating) > 0 && (
                    <span className="flex items-center gap-1">
                      <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                      {parseFloat(course.average_rating).toFixed(1)}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <BarChart3 className="h-3.5 w-3.5" />
                    {formatCurrency(course.effective_price ?? course.price)}
                  </span>
                </div>
              </div>

              {/* Status */}
              <Badge
                variant={STATUS_VARIANT[course.status] ?? "default"}
                className="shrink-0"
              >
                {course.status}
              </Badge>

              {/* Actions menu */}
              <Dropdown>
                <DropdownTrigger asChild>
                  <Button variant="ghost" size="icon-sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownTrigger>
                <DropdownContent align="end">
                  <DropdownItem asChild>
                    <Link href={`/instructor/courses/${course.id}`}>
                      <Edit3 className="h-4 w-4 text-muted-foreground" />
                      Edit course
                    </Link>
                  </DropdownItem>
                  <DropdownItem asChild>
                    <Link href={`/courses/${course.slug}`} target="_blank">
                      <Eye className="h-4 w-4 text-muted-foreground" />
                      Preview
                    </Link>
                  </DropdownItem>
                  {course.status === "draft" && (
                    <DropdownItem
                      onClick={() => publish(course.id)}
                      disabled={publishing}
                    >
                      <BarChart3 className="h-4 w-4 text-emerald-500" />
                      Publish
                    </DropdownItem>
                  )}
                  {course.status === "published" && (
                    <DropdownItem
                      onClick={() => archive(course.id)}
                      disabled={archiving}
                    >
                      <Archive className="h-4 w-4 text-amber-500" />
                      Archive
                    </DropdownItem>
                  )}
                  <DropdownSeparator />
                  <DropdownItem
                    className="text-destructive focus:text-destructive"
                    onClick={() => setDeleteTarget(course)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </DropdownItem>
                </DropdownContent>
              </Dropdown>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation modal */}
      <Modal
        open={!!deleteTarget}
        onOpenChange={(v) => !v && setDeleteTarget(null)}
      >
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Delete course?</ModalTitle>
            <ModalDescription>
              Are you sure you want to delete{" "}
              <span className="font-semibold text-foreground">
                {deleteTarget?.title}
              </span>
              ? This action cannot be undone and will remove all enrollments.
            </ModalDescription>
          </ModalHeader>
          <ModalFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              isLoading={deleting}
              loadingText="Deleting…"
              onClick={() => {
                if (deleteTarget) {
                  deleteCourse(deleteTarget.id, {
                    onSuccess: () => setDeleteTarget(null),
                  });
                }
              }}
            >
              Delete course
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
