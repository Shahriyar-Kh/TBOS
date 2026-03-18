// ============================================================
// components/common/CourseCard.tsx
// ============================================================

import Link from "next/link";
import Image from "next/image";
import { Star, Clock, Users, BookOpen, Award } from "lucide-react";
import { cn, formatCurrency, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { Course } from "@/types/course";

interface CourseCardProps {
  course: Course;
  className?: string;
  showInstructor?: boolean;
  compact?: boolean;
}

export function CourseCard({
  course,
  className,
  showInstructor = true,
  compact = false,
}: CourseCardProps) {
  const effectivePrice = parseFloat(course.effective_price ?? course.price);
  const isFree = course.is_free || effectivePrice === 0;
  const hasDiscount =
    !isFree &&
    course.discount_price &&
    parseFloat(course.discount_price) > 0 &&
    parseFloat(course.discount_price) < parseFloat(course.price);

  return (
    <article
      className={cn(
        "group relative flex flex-col rounded-2xl border border-border bg-card overflow-hidden",
        "transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:border-brand-200 dark:hover:border-brand-800",
        className
      )}
    >
      {/* ── Thumbnail ─── */}
      <Link href={`/courses/${course.slug}`} className="block">
        <div className="relative aspect-video w-full overflow-hidden bg-slate-100 dark:bg-slate-800">
          {course.thumbnail ? (
            <Image
              src={course.thumbnail}
              alt={course.title}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <BookOpen className="h-10 w-10 text-slate-300" />
            </div>
          )}

          {/* Overlay badges */}
          <div className="absolute left-3 top-3 flex gap-1.5">
            {isFree && (
              <Badge variant="success" className="shadow-sm">
                Free
              </Badge>
            )}
            {course.certificate_available && (
              <Badge variant="default" className="shadow-sm gap-1">
                <Award className="h-2.5 w-2.5" />
                Certificate
              </Badge>
            )}
          </div>
        </div>
      </Link>

      {/* ── Body ─── */}
      <div className={cn("flex flex-1 flex-col gap-3 p-4", compact && "p-3")}>
        {/* Category */}
        {course.category && (
          <p className="text-[11px] font-semibold uppercase tracking-widest text-brand-500">
            {course.category.name}
          </p>
        )}

        {/* Title */}
        <Link href={`/courses/${course.slug}`}>
          <h3
            className={cn(
              "font-display font-semibold leading-snug text-foreground",
              "transition-colors group-hover:text-brand-600 dark:group-hover:text-brand-400",
              compact ? "text-sm" : "text-base"
            )}
          >
            {truncate(course.title, compact ? 55 : 70)}
          </h3>
        </Link>

        {/* Instructor */}
        {showInstructor && course.instructor_name && (
          <p className="text-xs text-muted-foreground">
            By{" "}
            <span className="font-medium text-foreground">
              {course.instructor_name}
            </span>
          </p>
        )}

        {/* Stats row */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          {parseFloat(course.average_rating) > 0 && (
            <span className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              <span className="font-semibold text-foreground">
                {parseFloat(course.average_rating).toFixed(1)}
              </span>
              <span>({course.rating_count.toLocaleString()})</span>
            </span>
          )}
          {course.total_enrollments > 0 && (
            <span className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {course.total_enrollments.toLocaleString()}
            </span>
          )}
          {course.duration_hours > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {course.duration_hours}h
            </span>
          )}
          {course.total_lessons > 0 && (
            <span className="flex items-center gap-1">
              <BookOpen className="h-3.5 w-3.5" />
              {course.total_lessons} lessons
            </span>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Price row */}
        <div className="flex items-center justify-between gap-2 pt-1 border-t border-border">
          <div className="flex items-baseline gap-2">
            {isFree ? (
              <span className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                Free
              </span>
            ) : (
              <>
                <span className="text-base font-bold text-foreground">
                  {formatCurrency(effectivePrice)}
                </span>
                {hasDiscount && (
                  <span className="text-xs text-muted-foreground line-through">
                    {formatCurrency(course.price)}
                  </span>
                )}
              </>
            )}
          </div>
          <Button size="sm" variant="brand-outline" asChild>
            <Link href={`/courses/${course.slug}`}>View</Link>
          </Button>
        </div>
      </div>
    </article>
  );
}
