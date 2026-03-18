// ============================================================
// app/courses/[slug]/page.tsx — Public course detail page
// ============================================================
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  Star, Clock, Users, BookOpen, Award, ChevronDown, ChevronUp,
  Play, Lock, CheckCircle, Globe, BarChart3, ArrowRight, ShoppingCart,
} from "lucide-react";

import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { ReviewCard } from "@/components/common/ReviewCard";
import { CheckoutModal } from "@/components/common/CheckoutModal";
import { useCourseDetail, useCourseCurriculum } from "@/hooks/useCourses";
import { useEnrollCourse } from "@/hooks/useEnrollments";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency, cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import ReviewService from "@/services/reviewService";

export default function CourseDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();

  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const { data: course, isLoading: courseLoading } = useCourseDetail(slug);
  const { data: curriculum } = useCourseCurriculum(slug);
  const { mutate: enroll, isPending: enrolling } = useEnrollCourse();

  const { data: reviews } = useQuery({
    queryKey: ["reviews", slug],
    queryFn: () => course ? ReviewService.getCourseReviews(course.id) : null,
    enabled: !!course,
  });

  const toggleSection = (id: string) =>
    setExpandedSections((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  if (courseLoading) return <CourseDetailSkeleton />;
  if (!course) return null;

  const effectivePrice = parseFloat(course.effective_price ?? course.price);
  const isFree = course.is_free || effectivePrice === 0;
  const hasDiscount =
    !isFree &&
    course.discount_price &&
    parseFloat(course.discount_price) < parseFloat(course.price);

  const handleEnrollOrBuy = () => {
    if (!isAuthenticated) {
      router.push(`/auth/login?redirect=/courses/${slug}`);
      return;
    }
    if (isFree) {
      enroll(course.id);
    } else {
      setCheckoutOpen(true);
    }
  };

  const totalLessons = curriculum?.sections?.reduce(
    (acc: number, s: { lessons: unknown[] }) => acc + (s.lessons?.length ?? 0),
    0
  ) ?? course.total_lessons;

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-16">
        {/* ── Hero Banner ─── */}
        <div className="bg-slate-900 text-white">
          <div className="section-container grid gap-8 py-12 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              {course.category && (
                <Badge variant="default" className="bg-brand-500/20 text-brand-300 border-brand-500/30">
                  {course.category.name}
                </Badge>
              )}
              <h1 className="font-display text-3xl font-bold leading-tight lg:text-4xl">
                {course.title}
              </h1>
              {course.subtitle && (
                <p className="text-lg text-slate-300">{course.subtitle}</p>
              )}

              {/* Meta row */}
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                {parseFloat(course.average_rating) > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    <span className="font-bold text-amber-400">
                      {parseFloat(course.average_rating).toFixed(1)}
                    </span>
                    <span>({course.rating_count.toLocaleString()} ratings)</span>
                  </span>
                )}
                <span className="flex items-center gap-1.5">
                  <Users className="h-4 w-4" />
                  {course.total_enrollments.toLocaleString()} students
                </span>
                {course.duration_hours > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-4 w-4" />
                    {course.duration_hours} hours total
                  </span>
                )}
                {course.language && (
                  <span className="flex items-center gap-1.5">
                    <Globe className="h-4 w-4" />
                    {course.language.name}
                  </span>
                )}
              </div>

              <p className="text-sm text-slate-400">
                Created by{" "}
                <span className="font-semibold text-brand-300">
                  {course.instructor_name}
                </span>
              </p>
            </div>

            {/* ── Sticky Purchase Card (desktop) ─── */}
            <div className="hidden lg:block">
              <PurchaseCard
                course={course}
                isFree={isFree}
                effectivePrice={effectivePrice}
                hasDiscount={!!hasDiscount}
                onEnrollOrBuy={handleEnrollOrBuy}
                enrolling={enrolling}
              />
            </div>
          </div>
        </div>

        {/* ── Mobile Purchase Bar ─── */}
        <div className="sticky top-16 z-20 border-b border-border bg-white px-4 py-3 shadow-sm dark:bg-slate-900 lg:hidden">
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="text-xl font-bold">
                {isFree ? "Free" : formatCurrency(effectivePrice)}
              </span>
              {hasDiscount && (
                <span className="ml-2 text-sm text-muted-foreground line-through">
                  {formatCurrency(course.price)}
                </span>
              )}
            </div>
            <Button
              onClick={handleEnrollOrBuy}
              isLoading={enrolling}
              size="sm"
              className="shrink-0"
            >
              {isFree ? "Enroll free" : "Buy now"}
            </Button>
          </div>
        </div>

        {/* ── Body ─── */}
        <div className="section-container grid gap-10 py-12 lg:grid-cols-3">
          <div className="space-y-10 lg:col-span-2">
            {/* What you'll learn */}
            {course.learning_outcomes && course.learning_outcomes.length > 0 && (
              <section>
                <h2 className="mb-4 font-display text-xl font-bold">
                  What you&apos;ll learn
                </h2>
                <div className="grid grid-cols-1 gap-2 rounded-2xl border border-border bg-card p-6 sm:grid-cols-2">
                  {course.learning_outcomes.map((outcome) => (
                    <div key={outcome.id} className="flex items-start gap-2.5">
                      <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
                      <span className="text-sm">{outcome.text}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Course curriculum */}
            {curriculum?.sections && curriculum.sections.length > 0 && (
              <section>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-display text-xl font-bold">Curriculum</h2>
                  <span className="text-sm text-muted-foreground">
                    {curriculum.sections.length} sections · {totalLessons} lessons
                  </span>
                </div>
                <div className="space-y-2">
                  {curriculum.sections.map(
                    (section: {
                      id: string;
                      title: string;
                      description: string;
                      order: number;
                      lessons: Array<{
                        id: string;
                        title: string;
                        lesson_type: string;
                        duration_seconds: number;
                        is_preview: boolean;
                      }>;
                    }) => {
                      const isOpen = expandedSections.has(section.id);
                      return (
                        <div
                          key={section.id}
                          className="rounded-xl border border-border overflow-hidden"
                        >
                          <button
                            onClick={() => toggleSection(section.id)}
                            className="flex w-full items-center justify-between bg-slate-50 px-5 py-4 text-left transition-colors hover:bg-slate-100 dark:bg-slate-800/50 dark:hover:bg-slate-800"
                          >
                            <div className="flex items-center gap-3">
                              {isOpen ? (
                                <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
                              ) : (
                                <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                              )}
                              <span className="font-semibold">{section.title}</span>
                            </div>
                            <span className="shrink-0 text-xs text-muted-foreground">
                              {section.lessons?.length ?? 0} lessons
                            </span>
                          </button>
                          {isOpen && section.lessons && (
                            <ul className="divide-y divide-border">
                              {section.lessons.map((lesson) => (
                                <li
                                  key={lesson.id}
                                  className="flex items-center justify-between gap-3 px-5 py-3"
                                >
                                  <div className="flex items-center gap-2.5">
                                    {lesson.is_preview ? (
                                      <Play className="h-3.5 w-3.5 shrink-0 text-brand-500" />
                                    ) : (
                                      <Lock className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                                    )}
                                    <span
                                      className={cn(
                                        "text-sm",
                                        lesson.is_preview
                                          ? "text-foreground"
                                          : "text-muted-foreground"
                                      )}
                                    >
                                      {lesson.title}
                                    </span>
                                    {lesson.is_preview && (
                                      <Badge
                                        variant="default"
                                        className="text-[10px]"
                                      >
                                        Preview
                                      </Badge>
                                    )}
                                  </div>
                                  {lesson.duration_seconds > 0 && (
                                    <span className="shrink-0 text-xs text-muted-foreground">
                                      {Math.floor(lesson.duration_seconds / 60)}m
                                    </span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      );
                    }
                  )}
                </div>
              </section>
            )}

            {/* Description */}
            <section>
              <h2 className="mb-4 font-display text-xl font-bold">
                About this course
              </h2>
              <div className="prose prose-slate max-w-none dark:prose-invert">
                <p className="leading-relaxed text-muted-foreground">
                  {course.description}
                </p>
              </div>
            </section>

            {/* Requirements */}
            {course.requirements && course.requirements.length > 0 && (
              <section>
                <h2 className="mb-4 font-display text-xl font-bold">
                  Requirements
                </h2>
                <ul className="space-y-2">
                  {course.requirements.map((req) => (
                    <li key={req.id} className="flex items-start gap-2.5 text-sm">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                      {req.text}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Reviews */}
            {reviews && reviews.results.length > 0 && (
              <section>
                <div className="mb-6 flex items-center gap-3">
                  <h2 className="font-display text-xl font-bold">
                    Student Reviews
                  </h2>
                  <Badge variant="secondary">
                    {reviews.count} reviews
                  </Badge>
                </div>
                <div className="space-y-4">
                  {reviews.results.slice(0, 5).map((review) => (
                    <ReviewCard key={review.id} review={review} />
                  ))}
                </div>
              </section>
            )}
          </div>

          {/* ── Desktop sidebar purchase card (already in hero) ─── */}
          <div className="hidden lg:block" />
        </div>
      </main>
      <Footer />

      {/* Checkout modal */}
      {checkoutOpen && course && (
        <CheckoutModal
          course={course}
          open={checkoutOpen}
          onClose={() => setCheckoutOpen(false)}
        />
      )}
    </>
  );
}

// ── Purchase Card ─────────────────────────────────────────────
function PurchaseCard({
  course,
  isFree,
  effectivePrice,
  hasDiscount,
  onEnrollOrBuy,
  enrolling,
}: {
  course: ReturnType<typeof useCourseDetail>["data"];
  isFree: boolean;
  effectivePrice: number;
  hasDiscount: boolean;
  onEnrollOrBuy: () => void;
  enrolling: boolean;
}) {
  if (!course) return null;
  return (
    <div className="sticky top-24">
      <Card className="overflow-hidden shadow-xl">
        {course.thumbnail && (
          <div className="relative aspect-video w-full">
            <Image
              src={course.thumbnail}
              alt={course.title}
              fill
              className="object-cover"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/90 shadow-lg">
                <Play className="h-6 w-6 text-slate-900 fill-slate-900 ml-0.5" />
              </div>
            </div>
          </div>
        )}
        <CardContent className="p-6 space-y-5">
          {/* Price */}
          <div className="flex items-baseline gap-3">
            <span className="font-display text-3xl font-bold">
              {isFree ? "Free" : formatCurrency(effectivePrice)}
            </span>
            {hasDiscount && (
              <span className="text-base text-muted-foreground line-through">
                {formatCurrency(course.price)}
              </span>
            )}
          </div>

          <Button
            className="w-full"
            size="lg"
            onClick={onEnrollOrBuy}
            isLoading={enrolling}
            loadingText={isFree ? "Enrolling…" : "Processing…"}
          >
            {isFree ? (
              <>Enroll for free</>
            ) : (
              <>
                <ShoppingCart className="h-4 w-4" />
                Buy now
              </>
            )}
          </Button>
          {!isFree && (
            <p className="text-center text-xs text-muted-foreground">
              30-day money-back guarantee
            </p>
          )}

          {/* Course includes */}
          <div className="space-y-2 pt-2 border-t border-border">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              This course includes
            </p>
            <ul className="space-y-2">
              {[
                { icon: Clock, label: `${course.duration_hours}h of on-demand content` },
                { icon: BookOpen, label: `${course.total_lessons} lessons` },
                { icon: BarChart3, label: `${course.level?.name ?? "All levels"}` },
                course.certificate_available && { icon: Award, label: "Certificate of completion" },
              ]
                .filter(Boolean)
                .map((item) => {
                  if (!item) return null;
                  const { icon: Icon, label } = item as { icon: typeof Clock; label: string };
                  return (
                    <li key={label} className="flex items-center gap-2.5 text-sm">
                      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                      {label}
                    </li>
                  );
                })}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Skeleton ──────────────────────────────────────────────────
function CourseDetailSkeleton() {
  return (
    <>
      <Navbar />
      <div className="pt-16">
        <div className="bg-slate-900 py-12">
          <div className="section-container">
            <Skeleton className="h-5 w-24 bg-slate-700" />
            <Skeleton className="mt-4 h-10 w-3/4 bg-slate-700" />
            <Skeleton className="mt-3 h-5 w-1/2 bg-slate-700" />
            <div className="mt-4 flex gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-4 w-24 bg-slate-700" />
              ))}
            </div>
          </div>
        </div>
        <div className="section-container py-12">
          <div className="grid gap-10 lg:grid-cols-3">
            <div className="space-y-8 lg:col-span-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="h-6 w-40" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
