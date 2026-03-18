import { NextRequest, NextResponse } from "next/server";
import { ACCESS_TOKEN_COOKIE, USER_ROLE_COOKIE } from "@/lib/constants";
import type { UserRole } from "@/types/auth";

const ROLE_REDIRECTS: Record<UserRole, string> = {
  student: "/student",
  instructor: "/instructor",
  admin: "/admin",
};

function isProtectedPath(pathname: string) {
  return pathname.startsWith("/student") || pathname.startsWith("/instructor") || pathname.startsWith("/admin");
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;
  const role = request.cookies.get(USER_ROLE_COOKIE)?.value as UserRole | undefined;

  if (pathname === "/" && token && role) {
    return NextResponse.redirect(new URL(ROLE_REDIRECTS[role], request.url));
  }

  if (pathname === "/login" || pathname === "/register") {
    if (token && role) {
      return NextResponse.redirect(new URL(ROLE_REDIRECTS[role], request.url));
    }
    return NextResponse.next();
  }

  if (isProtectedPath(pathname)) {
    if (!token || !role) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    if (pathname.startsWith("/student") && role !== "student") {
      return NextResponse.redirect(new URL(ROLE_REDIRECTS[role], request.url));
    }

    if (pathname.startsWith("/instructor") && role !== "instructor") {
      return NextResponse.redirect(new URL(ROLE_REDIRECTS[role], request.url));
    }

    if (pathname.startsWith("/admin") && role !== "admin") {
      return NextResponse.redirect(new URL(ROLE_REDIRECTS[role], request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/login", "/register", "/student/:path*", "/instructor/:path*", "/admin/:path*"],
};
