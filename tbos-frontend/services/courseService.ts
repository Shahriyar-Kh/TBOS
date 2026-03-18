// ============================================================
// services/courseService.ts
// ============================================================

import { api, publicApi } from "@/lib/axios";
import type { Course, CourseCreatePayload } from "@/types/course";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

export interface CourseFilters {
  search?: string;
  category__slug?: string;
  level__id?: string;
  is_free?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

const CourseService = {
  /** Public: List published courses */
  async listPublic(
    filters: CourseFilters = {}
  ): Promise<PaginatedResponse<Course>> {
    const { data } = await publicApi.get<ApiSuccess<PaginatedResponse<Course>>>(
      "/courses/",
      { params: filters }
    );
    return data.data;
  },

  /** Public: Course detail by slug */
  async getBySlug(slug: string): Promise<Course> {
    const { data } = await publicApi.get<ApiSuccess<Course>>(
      `/courses/${slug}/`
    );
    return data.data;
  },

  /** Public: Course curriculum */
  async getCurriculum(slug: string) {
    const { data } = await publicApi.get(`/courses/${slug}/curriculum/`);
    return data.data;
  },

  /** Instructor: List own courses */
  async listInstructor(): Promise<PaginatedResponse<Course>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Course>>>(
      "/courses/instructor/courses/"
    );
    return data.data;
  },

  /** Instructor: Create course */
  async create(payload: CourseCreatePayload): Promise<Course> {
    const { data } = await api.post<ApiSuccess<Course>>(
      "/courses/instructor/courses/",
      payload
    );
    return data.data;
  },

  /** Instructor: Update course */
  async update(id: string, payload: Partial<CourseCreatePayload>): Promise<Course> {
    const { data } = await api.patch<ApiSuccess<Course>>(
      `/courses/instructor/courses/${id}/`,
      payload
    );
    return data.data;
  },

  /** Instructor: Publish course */
  async publish(id: string): Promise<Course> {
    const { data } = await api.post<ApiSuccess<Course>>(
      `/courses/instructor/courses/${id}/publish/`
    );
    return data.data;
  },

  /** Instructor: Archive course */
  async archive(id: string): Promise<Course> {
    const { data } = await api.post<ApiSuccess<Course>>(
      `/courses/instructor/courses/${id}/archive/`
    );
    return data.data;
  },

  /** Admin: List all courses */
  async listAdmin(filters: CourseFilters = {}): Promise<PaginatedResponse<Course>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Course>>>(
      "/courses/admin/courses/",
      { params: filters }
    );
    return data.data;
  },

  /** Admin: Delete course */
  async delete(id: string): Promise<void> {
    await api.delete(`/courses/admin/courses/${id}/`);
  },
};

export default CourseService;
