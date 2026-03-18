// ============================================================
// hooks/useNotifications.ts
// ============================================================
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import NotificationService from "@/services/notificationService";
import { QUERY_KEYS } from "@/config/constants";
import { extractApiError } from "@/lib/utils";

export function useNotifications(isRead?: boolean) {
  return useQuery({
    queryKey: QUERY_KEYS.notifications.list(isRead),
    queryFn: () => NotificationService.list(isRead !== undefined ? { is_read: isRead } : {}),
    refetchInterval: 60_000, // poll every 60s
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => NotificationService.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: NotificationService.markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast.success("All notifications marked as read.");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ["notifications", "preferences"],
    queryFn: NotificationService.getPreferences,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: NotificationService.updatePreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", "preferences"] });
      toast.success("Notification preferences saved.");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => NotificationService.markAllRead(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      const count = (data as { updated_count?: number })?.updated_count ?? 0;
      if (count > 0) {
        toast.success(`${count} notification${count !== 1 ? "s" : ""} marked as read.`);
      }
    },
    onError: (err) => toast.error(extractApiError(err)),
  });
}
