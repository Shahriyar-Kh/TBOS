// ============================================================
// services/notificationService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

export interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  reference_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPreferences {
  email_notifications_enabled: boolean;
  in_app_notifications_enabled: boolean;
  course_updates: boolean;
  assignment_notifications: boolean;
  quiz_notifications: boolean;
}

const NotificationService = {
  async list(params?: { is_read?: boolean }) {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Notification>>>(
      "/notifications/",
      { params }
    );
    return data.data;
  },

  async markRead(id: string): Promise<Notification> {
    const { data } = await api.put<ApiSuccess<Notification>>(
      `/notifications/${id}/read/`
    );
    return data.data;
  },

  async markAllRead() {
    const { data } = await api.put("/notifications/read-all/");
    return data.data;
  },

  async getPreferences(): Promise<NotificationPreferences> {
    const { data } = await api.get<ApiSuccess<NotificationPreferences>>(
      "/notifications/preferences/"
    );
    return data.data;
  },

  async updatePreferences(
    payload: Partial<NotificationPreferences>
  ): Promise<NotificationPreferences> {
    const { data } = await api.put<ApiSuccess<NotificationPreferences>>(
      "/notifications/preferences/",
      payload
    );
    return data.data;
  },
};

export default NotificationService;
