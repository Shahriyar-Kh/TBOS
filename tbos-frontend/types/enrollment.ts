// ============================================================
// types/enrollment.ts
// ============================================================
import type { Course } from "./course";

export type EnrollmentStatus = "active" | "completed" | "cancelled";

export interface Enrollment {
  id: string;
  student: string;
  course: string;
  course_detail: Course;
  enrollment_status: EnrollmentStatus;
  is_active: boolean;
  progress_percentage: string;
  completed_lessons_count: number;
  total_lessons_count: number;
  enrolled_at: string;
  completed_at: string | null;
  last_accessed_at: string | null;
  created_at: string;
}

export interface LessonProgress {
  id: string;
  lesson_id: string;
  lesson_title: string;
  is_completed: boolean;
  completed_at: string | null;
}
