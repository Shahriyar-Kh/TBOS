// ============================================================
// app/admin/courses/page.tsx — Admin course management
// ============================================================
"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search, BookOpen, Trash2, Eye, MoreHorizontal,
  CheckCircle, Archive, AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  Dropdown, DropdownTrigger, DropdownContent,
  DropdownItem, DropdownSeparator, DropdownLabel,
} from "@/components/ui/Dropdown";
import { TableRowSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import {
  Modal, ModalContent, ModalHeader, ModalTitle,
  ModalDescription, ModalFooter,
} from "@/components/ui/Modal";
import CourseService from "@/services/courseService";
import { formatDate, extractApiError } from "@/lib/utils";
import type { Course } from "@/types/course";

const STATUS_BADGE: Record<string, "success" | "warning" | "secondary"> = {
  published: "success",
  draft: "warning",
  archived: "secondary",
};

export default function AdminCoursesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deleteTarget, setDeleteTarget] = useState<Course | null>(null);
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-courses", { search, status: statusFilter, page }],
    queryFn: () =>
      CourseService.listAdmin({
        search: search || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        page,
        page_size: 15,
      }),
    placeholderData: (prev) => prev,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => CourseService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
      toast.success("Course deleted.");
      setDeleteTarget(null);
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => CourseService.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
      toast.success("Course published.");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const STATUS_OPTIONS = ["all", "published", "draft", "archived"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">Courses</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.count ?? 0} total courses on the platform
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Search courses or instructors…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          leftIcon={<Search className="h-4 w-4" />}
          containerClassName="max-w-xs"
        />
        <div className="flex gap-1.5">
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition-colors ${
                statusFilter === s
                  ? "bg-brand-500 text-white"
                  : "border border-border text-muted-foreground hover:bg-slate-50"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Table */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Course
                </th>
                <th className="hidden px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground md:table-cell">
                  Instructor
                </th>
                <th className="hidden px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground lg:table-cell">
                  Students
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <TableRowSkeleton key={i} cols={5} />
                  ))
                : data?.results.map((course) => (
                    <tr
                      key={course.id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-14 shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
                            {course.thumbnail && (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img
                                src={course.thumbnail}
                                alt=""
                                className="h-full w-full object-cover"
                              />
                            )}
                          </div>
                          <div>
                            <Link
                              href={`/courses/${course.slug}`}
                              className="font-semibold text-foreground hover:text-brand-600 transition-colors line-clamp-1"
                              target="_blank"
                            >
                              {course.title}
                            </Link>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {course.total_lessons} lessons · {course.duration_hours}h
                              {course.is_free ? " · Free" : ` · $${course.price}`}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="hidden px-5 py-4 text-sm text-muted-foreground md:table-cell">
                        {course.instructor_name}
                      </td>
                      <td className="hidden px-5 py-4 text-right text-sm text-muted-foreground lg:table-cell">
                        {course.total_enrollments.toLocaleString()}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <Badge
                          variant={STATUS_BADGE[course.status] ?? "secondary"}
                          className="text-[10px]"
                        >
                          {course.status}
                        </Badge>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <Dropdown>
                          <DropdownTrigger asChild>
                            <Button variant="ghost" size="icon-sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownTrigger>
                          <DropdownContent align="end">
                            <DropdownLabel>Actions</DropdownLabel>
                            <DropdownItem asChild>
                              <Link href={`/courses/${course.slug}`} target="_blank">
                                <Eye className="h-4 w-4 text-slate-400" />
                                View public page
                              </Link>
                            </DropdownItem>
                            {course.status === "draft" && (
                              <DropdownItem
                                onClick={() => publishMutation.mutate(course.id)}
                              >
                                <CheckCircle className="h-4 w-4 text-emerald-500" />
                                Publish course
                              </DropdownItem>
                            )}
                            <DropdownSeparator />
                            <DropdownItem
                              className="text-red-500 focus:text-red-500"
                              onClick={() => setDeleteTarget(course)}
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete course
                            </DropdownItem>
                          </DropdownContent>
                        </Dropdown>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        {/* Pagination footer */}
        {data && (data.next || data.previous) && (
          <div className="flex items-center justify-between border-t border-border px-5 py-3">
            <p className="text-xs text-muted-foreground">
              Showing {((page - 1) * 15) + 1}–{Math.min(page * 15, data.count)} of {data.count}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm" variant="outline"
                onClick={() => setPage((p) => p - 1)}
                disabled={!data.previous}
              >
                Prev
              </Button>
              <Button
                size="sm" variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.next}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Delete confirmation modal */}
      <Modal open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <ModalContent>
          <ModalHeader>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-100 dark:bg-red-950/30 mb-2">
              <AlertTriangle className="h-6 w-6 text-red-500" />
            </div>
            <ModalTitle>Delete Course</ModalTitle>
            <ModalDescription>
              Are you sure you want to permanently delete{" "}
              <strong>&quot;{deleteTarget?.title}&quot;</strong>? This will
              remove all enrollments, lessons, and associated data. This action
              cannot be undone.
            </ModalDescription>
          </ModalHeader>
          <ModalFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              isLoading={deleteMutation.isPending}
              loadingText="Deleting…"
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            >
              Delete permanently
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
}
