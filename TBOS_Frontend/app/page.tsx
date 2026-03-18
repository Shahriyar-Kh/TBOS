import Link from "next/link";
import { ArrowRight, BookOpen, GraduationCap, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <section className="space-y-8">
      <div className="grid gap-8 rounded-3xl border border-border/50 bg-card/60 p-8 shadow-sm backdrop-blur md:grid-cols-2 md:p-12">
        <div className="space-y-6">
          <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
            TechBuilt Open School
          </span>
          <h1 className="text-4xl font-bold tracking-tight text-balance sm:text-5xl">
            Build your future with a modern LMS experience.
          </h1>
          <p className="max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
            TBOS delivers role-based learning workflows for students, instructors, and administrators with a scalable API-first architecture.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg bg-primary px-2.5 text-sm font-medium text-primary-foreground transition hover:bg-primary/80"
            >
              Start Learning
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/register"
              className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-background px-2.5 text-sm font-medium text-foreground transition hover:bg-muted"
            >
              Create Account
            </Link>
          </div>
        </div>
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookOpen className="h-5 w-5 text-primary" />
                Structured Courses
              </CardTitle>
              <CardDescription>
                Modular lessons, analytics, and progress tracking for every learner.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <GraduationCap className="h-5 w-5 text-primary" />
                Instructor Workflows
              </CardTitle>
              <CardDescription>
                Create courses, manage students, and monitor engagement in real time.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ShieldCheck className="h-5 w-5 text-primary" />
                Admin Controls
              </CardTitle>
              <CardDescription>
                Centralized governance for users, payments, and platform operations.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <Link className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline" href="/admin">
                View admin dashboard
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
