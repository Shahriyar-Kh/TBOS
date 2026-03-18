// ============================================================
// services/enrollmentService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { Enrollment, LessonProgress } from "@/types/enrollment";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

const EnrollmentService = {
  /** Student: List own enrollments */
  async listMyEnrollments(): Promise<PaginatedResponse<Enrollment>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Enrollment>>>(
      "/enrollments/student/"
    );
    return data.data;
  },

  /** Student: Enroll in free course */
  async enroll(courseId: string): Promise<Enrollment> {
    const { data } = await api.post<ApiSuccess<Enrollment>>(
      "/enrollments/student/enroll/",
      { course_id: courseId }
    );
    return data.data;
  },

  /** Student: Get course progress */
  async getProgress(enrollmentId: string) {
    const { data } = await api.get(
      `/enrollments/student/${enrollmentId}/progress/`
    );
    return data.data;
  },

  /** Student: Mark lesson complete */
  async markLessonComplete(
    enrollmentId: string,
    lessonId: string
  ): Promise<Enrollment> {
    const { data } = await api.post<ApiSuccess<Enrollment>>(
      `/enrollments/student/${enrollmentId}/complete-lesson/`,
      { lesson_id: lessonId }
    );
    return data.data;
  },

  /** Student: Update video progress */
  async updateVideoProgress(payload: {
    video_id: string;
    watch_time_seconds: number;
    last_position_seconds: number;
  }) {
    const { data } = await api.post(
      "/enrollments/student/video-progress/",
      payload
    );
    return data.data;
  },

  /** Instructor: List enrollments for own courses */
  async listInstructorEnrollments(courseId?: string) {
    const params = courseId ? { course: courseId } : {};
    const { data } = await api.get("/enrollments/instructor/", { params });
    return data.data;
  },

  /** Admin: List all enrollments */
  async listAdminEnrollments(filters?: {
    course?: string;
    student?: string;
    status?: string;
  }) {
    const { data } = await api.get("/enrollments/admin/", {
      params: filters,
    });
    return data.data;
  },
};

export default EnrollmentService;
