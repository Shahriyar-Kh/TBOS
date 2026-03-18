// ============================================================
// services/reviewService.ts
// ============================================================

import { api, publicApi } from "@/lib/axios";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

export interface Review {
  id: string;
  student: string;
  student_name: string;
  course: string;
  rating: number;
  review_text: string;
  status: "published" | "pending" | "rejected";
  instructor_response: {
    id: string;
    instructor_name: string;
    response_text: string;
    created_at: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewCreatePayload {
  course_id: string;
  rating: number;
  review_text: string;
}

export interface ReviewUpdatePayload {
  rating?: number;
  review_text?: string;
}

const ReviewService = {
  /** Public: Get all published reviews for a course */
  async getCourseReviews(courseId: string): Promise<PaginatedResponse<Review>> {
    const { data } = await publicApi.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/public/",
      { params: { course: courseId } }
    );
    return data.data;
  },

  /** Student: Get my reviews */
  async getMyReviews(): Promise<PaginatedResponse<Review>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/student/"
    );
    return data.data;
  },

  /** Student: Create review */
  async createReview(payload: ReviewCreatePayload): Promise<Review> {
    const { data } = await api.post<ApiSuccess<Review>>(
      "/reviews/student/",
      payload
    );
    return data.data;
  },

  /** Student: Update review */
  async updateReview(id: string, payload: ReviewUpdatePayload): Promise<Review> {
    const { data } = await api.patch<ApiSuccess<Review>>(
      `/reviews/student/${id}/`,
      payload
    );
    return data.data;
  },

  /** Student: Delete review */
  async deleteReview(id: string): Promise<void> {
    await api.delete(`/reviews/student/${id}/`);
  },

  /** Instructor: List reviews for own courses */
  async listInstructorReviews(courseId?: string): Promise<PaginatedResponse<Review>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/instructor/",
      { params: courseId ? { course: courseId } : {} }
    );
    return data.data;
  },

  /** Instructor: Respond to review */
  async respondToReview(
    reviewId: string,
    responseText: string
  ): Promise<Review> {
    const { data } = await api.post<ApiSuccess<Review>>(
      "/reviews/instructor/respond/",
      { review_id: reviewId, response_text: responseText }
    );
    return data.data;
  },

  /** Admin: List all reviews */
  async listAdminReviews(params?: {
    status?: string;
    course?: string;
  }): Promise<PaginatedResponse<Review>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/admin/",
      { params }
    );
    return data.data;
  },

  /** Admin: Moderate review */
  async moderateReview(
    id: string,
    status: "published" | "rejected"
  ): Promise<Review> {
    const { data } = await api.put<ApiSuccess<Review>>(
      `/reviews/admin/${id}/moderate/`,
      { status }
    );
    return data.data;
  },
};

export default ReviewService;
