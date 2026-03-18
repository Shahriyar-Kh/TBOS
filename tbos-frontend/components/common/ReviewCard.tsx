// ============================================================
// components/common/ReviewCard.tsx
// ============================================================

import { Star } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { toInitials, formatDate, cn } from "@/lib/utils";
import type { Review } from "@/services/reviewService";

interface ReviewCardProps {
  review: Review;
  className?: string;
}

export function ReviewCard({ review, className }: ReviewCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-card p-5 space-y-3",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <Avatar className="h-9 w-9">
            <AvatarFallback className="bg-slate-100 text-slate-600 text-xs font-semibold">
              {toInitials(review.student_name)}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="text-sm font-semibold text-foreground">
              {review.student_name}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatDate(review.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-0.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={cn(
                "h-4 w-4",
                i < review.rating
                  ? "fill-amber-400 text-amber-400"
                  : "fill-slate-200 text-slate-200"
              )}
            />
          ))}
        </div>
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">
        {review.review_text}
      </p>

      {review.instructor_response && (
        <div className="rounded-xl bg-brand-50 p-4 dark:bg-brand-950/20 space-y-2">
          <p className="text-xs font-semibold text-brand-700 dark:text-brand-300">
            Instructor response — {review.instructor_response.instructor_name}
          </p>
          <p className="text-sm text-muted-foreground">
            {review.instructor_response.response_text}
          </p>
        </div>
      )}
    </div>
  );
}
