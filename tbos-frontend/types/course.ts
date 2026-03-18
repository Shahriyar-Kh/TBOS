// ============================================================
// types/course.ts
// ============================================================

export type CourseStatus = "draft" | "published" | "archived";

export interface Category {
  id: string;
  name: string;
  icon: string;
  slug: string;
}

export interface Level {
  id: string;
  name: string;
}

export interface Language {
  id: string;
  name: string;
}

export interface LearningOutcome {
  id: string;
  text: string;
  order: number;
}

export interface Requirement {
  id: string;
  text: string;
  order: number;
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  subtitle: string;
  description: string;
  thumbnail: string;
  featured_image: string;
  promo_video_url: string;
  price: string;
  discount_price: string;
  discount: string;
  effective_price: string;
  is_free: boolean;
  status: CourseStatus;
  certificate_available: boolean;
  category: Category | null;
  level: Level | null;
  language: Language | null;
  instructor_name: string;
  instructor_id?: string;
  average_rating: string;
  rating_count: number;
  total_enrollments: number;
  duration_hours: number;
  total_lessons: number;
  learning_outcomes?: LearningOutcome[];
  requirements?: Requirement[];
  published_at: string | null;
  created_at: string;
  updated_at?: string;
}

export interface CourseCreatePayload {
  title: string;
  subtitle?: string;
  description: string;
  thumbnail?: string;
  promo_video_url?: string;
  price?: number;
  discount_price?: number;
  is_free?: boolean;
  certificate_available?: boolean;
  category_id: string;
  level_id?: string;
  language_id?: string;
}
