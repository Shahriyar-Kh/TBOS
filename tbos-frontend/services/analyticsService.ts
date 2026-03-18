// ============================================================
// services/analyticsService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { ApiSuccess } from "@/types/api";

export interface StudentAnalytics {
  courses_enrolled: number;
  courses_completed: number;
  lessons_completed: number;
  quizzes_attempted: number;
  assignments_submitted: number;
  certificates_earned: number;
  learning_streak_days: number;
  learning_hours: number;
  average_quiz_score: number;
}

export interface InstructorAnalytics {
  total_courses: number;
  total_students: number;
  total_revenue: string;
  average_rating: number;
  course_completion_rate: number;
  lesson_completion_rate: number;
  quiz_performance: number;
  assignment_submissions: number;
}

export interface AdminAnalytics {
  total_users: number;
  total_students: number;
  total_instructors: number;
  total_courses: number;
  total_enrollments: number;
  total_revenue: string;
  course_completion_rate: number;
  average_platform_rating: number;
  insights: {
    most_popular_courses: Array<{ id: string; title: string; student_count: number }>;
    highest_completion_rate_courses: Array<{ id: string; title: string; completion_rate: number }>;
    most_engaged_students: Array<{ user: string; activity_count: number }>;
    highest_revenue_courses: Array<{ id: string; title: string; revenue: string }>;
  };
}

const AnalyticsService = {
  async getStudentDashboard(): Promise<{ overview: StudentAnalytics; insights: unknown }> {
    const { data } = await api.get("/analytics/student/dashboard/");
    return data.data;
  },

  async getInstructorDashboard(): Promise<InstructorAnalytics> {
    const { data } = await api.get("/analytics/instructor/dashboard/");
    return data.data;
  },

  async getAdminDashboard(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<AdminAnalytics> {
    const { data } = await api.get("/analytics/admin/dashboard/", { params });
    return data.data;
  },

  async trackActivity(payload: {
    activity_type: string;
    reference_id?: string;
  }) {
    const { data } = await api.post("/analytics/activity/", payload);
    return data.data;
  },

  async getRevenueAnalytics(params?: {
    start_date?: string;
    end_date?: string;
  }) {
    const { data } = await api.get("/analytics/admin/revenue/", { params });
    return data.data;
  },
};

export default AnalyticsService;
