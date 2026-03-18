// ============================================================
// types/api.ts — Generic API response shapes
// ============================================================

export interface ApiSuccess<T = unknown> {
  success: true;
  message: string;
  data: T;
}

export interface ApiError {
  success: false;
  message: string;
  errors: Record<string, string | string[]> | null;
}

export type ApiResponse<T = unknown> = ApiSuccess<T> | ApiError;

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiRequestConfig {
  showErrorToast?: boolean;
  showSuccessToast?: boolean;
}
