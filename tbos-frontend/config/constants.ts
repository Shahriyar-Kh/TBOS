// ============================================================
// config/constants.ts
// ============================================================

export const ACCESS_TOKEN_KEY = "tbos_access";
export const REFRESH_TOKEN_KEY = "tbos_refresh";
export const USER_ROLE_KEY = "tbos_role";

/** 15 minutes in ms — used to compute expiry buffer */
export const TOKEN_EXPIRY_BUFFER_MS = 15 * 60 * 1000;

export const ROLE_ROUTES = {
  student: "/student/dashboard",
  instructor: "/instructor/dashboard",
  admin: "/admin/dashboard",
} as const;

export const PUBLIC_ROUTES = [
  "/",
  "/auth/login",
  "/auth/register",
  "/courses",
];

export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "TechBuilt Open School";

export const QUERY_KEYS = {
  auth: {
    me: ["auth", "me"],
    profile: ["auth", "profile"],
  },
  courses: {
    list: (params?: object) => ["courses", "list", params],
    detail: (slug: string) => ["courses", "detail", slug],
    curriculum: (slug: string) => ["courses", "curriculum", slug],
    instructorList: ["courses", "instructor"],
  },
  enrollments: {
    list: ["enrollments", "list"],
    detail: (id: string) => ["enrollments", "detail", id],
  },
  analytics: {
    student: ["analytics", "student"],
    instructor: ["analytics", "instructor"],
    admin: (params?: object) => ["analytics", "admin", params],
  },
  notifications: {
    list: (isRead?: boolean) => ["notifications", "list", isRead],
  },
} as const;
