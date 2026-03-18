// ============================================================
// hooks/useCourses.ts
// ============================================================
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import CourseService, { type CourseFilters } from "@/services/courseService";
import { QUERY_KEYS } from "@/config/constants";
import { extractApiError } from "@/lib/utils";
import type { CourseCreatePayload } from "@/types/course";

export function usePublicCourses(filters: CourseFilters = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.courses.list(filters),
    queryFn: () => CourseService.listPublic(filters),
    staleTime: 2 * 60 * 1000,
  });
}

export function useCourseDetail(slug: string) {
  return useQuery({
    queryKey: QUERY_KEYS.courses.detail(slug),
    queryFn: () => CourseService.getBySlug(slug),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCourseCurriculum(slug: string) {
  return useQuery({
    queryKey: QUERY_KEYS.courses.curriculum(slug),
    queryFn: () => CourseService.getCurriculum(slug),
    enabled: !!slug,
  });
}

export function useInstructorCourses() {
  return useQuery({
    queryKey: QUERY_KEYS.courses.instructorList,
    queryFn: CourseService.listInstructor,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CourseCreatePayload) => CourseService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.courses.instructorList,
      });
      toast.success("Course created successfully!");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function usePublishCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => CourseService.publish(id),
    onSuccess: (course) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.courses.instructorList,
      });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.courses.detail(course.slug),
      });
      toast.success("Course published!");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useArchiveCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => CourseService.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.courses.instructorList,
      });
      toast.success("Course archived.");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useDeleteCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => CourseService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.courses.instructorList,
      });
      toast.success("Course deleted.");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}
