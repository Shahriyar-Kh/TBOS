// ============================================================
// hooks/useRealtimeAnalytics.ts
// Realtime WebSocket analytics with React Query cache updates
// ============================================================
"use client";

import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getWSInstance, type WSMessage } from "@/lib/websocket";
import { QUERY_KEYS } from "@/config/constants";
import { useAuthStore } from "@/store/authStore";

type EventType =
  | "student_dashboard_updated"
  | "instructor_dashboard_updated"
  | "admin_dashboard_updated"
  | "course_analytics_updated";

export function useStudentRealtimeAnalytics() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const wsRef = useRef(getWSInstance("/ws/analytics/dashboard/"));

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.message === "student_dashboard_updated") {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.analytics.student });
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!user || user.role !== "student") return;
    const ws = wsRef.current;
    ws.connect("/ws/analytics/dashboard/");
    const unsub = ws.subscribe(handleMessage);
    return () => {
      unsub();
      ws.disconnect();
    };
  }, [user, handleMessage]);
}

export function useInstructorRealtimeAnalytics() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const wsRef = useRef(getWSInstance("/ws/analytics/dashboard/"));

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.message === "instructor_dashboard_updated") {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.analytics.instructor,
        });
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.courses.instructorList,
        });
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!user || user.role !== "instructor") return;
    const ws = wsRef.current;
    ws.connect("/ws/analytics/dashboard/");
    const unsub = ws.subscribe(handleMessage);
    return () => {
      unsub();
      ws.disconnect();
    };
  }, [user, handleMessage]);
}

export function useAdminRealtimeAnalytics() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const wsRef = useRef(getWSInstance("/ws/analytics/dashboard/"));

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.message === "admin_dashboard_updated") {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.analytics.admin(),
        });
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!user || user.role !== "admin") return;
    const ws = wsRef.current;
    ws.connect("/ws/analytics/dashboard/");
    const unsub = ws.subscribe(handleMessage);
    return () => {
      unsub();
      ws.disconnect();
    };
  }, [user, handleMessage]);
}

export function useCourseRealtimeAnalytics(courseId: string) {
  const queryClient = useQueryClient();
  const wsRef = useRef(
    getWSInstance(`/ws/analytics/course/${courseId}/`)
  );

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      if (msg.message === "course_analytics_updated") {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.analytics.instructor,
        });
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!courseId) return;
    const ws = wsRef.current;
    ws.connect(`/ws/analytics/course/${courseId}/`);
    const unsub = ws.subscribe(handleMessage);
    return () => {
      unsub();
      ws.disconnect();
    };
  }, [courseId, handleMessage]);
}
