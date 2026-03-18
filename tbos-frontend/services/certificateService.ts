// ============================================================
// services/certificateService.ts
// ============================================================

import { api, publicApi } from "@/lib/axios";
import type { ApiSuccess } from "@/types/api";

export interface Certificate {
  id: string;
  certificate_number: string;
  course: string;
  student: string;
  issue_date: string;
  certificate_url: string;
}

export interface CertificateVerification {
  student_name: string;
  course_title: string;
  issue_date: string;
  is_valid: boolean;
}

const CertificateService = {
  async getMyCertificates(): Promise<Certificate[]> {
    const { data } = await api.get<ApiSuccess<Certificate[]>>(
      "/certificates/my/"
    );
    return data.data;
  },

  async verify(verificationCode: string): Promise<CertificateVerification> {
    const { data } = await publicApi.get<ApiSuccess<CertificateVerification>>(
      `/certificates/verify/${verificationCode}/`
    );
    return data.data;
  },

  getDownloadUrl(id: string): string {
    return `${process.env.NEXT_PUBLIC_API_URL}/certificates/${id}/download/`;
  },
};

export default CertificateService;


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

const ReviewService = {
  async getCourseReviews(courseId: string): Promise<PaginatedResponse<Review>> {
    const { data } = await publicApi.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/public/",
      { params: { course: courseId } }
    );
    return data.data;
  },

  async submitReview(payload: {
    course_id: string;
    rating: number;
    review_text: string;
  }): Promise<Review> {
    const { data } = await api.post<ApiSuccess<Review>>(
      "/reviews/student/",
      payload
    );
    return data.data;
  },

  async updateReview(
    id: string,
    payload: { rating?: number; review_text?: string }
  ): Promise<Review> {
    const { data } = await api.patch<ApiSuccess<Review>>(
      `/reviews/student/${id}/`,
      payload
    );
    return data.data;
  },

  async deleteReview(id: string): Promise<void> {
    await api.delete(`/reviews/student/${id}/`);
  },

  async getMyReviews(): Promise<PaginatedResponse<Review>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Review>>>(
      "/reviews/student/"
    );
    return data.data;
  },
};

export default ReviewService;
