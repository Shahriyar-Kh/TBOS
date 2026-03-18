"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpenText, Menu } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DASHBOARD_BY_ROLE } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

export function Navbar() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const role = useAuthStore((state) => state.role);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border/50 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link className="inline-flex items-center gap-2 font-semibold tracking-tight" href="/">
          <BookOpenText className="h-5 w-5 text-primary" />
          TBOS
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium md:flex">
          <Link className="text-muted-foreground transition hover:text-foreground" href="/">
            Home
          </Link>
          <Link className="text-muted-foreground transition hover:text-foreground" href="/student">
            Student
          </Link>
          <Link className="text-muted-foreground transition hover:text-foreground" href="/instructor">
            Instructor
          </Link>
          <Link className="text-muted-foreground transition hover:text-foreground" href="/admin">
            Admin
          </Link>
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {!user ? (
            <>
              <Link href="/login" className={cn(buttonVariants({ variant: "ghost" }))}>
                Login
              </Link>
              <Link href="/register" className={cn(buttonVariants())}>
                Register
              </Link>
            </>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger className={cn(buttonVariants({ variant: "outline" }))}>
                {user.full_name}
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>{user.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {role && (
                  <DropdownMenuItem onClick={() => router.push(DASHBOARD_BY_ROLE[role])}>Dashboard</DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger className={cn(buttonVariants({ variant: "outline", size: "icon" }), "md:hidden")}>
            <Menu className="h-5 w-5" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem onClick={() => router.push("/")}>Home</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/student")}>Student</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/instructor")}>Instructor</DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/admin")}>Admin</DropdownMenuItem>
            <DropdownMenuSeparator />
            {!user ? (
              <>
                <DropdownMenuItem onClick={() => router.push("/login")}>Login</DropdownMenuItem>
                <DropdownMenuItem onClick={() => router.push("/register")}>Register</DropdownMenuItem>
              </>
            ) : (
              <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
