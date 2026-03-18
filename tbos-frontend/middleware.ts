// ============================================================
// middleware.ts — Role-based routing + auth guard
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";
import { ACCESS_TOKEN_KEY, ROLE_ROUTES } from "./config/constants";

type UserRole = "admin" | "instructor" | "student";

const PUBLIC_PATHS = new Set([
  "/",
  "/auth/login",
  "/auth/register",
  "/courses",
]);

const ROLE_PREFIXES: Record<string, UserRole> = {
  "/student": "student",
  "/instructor": "instructor",
  "/admin": "admin",
};

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  // Allow /courses/* without auth
  if (pathname.startsWith("/courses/")) return true;
  // Allow static assets
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".") // files like favicon.ico
  )
    return true;
  return false;
}

function getRoleFromPath(pathname: string): UserRole | null {
  for (const [prefix, role] of Object.entries(ROLE_PREFIXES)) {
    if (pathname.startsWith(prefix)) return role;
  }
  return null;
}

async function verifyToken(token: string): Promise<{ role: UserRole } | null> {
  try {
    const secret = new TextEncoder().encode(
      process.env.JWT_SECRET_KEY ?? process.env.NEXTAUTH_SECRET ?? "fallback"
    );
    const { payload } = await jwtVerify(token, secret);
    return payload as { role: UserRole };
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ── Always allow public routes ───────────────────────────
  if (isPublicPath(pathname)) return NextResponse.next();

  // ── Get token from cookies ───────────────────────────────
  const token = request.cookies.get(ACCESS_TOKEN_KEY)?.value;

  // ── No token → redirect to login ────────────────────────
  if (!token) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // ── Verify token (best-effort; real validation is server-side) ──
  // We do a lightweight role check here. The real security lives
  // in the Django backend — this is purely a UX redirect.
  const requiredRole = getRoleFromPath(pathname);

  // For role-protected paths, check the role cookie (set at login)
  if (requiredRole) {
    const roleCookie = request.cookies.get("tbos_role")?.value as
      | UserRole
      | undefined;

    if (roleCookie && roleCookie !== requiredRole) {
      // User is authenticated but wrong role — redirect to their area
      const correctPath =
        ROLE_ROUTES[roleCookie as UserRole] ?? "/auth/login";
      return NextResponse.redirect(new URL(correctPath, request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static (static files)
     * - _next/image (image optimisation)
     * - favicon.ico
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
