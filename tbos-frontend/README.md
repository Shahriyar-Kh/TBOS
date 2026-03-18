# TechBuilt Open School — Frontend

> **Production-ready Next.js 14 LMS frontend** built with TypeScript, TailwindCSS, React Query, and Zustand. Fully integrated with the TBOS Django REST API backend.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Pages & Routes](#pages--routes)
- [Architecture](#architecture)
  - [API Layer](#api-layer)
  - [Authentication Flow](#authentication-flow)
  - [State Management](#state-management)
  - [Role-Based Routing](#role-based-routing)
  - [Real-Time Analytics](#real-time-analytics)
- [Components](#components)
- [Services](#services)
- [Hooks](#hooks)
- [Design System](#design-system)
- [File Extension Guide](#file-extension-guide)
- [Scripts](#scripts)
- [Deployment](#deployment)

---

## Overview

TBOS Frontend is a full-featured Learning Management System interface supporting three distinct roles:

| Role | Access |
|---|---|
| **Student** | Browse courses, enroll, learn, take quizzes, submit assignments, view certificates |
| **Instructor** | Create and manage courses, track student progress, view analytics |
| **Admin** | Manage all users, courses, payments, and platform-wide analytics |

---

## Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| **Framework** | Next.js 14 (App Router) | SSR, routing, layouts |
| **Language** | TypeScript (strict) | Type safety throughout |
| **Styling** | TailwindCSS + ShadCN UI | Utility-first design system |
| **Data Fetching** | TanStack React Query v5 | Server state, caching, mutations |
| **Global State** | Zustand | Auth store (client-only) |
| **HTTP Client** | Axios | API calls with JWT interceptors |
| **Forms** | React Hook Form + Zod | Validated, typed forms |
| **Notifications** | Sonner | Toast notifications |
| **UI Primitives** | Radix UI | Accessible headless components |
| **Icons** | Lucide React | Consistent icon set |
| **Fonts** | Syne · DM Sans · JetBrains Mono | Display, body, code |
| **Themes** | next-themes | Light / dark mode |
| **WebSocket** | Native WS + custom manager | Real-time analytics |

---

## Project Structure

```
tbos-frontend/
│
├── app/                            # Next.js App Router
│   ├── layout.tsx                  # Root layout (fonts, providers)
│   ├── page.tsx                    # Public homepage
│   ├── loading.tsx                 # Global loading UI
│   ├── error.tsx                   # Global error boundary
│   ├── not-found.tsx               # 404 page
│   ├── globals.css                 # Tailwind + CSS variables
│   │
│   ├── auth/
│   │   ├── layout.tsx              # Split-panel auth layout
│   │   ├── login/page.tsx          # Email + Google OAuth login
│   │   └── register/page.tsx       # Role-aware registration
│   │
│   ├── courses/
│   │   ├── page.tsx                # Public course catalog
│   │   └── [slug]/page.tsx         # Course detail + checkout
│   │
│   ├── certificates/
│   │   └── verify/[code]/page.tsx  # Public certificate verification
│   │
│   ├── payment/
│   │   ├── success/page.tsx        # Post-payment confirmation
│   │   └── failed/page.tsx         # Payment failure page
│   │
│   ├── student/                    # 🎓 Student portal
│   │   ├── layout.tsx              # Sidebar layout (protected)
│   │   ├── dashboard/page.tsx      # Stats, progress, enrolled courses
│   │   ├── courses/page.tsx        # All enrollments with filters
│   │   ├── learn/[id]/page.tsx     # Course player (video/article/quiz)
│   │   ├── quiz/[id]/page.tsx      # Quiz-taking (3-phase flow)
│   │   ├── certificates/page.tsx   # My certificates
│   │   ├── orders/page.tsx         # Purchase history
│   │   ├── notifications/page.tsx  # Notification inbox
│   │   └── settings/page.tsx       # Profile, password, preferences
│   │
│   ├── instructor/                 # 👨‍🏫 Instructor portal
│   │   ├── layout.tsx              # Sidebar layout (protected)
│   │   ├── dashboard/page.tsx      # Revenue, students, ratings
│   │   ├── courses/page.tsx        # Course list with actions
│   │   ├── courses/new/page.tsx    # Create new course
│   │   ├── courses/[id]/page.tsx   # Edit course + publish/archive
│   │   ├── students/page.tsx       # Enrolled students + progress
│   │   ├── analytics/page.tsx      # Performance charts
│   │   ├── notifications/page.tsx  # Notification inbox
│   │   └── settings/page.tsx       # Profile + preferences
│   │
│   └── admin/                      # 🛡️ Admin console
│       ├── layout.tsx              # Sidebar layout (protected)
│       ├── dashboard/page.tsx      # Platform KPIs + insights
│       ├── users/page.tsx          # User management table
│       ├── courses/page.tsx        # All courses management
│       ├── payments/page.tsx       # Payment & refund management
│       ├── analytics/page.tsx      # Revenue + platform metrics
│       ├── notifications/page.tsx  # Broadcast + inbox
│       └── settings/page.tsx       # Profile + preferences
│
├── components/
│   ├── Providers.tsx               # QueryClient + ThemeProvider + Toaster
│   │
│   ├── layout/
│   │   ├── Navbar.tsx              # Responsive navbar (auth-aware)
│   │   └── Footer.tsx              # Site footer
│   │
│   ├── ui/                         # Primitive UI components
│   │   ├── Button.tsx              # 7 variants (default, outline, ghost…)
│   │   ├── Input.tsx               # Labeled input with error & icons
│   │   ├── Textarea.tsx            # Labeled textarea with error
│   │   ├── Select.tsx              # Radix Select wrapper
│   │   ├── Card.tsx                # Card compound component
│   │   ├── Modal.tsx               # Radix Dialog wrapper
│   │   ├── Dropdown.tsx            # Radix DropdownMenu wrapper
│   │   ├── Tabs.tsx                # Radix Tabs wrapper
│   │   ├── Progress.tsx            # Radix Progress bar
│   │   ├── Avatar.tsx              # Radix Avatar with fallback
│   │   ├── Badge.tsx               # Status + role badges
│   │   └── index.ts                # Barrel exports
│   │
│   └── common/                     # Shared feature components
│       ├── CourseCard.tsx          # Course listing card
│       ├── ReviewCard.tsx          # Student review card
│       ├── CheckoutModal.tsx       # Billing form + Stripe checkout
│       ├── NotificationCenter.tsx  # Full notification inbox UI
│       ├── SettingsPanel.tsx       # Shared profile/password/prefs form
│       ├── ConfirmDialog.tsx       # Reusable confirmation modal
│       ├── DataTable.tsx           # Generic paginated data table
│       ├── StarRating.tsx          # Interactive + display star rating
│       ├── PageHeader.tsx          # Consistent page heading component
│       ├── EmptyState.tsx          # Consistent empty content state
│       ├── ErrorBoundary.tsx       # React error boundary + QueryError
│       └── LoadingSpinner.tsx      # Spinner, PageLoader, skeletons
│
├── hooks/
│   ├── useAuth.ts                  # Login, register, logout, profile
│   ├── useCourses.ts               # Course CRUD, publish, archive
│   ├── useEnrollments.ts           # Enroll, progress, lesson completion
│   ├── useAnalytics.ts             # Dashboard data queries
│   ├── useNotifications.ts         # List, mark-read, preferences
│   ├── usePayments.ts              # Checkout, orders, verify
│   └── useRealtimeAnalytics.ts     # WebSocket dashboard updates
│
├── services/                       # Typed API wrappers
│   ├── authService.ts              # /auth/* endpoints
│   ├── courseService.ts            # /courses/* endpoints
│   ├── enrollmentService.ts        # /enrollments/* endpoints
│   ├── analyticsService.ts         # /analytics/* endpoints
│   ├── notificationService.ts      # /notifications/* endpoints
│   ├── paymentService.ts           # /payments/* endpoints
│   ├── quizService.ts              # /quiz/* endpoints
│   ├── reviewService.ts            # /reviews/* endpoints
│   ├── certificateService.ts       # /certificates/* endpoints
│   └── adminService.ts             # /admin/* endpoints
│
├── store/
│   └── authStore.ts                # Zustand auth store (persisted)
│
├── lib/
│   ├── axios.ts                    # Axios instance + JWT interceptors
│   ├── queryClient.ts              # React Query client factory
│   ├── auth.ts                     # Server-side JWT helpers
│   ├── websocket.ts                # Reconnecting WebSocket manager
│   ├── utils.ts                    # cn(), formatCurrency(), truncate()…
│   └── index.ts                    # Barrel exports
│
├── types/
│   ├── auth.ts                     # User, AuthPayload, UserRole
│   ├── api.ts                      # ApiSuccess, ApiError, Paginated
│   ├── course.ts                   # Course, Category, Level, Language
│   ├── enrollment.ts               # Enrollment, LessonProgress
│   ├── quiz.ts                     # Quiz, QuizAttempt, QuizAnswer
│   └── index.ts                    # Barrel re-exports
│
├── config/
│   └── constants.ts                # Token keys, role routes, query keys
│
├── middleware.ts                   # Next.js route protection
├── tailwind.config.ts              # TBOS design tokens
├── next.config.ts                  # Image domains, security headers
├── tsconfig.json                   # TypeScript configuration
├── postcss.config.mjs              # PostCSS config
├── eslint.config.mjs               # ESLint rules
├── package.json                    # Dependencies
├── .env.local                      # Local environment variables
└── .env.local.example              # Environment variable template
```

---

## Getting Started

### Prerequisites

- **Node.js** v18.17+ or v20+
- **npm** v9+ (or pnpm / yarn)
- TBOS Django backend running (see backend README)

### Installation

```bash
# 1. Install dependencies
npm install

# 2. Configure environment variables
cp .env.local.example .env.local
```

Open `.env.local` and fill in your values:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
```

```bash
# 3. Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Django backend base URL (e.g. `http://localhost:8000/api/v1`) |
| `NEXT_PUBLIC_WS_URL` | ✅ | WebSocket server URL (e.g. `ws://localhost:8000`) |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | ✅ | Google OAuth 2.0 Client ID |
| `NEXT_PUBLIC_APP_URL` | ✅ | This app's public URL |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | ✅ | Stripe publishable key |
| `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` | Optional | Cloudinary cloud name for media |

> **Note:** All `NEXT_PUBLIC_` variables are exposed to the browser. Never put secrets in these.

---

## Pages & Routes

### Public Routes (no login required)

| Path | Page |
|---|---|
| `/` | Homepage |
| `/courses` | Course catalog (search, filter, paginate) |
| `/courses/[slug]` | Course detail + enroll / checkout |
| `/certificates/verify/[code]` | Certificate verification |
| `/auth/login` | Login (email + Google OAuth) |
| `/auth/register` | Register (student or instructor) |
| `/payment/success` | Post-payment confirmation |
| `/payment/failed` | Payment failure |

### Student Routes (`/student/*`)

| Path | Page |
|---|---|
| `/student/dashboard` | Learning stats, streak, enrolled courses |
| `/student/courses` | All enrollments with progress bars |
| `/student/learn/[id]` | Course player (video / article / quiz / assignment) |
| `/student/quiz/[id]` | 3-phase quiz (info → taking → results) |
| `/student/certificates` | Earned certificates with download links |
| `/student/orders` | Purchase history |
| `/student/notifications` | Notification inbox |
| `/student/settings` | Profile, password, notification preferences |

### Instructor Routes (`/instructor/*`)

| Path | Page |
|---|---|
| `/instructor/dashboard` | Revenue, students, course stats |
| `/instructor/courses` | My courses list (publish, archive, delete) |
| `/instructor/courses/new` | Create course wizard |
| `/instructor/courses/[id]` | Edit course (title, pricing, media, status) |
| `/instructor/students` | Enrolled students with progress tracking |
| `/instructor/analytics` | KPIs, completion rates, per-course table |
| `/instructor/notifications` | Notification inbox |
| `/instructor/settings` | Profile, password, notification preferences |

### Admin Routes (`/admin/*`)

| Path | Page |
|---|---|
| `/admin/dashboard` | Platform KPIs + popular course insights |
| `/admin/users` | All users (activate/deactivate, filter by role) |
| `/admin/courses` | All courses (publish, delete, status filter) |
| `/admin/payments` | All payments (filter by status, refund) |
| `/admin/analytics` | Date-filtered revenue + platform health |
| `/admin/notifications` | Broadcast notifications + own inbox |
| `/admin/settings` | Profile, password, notification preferences |

---

## Architecture

### API Layer

All API communication flows through a strict 3-layer pattern:

```
Component / Page
      │
      ▼
  Custom Hook  (hooks/*.ts)
  React Query mutation / query
      │
      ▼
  Service      (services/*.ts)
  Typed function calling axios
      │
      ▼
  lib/axios.ts
  Configured Axios instance
      │
      ▼
  Django REST API
  http://localhost:8000/api/v1
```

**Rule:** Components never import from `services/` directly. They always go through a hook.

### Authentication Flow

```
User submits login form
        │
        ▼
useLogin() → POST /api/v1/auth/login/
        │
        ▼
Response: { access_token, refresh_token, user_role, user }
        │
        ▼
setAuth(payload)
  ├── access_token  → cookie (15 min, secure, sameSite: strict)
  ├── refresh_token → cookie (1 day, secure, sameSite: strict)
  └── user object   → Zustand store (persisted to sessionStorage)
        │
        ▼
Redirect to role dashboard:
  student    →  /student/dashboard
  instructor →  /instructor/dashboard
  admin      →  /admin/dashboard
```

**Token Refresh (automatic):**

When any API request returns `401 Unauthorized`, the Axios response interceptor:
1. Pauses all concurrent requests in a queue
2. Silently calls `POST /auth/token/refresh/` with the refresh token
3. Stores the new access token in the cookie
4. Replays all queued requests with the new token
5. If refresh fails → clears all tokens → redirects to `/auth/login`

### State Management

| State type | Tool | Storage |
|---|---|---|
| Authenticated user | Zustand (`authStore`) | sessionStorage (persisted) |
| JWT tokens | js-cookie | Browser cookies |
| Server data | React Query | In-memory cache |
| Form state | React Hook Form | Component local state |
| UI state | React `useState` | Component local state |

### Role-Based Routing

`middleware.ts` runs on every request before the page renders:

```
Request to /student/* or /instructor/* or /admin/*
        │
        ▼
Read access token cookie
        │
   ┌────┴────┐
   │No token │ → Redirect to /auth/login?redirect=<original path>
   └────┬────┘
        │ Token exists
        ▼
Read role cookie set at login
        │
   ┌────┴──────────────────────────┐
   │ Role doesn't match path prefix│ → Redirect to correct dashboard
   └────┬──────────────────────────┘
        │ Role matches
        ▼
   Allow request through
```

> **Important:** Middleware performs a UX redirect only. Real permission enforcement happens on the Django backend via JWT claims.

### Real-Time Analytics

WebSocket connections update dashboard data live without page refresh:

```typescript
// Each role connects to their analytics WS channel
useStudentRealtimeAnalytics()    // → /ws/analytics/dashboard/
useInstructorRealtimeAnalytics() // → /ws/analytics/dashboard/
useAdminRealtimeAnalytics()      // → /ws/analytics/dashboard/
useCourseRealtimeAnalytics(id)   // → /ws/analytics/course/{id}/
```

When the backend publishes an update, the hook calls `queryClient.invalidateQueries()` which triggers a background refetch. The UI updates automatically.

**WebSocket manager features (`lib/websocket.ts`):**
- Automatic reconnect with exponential backoff (max 5 attempts, up to 30s delay)
- Ping/keepalive every 30 seconds
- Auth via `?token=<jwt>` query parameter
- No reconnect on `4401` (unauthenticated) or `4403` (forbidden) close codes
- Singleton per WebSocket path

---

## Components

### UI Primitives (`components/ui/`)

| Component | Description | Key Props |
|---|---|---|
| `Button` | 7 variants: default, outline, ghost, destructive, success, brand-outline, link | `variant`, `size`, `isLoading`, `loadingText`, `asChild` |
| `Input` | Labeled input with left/right icons, error & hint text | `label`, `error`, `hint`, `leftIcon`, `rightIcon` |
| `Textarea` | Labeled textarea with error & hint | `label`, `error`, `hint` |
| `Select` | Radix Select with styled items and label | `label`, `error` |
| `Card` | Compound: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter | — |
| `Modal` | Radix Dialog: Modal, ModalContent, ModalHeader, ModalTitle, ModalFooter | `showCloseButton` |
| `Dropdown` | Radix DropdownMenu with all sub-components | — |
| `Tabs` | Radix Tabs: TabsList, TabsTrigger, TabsContent | — |
| `Progress` | Animated progress bar | `value`, `indicatorClassName`, `showLabel` |
| `Avatar` | Radix Avatar with image + text fallback | — |
| `Badge` | Status badges: default, success, warning, destructive, admin, instructor, student | `variant` |

### Common Components (`components/common/`)

| Component | Description |
|---|---|
| `CourseCard` | Full course card with thumbnail, stats, price, enroll button |
| `ReviewCard` | Student review with star rating and instructor response |
| `CheckoutModal` | Complete billing form + Stripe checkout redirect |
| `NotificationCenter` | Full notification inbox: filter tabs, type icons, mark read/all |
| `SettingsPanel` | Shared settings UI: profile form, password change, notification toggles |
| `ConfirmDialog` | Reusable confirm modal with danger/warning/success variants |
| `DataTable` | Generic paginated table with skeleton loading and empty state |
| `StarRating` | Interactive rating input + read-only display mode |
| `PageHeader` | Consistent page heading with breadcrumb and action slot |
| `EmptyState` | Consistent empty content placeholder with icon and action |
| `ErrorBoundary` | React error boundary + `QueryError` for failed data fetches |
| `LoadingSpinner` | Spinner, `PageLoader`, `CourseCardSkeleton`, `DashboardStatSkeleton` |

---

## Services

Each service file is a plain object with typed async methods. All return typed responses matching the Django API.

| Service | Endpoints covered |
|---|---|
| `authService` | Register, login, Google login, logout, me, profile, update profile, change password |
| `courseService` | Public list, detail, curriculum; instructor CRUD, publish, archive; admin list/delete |
| `enrollmentService` | Enroll free, enroll paid, progress, mark lesson complete, video progress |
| `analyticsService` | Student dashboard, instructor dashboard, admin dashboard, revenue, track activity |
| `quizService` | Student: list, start, answer, submit, results; Instructor: CRUD, questions, options |
| `reviewService` | Public course reviews; student CRUD; instructor respond; admin moderate |
| `notificationService` | List, mark read, mark all read, get/update preferences |
| `paymentService` | Checkout, verify payment, list orders, get order |
| `certificateService` | My certificates, verify by code, download URL |
| `adminService` | Users, instructors, students, activate/deactivate, broadcast notifications, refunds |

---

## Hooks

All hooks wrap React Query and call services. Components only import from hooks.

| Hook file | Exports |
|---|---|
| `useAuth.ts` | `useMe`, `useProfile`, `useLogin`, `useRegister`, `useGoogleLogin`, `useLogout`, `useChangePassword`, `useUpdateProfile` |
| `useCourses.ts` | `usePublicCourses`, `useCourseDetail`, `useCourseCurriculum`, `useInstructorCourses`, `useCreateCourse`, `usePublishCourse`, `useArchiveCourse`, `useDeleteCourse` |
| `useEnrollments.ts` | `useMyEnrollments`, `useEnrollmentProgress`, `useEnrollCourse`, `useMarkLessonComplete`, `useVideoProgress` |
| `useAnalytics.ts` | `useStudentDashboard`, `useInstructorDashboard`, `useAdminDashboard`, `useRevenueAnalytics` |
| `useNotifications.ts` | `useNotifications`, `useMarkNotificationRead`, `useMarkAllRead`, `useNotificationPreferences`, `useUpdateNotificationPreferences` |
| `usePayments.ts` | `useMyOrders`, `useOrder`, `useCheckout`, `useVerifyPayment` |
| `useRealtimeAnalytics.ts` | `useStudentRealtimeAnalytics`, `useInstructorRealtimeAnalytics`, `useAdminRealtimeAnalytics`, `useCourseRealtimeAnalytics` |

---

## Design System

### Colors

```
Brand (Cyan):  brand-50 → brand-950   Primary: #1eb8e5
Slate (Neutral): slate-50 → slate-950
```

### Typography

| Font | Variable | Used for |
|---|---|---|
| **Syne** | `--font-syne` | All headings (`h1`–`h6`, `.font-display`) |
| **DM Sans** | `--font-dm-sans` | Body text, UI labels |
| **JetBrains Mono** | `--font-jetbrains-mono` | Code, order numbers |

### CSS Design Tokens

```css
/* Light mode */
--background: 0 0% 100%
--foreground: 215 28% 9%
--primary: 195 83% 52%       /* brand-500 */
--radius: 0.75rem

/* Dark mode auto-switches */
```

### Utility Classes

```css
.section-container   /* max-w-7xl centered with responsive padding */
.stat-card           /* Dashboard metric card with hover shadow */
.glass-card          /* Frosted glass card */
.text-gradient       /* Brand gradient text */
.shimmer             /* Loading shimmer animation */
```

---

## File Extension Guide

This project correctly uses two TypeScript file extensions:

| Extension | When to use | Examples |
|---|---|---|
| `.tsx` | Any file that contains **JSX** (`<Component />` syntax) | All pages, layouts, all components |
| `.ts` | Pure TypeScript **without JSX** | Services, hooks, utils, types, store, config |

Both are standard TypeScript + Next.js conventions. Next.js handles both automatically.

---

## Scripts

```bash
# Start development server (hot reload)
npm run dev

# Build for production
npm run build

# Start production server (after build)
npm run start

# Run ESLint
npm run lint

# TypeScript type check (no emit)
npm run type-check
```

---

## Deployment

### Vercel (recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# or use vercel env add NEXT_PUBLIC_API_URL
```

### Docker

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Add to `next.config.ts`:
```ts
output: "standalone"
```

### Environment Variables for Production

```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1
NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-production-google-client-id
NEXT_PUBLIC_APP_URL=https://your-frontend.vercel.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
```

---

## Adding New Features

### Adding a new page

1. Create `app/<role>/<page>/page.tsx`
2. Add the route to the sidebar `NAV_ITEMS` in the role's `layout.tsx`
3. Create a service method in `services/` if new API calls are needed
4. Add a query key to `QUERY_KEYS` in `config/constants.ts`
5. Create a custom hook in `hooks/` wrapping the service with React Query

### Adding a new API service

```typescript
// services/myService.ts
import { api } from "@/lib/axios";
import type { ApiSuccess } from "@/types/api";

const MyService = {
  async getItems(): Promise<MyItem[]> {
    const { data } = await api.get<ApiSuccess<MyItem[]>>("/my-endpoint/");
    return data.data;
  },
};

export default MyService;
```

### Adding a new hook

```typescript
// hooks/useMyFeature.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import MyService from "@/services/myService";

export function useMyItems() {
  return useQuery({
    queryKey: ["my-items"],
    queryFn: MyService.getItems,
    staleTime: 2 * 60 * 1000,
  });
}
```

---

## Backend Integration

This frontend connects to the **TBOS Django REST Framework** backend. Ensure the backend is running and has `CORS_ALLOWED_ORIGINS` configured to include your frontend URL.

Key backend endpoints used:

```
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/google-login/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
GET    /api/v1/courses/
GET    /api/v1/courses/{slug}/
GET    /api/v1/courses/{slug}/curriculum/
POST   /api/v1/enrollments/student/enroll/
POST   /api/v1/payments/checkout/
GET    /api/v1/analytics/student/dashboard/
GET    /api/v1/analytics/instructor/dashboard/
GET    /api/v1/analytics/admin/dashboard/
WS     /ws/analytics/dashboard/?token={jwt}
WS     /ws/analytics/course/{id}/?token={jwt}
```

---

## License

© 2026 TechBuilt Open School. All rights reserved.