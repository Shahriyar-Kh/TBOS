// ============================================================
// services/quizService.ts
// ============================================================

import { api } from "@/lib/axios";
import type { ApiSuccess, PaginatedResponse } from "@/types/api";

export interface Quiz {
  id: string;
  course: string;
  lesson: string | null;
  title: string;
  description: string;
  time_limit_minutes: number | null;
  max_attempts: number;
  passing_score: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  is_active: boolean;
  order: number;
  question_count: number;
  created_at: string;
}

export interface QuizDetail extends Quiz {
  questions: QuizQuestion[];
}

export interface QuizQuestion {
  id: string;
  question_text: string;
  order: number;
  points: number;
  options: QuizOption[];
}

export interface QuizOption {
  id: string;
  option_text: string;
  order: number;
}

export interface QuizAttempt {
  id: string;
  quiz: string;
  student: string;
  attempt_number: number;
  score: number;
  total_points: number;
  total_questions: number;
  correct_answers: number;
  percentage: string;
  passed: boolean;
  start_time: string;
  end_time: string | null;
  status: "in_progress" | "submitted" | "expired";
}

export interface QuizResult extends QuizAttempt {
  quiz_title: string;
  answers: Array<{
    id: string;
    question: string;
    selected_option: string | null;
    is_correct: boolean;
  }>;
}

const QuizService = {
  /** Student: list available quizzes for enrolled courses */
  async listStudentQuizzes(): Promise<Quiz[]> {
    const { data } = await api.get<ApiSuccess<Quiz[]>>("/quiz/student/");
    return data.data;
  },

  /** Student: get quiz detail (no correct answers) */
  async getStudentQuiz(id: string): Promise<QuizDetail> {
    const { data } = await api.get<ApiSuccess<QuizDetail>>(
      `/quiz/student/${id}/`
    );
    return data.data;
  },

  /** Student: start a quiz attempt */
  async startQuiz(quizId: string): Promise<{
    attempt: QuizAttempt;
    questions: QuizQuestion[];
  }> {
    const { data } = await api.post(
      `/quiz/student/${quizId}/start/`
    );
    return data.data;
  },

  /** Student: submit a single answer */
  async submitAnswer(
    quizId: string,
    questionId: string,
    optionId: string
  ): Promise<{ submitted: boolean; answer_id: string }> {
    const { data } = await api.post(
      `/quiz/student/${quizId}/submit-answer/`,
      { question_id: questionId, option_id: optionId }
    );
    return data.data;
  },

  /** Student: submit entire quiz */
  async submitQuiz(quizId: string): Promise<QuizResult> {
    const { data } = await api.post<ApiSuccess<QuizResult>>(
      `/quiz/student/${quizId}/submit/`
    );
    return data.data;
  },

  /** Student: get quiz results */
  async getQuizResults(quizId: string): Promise<QuizResult[]> {
    const { data } = await api.get<ApiSuccess<QuizResult[]>>(
      `/quiz/student/${quizId}/result/`
    );
    return data.data;
  },

  /** Instructor: list own quizzes */
  async listInstructorQuizzes(courseId?: string): Promise<PaginatedResponse<Quiz>> {
    const { data } = await api.get<ApiSuccess<PaginatedResponse<Quiz>>>(
      "/quiz/instructor/quizzes/",
      { params: courseId ? { course: courseId } : {} }
    );
    return data.data;
  },

  /** Instructor: create quiz */
  async createQuiz(payload: Partial<Quiz>): Promise<Quiz> {
    const { data } = await api.post<ApiSuccess<Quiz>>(
      "/quiz/instructor/quizzes/",
      payload
    );
    return data.data;
  },

  /** Instructor: update quiz */
  async updateQuiz(id: string, payload: Partial<Quiz>): Promise<Quiz> {
    const { data } = await api.patch<ApiSuccess<Quiz>>(
      `/quiz/instructor/quizzes/${id}/`,
      payload
    );
    return data.data;
  },

  /** Instructor: delete quiz */
  async deleteQuiz(id: string): Promise<void> {
    await api.delete(`/quiz/instructor/quizzes/${id}/`);
  },
};

export default QuizService;
