// ============================================================
// types/quiz.ts
// ============================================================

export type QuizAttemptStatus = "in_progress" | "submitted" | "expired";

export interface QuizOption {
  id: string;
  option_text: string;
  order: number;
  // is_correct only present in instructor view
  is_correct?: boolean;
}

export interface QuizQuestion {
  id: string;
  question_text: string;
  order: number;
  points: number;
  // explanation only present after attempt
  explanation?: string;
  options: QuizOption[];
}

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
  questions?: QuizQuestion[];
  created_at: string;
  updated_at: string;
}

export interface QuizAttempt {
  id: string;
  quiz: string;
  quiz_title?: string;
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
  status: QuizAttemptStatus;
  answers?: QuizAnswer[];
}

export interface QuizAnswer {
  id: string;
  question: string;
  selected_option: string | null;
  is_correct: boolean;
}

// ============================================================
// types/review.ts
// ============================================================

export interface InstructorResponse {
  id: string;
  instructor_name: string;
  response_text: string;
  created_at: string;
}

export interface Review {
  id: string;
  student: string;
  student_name: string;
  course: string;
  rating: number;
  review_text: string;
  status: "published" | "pending" | "rejected";
  instructor_response: InstructorResponse | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// types/notification.ts
// ============================================================

export type NotificationType =
  | "COURSE_UPDATE"
  | "NEW_LESSON"
  | "QUIZ_AVAILABLE"
  | "ASSIGNMENT_DEADLINE"
  | "CERTIFICATE_ISSUED"
  | "SYSTEM_ALERT";

export interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: NotificationType;
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

// ============================================================
// types/certificate.ts
// ============================================================

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
  issue_date: string | null;
  is_valid: boolean;
}
