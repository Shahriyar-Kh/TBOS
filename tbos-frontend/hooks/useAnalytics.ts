// ============================================================
// hooks/useAnalytics.ts
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import AnalyticsService from "@/services/analyticsService";
import { QUERY_KEYS } from "@/config/constants";

export function useStudentDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.analytics.student,
    queryFn: AnalyticsService.getStudentDashboard,
    staleTime: 5 * 60 * 1000,
  });
}

export function useInstructorDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.analytics.instructor,
    queryFn: AnalyticsService.getInstructorDashboard,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAdminDashboard(params?: {
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: QUERY_KEYS.analytics.admin(params),
    queryFn: () => AnalyticsService.getAdminDashboard(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useRevenueAnalytics(params?: {
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ["analytics", "revenue", params],
    queryFn: () => AnalyticsService.getRevenueAnalytics(params),
  });
}
