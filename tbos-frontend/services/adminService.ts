// ============================================================
// services/adminService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";
import type { User } from "@/types/auth";

const AdminService = {
  async getUsers(params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<User>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<User>>>(
      "/admin/users/",
      { params }
    );
    return data.data;
  },

  async getInstructors(params?: {
    page?: number;
  }): Promise<PaginatedResponse<User>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<User>>>(
      "/admin/instructors/",
      { params }
    );
    return data.data;
  },

  async getStudents(params?: {
    page?: number;
  }): Promise<PaginatedResponse<User>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<User>>>(
      "/admin/students/",
      { params }
    );
    return data.data;
  },

  async activateUser(userId: string): Promise<User> {
    const { data } = await api.post<ApiSuccess<User>>(
      `/admin/users/${userId}/activate/`
    );
    return data.data;
  },

  async deactivateUser(userId: string): Promise<User> {
    const { data } = await api.post<ApiSuccess<User>>(
      `/admin/users/${userId}/deactivate/`
    );
    return data.data;
  },

  async broadcastNotification(payload: {
    title: string;
    message: string;
  }): Promise<{ recipient_count: number }> {
    const { data } = await api.post<ApiSuccess<{ recipient_count: number }>>(
      "/admin/notifications/broadcast/",
      payload
    );
    return data.data;
  },

  async getPayments(params?: {
    status?: string;
    page?: number;
  }) {
    const { data } = await api.get("/admin/payments/", { params });
    return data.data;
  },

  async refundOrder(orderId: string) {
    const { data } = await api.post("/admin/payments/refund/", {
      order_id: orderId,
    });
    return data.data;
  },
};

export default AdminService;
