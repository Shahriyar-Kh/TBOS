// ============================================================
// app/auth/register/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  ArrowRight,
  GraduationCap,
  BookOpen,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import { useRegister } from "@/hooks/useAuth";

// ── Schema ────────────────────────────────────────────────────
const registerSchema = z
  .object({
    first_name: z.string().min(2, "First name must be at least 2 characters"),
    last_name: z.string().min(2, "Last name must be at least 2 characters"),
    email: z.string().min(1, "Email is required").email("Invalid email"),
    username: z.string().optional(),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[0-9]/, "Must contain at least one number"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    role: z.enum(["student", "instructor"]).default("student"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { mutate: register, isPending } = useRegister();

  const {
    register: formRegister,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "student" },
  });

  const selectedRole = watch("role");

  const onSubmit = (data: RegisterFormData) => {
    register(data);
  };

  return (
    <div className="space-y-7 animate-fade-in">
      {/* Heading */}
      <div className="space-y-2">
        <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
          Create your account
        </h1>
        <p className="text-sm text-muted-foreground">
          Join thousands of learners on TechBuilt Open School
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Role selector */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">I am a…</p>
          <div className="grid grid-cols-2 gap-3">
            {(["student", "instructor"] as const).map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => setValue("role", role)}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-center transition-all",
                  selectedRole === role
                    ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950/30 dark:text-brand-300"
                    : "border-border text-muted-foreground hover:border-slate-300"
                )}
              >
                {role === "student" ? (
                  <GraduationCap className="h-5 w-5" />
                ) : (
                  <BookOpen className="h-5 w-5" />
                )}
                <span className="text-sm font-semibold capitalize">{role}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Name row */}
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="First name"
            placeholder="John"
            autoComplete="given-name"
            leftIcon={<User className="h-4 w-4" />}
            error={errors.first_name?.message}
            {...formRegister("first_name")}
          />
          <Input
            label="Last name"
            placeholder="Doe"
            autoComplete="family-name"
            error={errors.last_name?.message}
            {...formRegister("last_name")}
          />
        </div>

        {/* Email */}
        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          leftIcon={<Mail className="h-4 w-4" />}
          error={errors.email?.message}
          {...formRegister("email")}
        />

        {/* Username (optional) */}
        <Input
          label="Username (optional)"
          placeholder="johndoe"
          autoComplete="username"
          hint="Unique identifier for your public profile"
          error={errors.username?.message}
          {...formRegister("username")}
        />

        {/* Password */}
        <Input
          label="Password"
          type={showPassword ? "text" : "password"}
          placeholder="Min. 8 characters"
          autoComplete="new-password"
          leftIcon={<Lock className="h-4 w-4" />}
          rightIcon={
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setShowPassword((v) => !v)}
              className="text-slate-400 hover:text-foreground transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          }
          error={errors.password?.message}
          hint="At least 8 characters with one uppercase and one number"
          {...formRegister("password")}
        />

        {/* Confirm password */}
        <Input
          label="Confirm password"
          type="password"
          placeholder="Re-enter your password"
          autoComplete="new-password"
          leftIcon={<Lock className="h-4 w-4" />}
          error={errors.confirm_password?.message}
          {...formRegister("confirm_password")}
        />

        <Button
          type="submit"
          className="w-full"
          size="lg"
          isLoading={isPending}
          loadingText="Creating account…"
        >
          Create account
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>

      {/* Terms */}
      <p className="text-center text-xs text-muted-foreground">
        By creating an account, you agree to our{" "}
        <Link href="/terms" className="text-brand-500 hover:underline">
          Terms of Service
        </Link>{" "}
        and{" "}
        <Link href="/privacy" className="text-brand-500 hover:underline">
          Privacy Policy
        </Link>
      </p>

      {/* Footer */}
      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/auth/login"
          className="font-semibold text-brand-500 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
