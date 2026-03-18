// ============================================================
// hooks/useEnrollments.ts
// ============================================================
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import EnrollmentService from "@/services/enrollmentService";
import { QUERY_KEYS } from "@/config/constants";
import { extractApiError } from "@/lib/utils";

export function useMyEnrollments() {
  return useQuery({
    queryKey: QUERY_KEYS.enrollments.list,
    queryFn: EnrollmentService.listMyEnrollments,
    staleTime: 2 * 60 * 1000,
  });
}

export function useEnrollmentProgress(enrollmentId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.enrollments.detail(enrollmentId),
    queryFn: () => EnrollmentService.getProgress(enrollmentId),
    enabled: !!enrollmentId,
  });
}

export function useEnrollCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => EnrollmentService.enroll(courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.enrollments.list });
      toast.success("Successfully enrolled! Start learning now.");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useMarkLessonComplete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      enrollmentId,
      lessonId,
    }: {
      enrollmentId: string;
      lessonId: string;
    }) => EnrollmentService.markLessonComplete(enrollmentId, lessonId),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.enrollments.detail(vars.enrollmentId),
      });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.enrollments.list });
      toast.success("Lesson marked as complete!");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useVideoProgress() {
  return useMutation({
    mutationFn: (payload: {
      video_id: string;
      watch_time_seconds: number;
      last_position_seconds: number;
    }) => EnrollmentService.updateVideoProgress(payload),
  });
}
