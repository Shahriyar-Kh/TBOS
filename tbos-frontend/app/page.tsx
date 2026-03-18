// ============================================================
// app/page.tsx — Public homepage
// ============================================================

import Link from "next/link";
import { ArrowRight, BookOpen, Users, Award, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main className="pt-16">
        {/* Hero */}
        <section className="relative overflow-hidden bg-slate-950 py-24 sm:py-32">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `radial-gradient(circle at 20% 60%, rgba(30,184,229,0.15) 0%, transparent 50%),
                                radial-gradient(circle at 80% 30%, rgba(14,148,194,0.1) 0%, transparent 50%)`,
            }}
          />
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: `linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px),
                                linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)`,
              backgroundSize: "64px 64px",
            }}
          />
          <div className="section-container relative text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5">
              <Zap className="h-3.5 w-3.5 text-brand-400" />
              <span className="text-xs font-semibold text-brand-300">
                Now with AI-powered course creation
              </span>
            </div>
            <h1 className="font-display text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
              Learn Without{" "}
              <span className="text-gradient bg-gradient-to-r from-brand-400 to-brand-300 bg-clip-text text-transparent">
                Limits
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-400">
              Access hundreds of expert-led courses, earn certificates, and build
              the skills that employers actually want — on your schedule.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Button size="xl" asChild>
                <Link href="/courses">
                  Explore courses
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </Button>
              <Button size="xl" variant="outline" className="border-white/20 text-white hover:bg-white/10" asChild>
                <Link href="/auth/register">Start for free</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Social proof */}
        <section className="border-b border-border py-14">
          <div className="section-container">
            <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
              {[
                { value: "50,000+", label: "Active Students", icon: Users },
                { value: "200+", label: "Expert Courses", icon: BookOpen },
                { value: "98%", label: "Satisfaction Rate", icon: Award },
                { value: "150+", label: "Instructors", icon: Zap },
              ].map(({ value, label, icon: Icon }) => (
                <div key={label} className="flex flex-col items-center gap-2 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950/30">
                    <Icon className="h-6 w-6 text-brand-500" />
                  </div>
                  <p className="font-display text-3xl font-bold text-foreground">{value}</p>
                  <p className="text-sm text-muted-foreground">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 bg-brand-50 dark:bg-brand-950/20">
          <div className="section-container text-center">
            <h2 className="font-display text-3xl font-bold">Ready to start learning?</h2>
            <p className="mt-4 text-muted-foreground">
              Join thousands of learners advancing their careers with TechBuilt Open School.
            </p>
            <Button size="lg" className="mt-8" asChild>
              <Link href="/auth/register">
                Get started free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
