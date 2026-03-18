// ============================================================
// components/common/StarRating.tsx
// Interactive and display star rating component
// ============================================================
"use client";

import { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  max?: number;
  size?: "sm" | "md" | "lg";
  readOnly?: boolean;
  showValue?: boolean;
  className?: string;
}

const SIZE_MAP = {
  sm: "h-3.5 w-3.5",
  md: "h-5 w-5",
  lg: "h-7 w-7",
};

const TEXT_SIZE_MAP = {
  sm: "text-xs",
  md: "text-sm",
  lg: "text-base",
};

export function StarRating({
  value,
  onChange,
  max = 5,
  size = "md",
  readOnly = false,
  showValue = false,
  className,
}: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  const displayed = hovered > 0 ? hovered : value;

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <div className="flex">
        {Array.from({ length: max }, (_, i) => {
          const starValue = i + 1;
          const isFilled = displayed >= starValue;
          const isHalfFilled = !isFilled && displayed >= starValue - 0.5;

          return (
            <button
              key={i}
              type="button"
              disabled={readOnly}
              onClick={() => onChange?.(starValue)}
              onMouseEnter={() => !readOnly && setHovered(starValue)}
              onMouseLeave={() => !readOnly && setHovered(0)}
              className={cn(
                "transition-transform duration-100",
                !readOnly &&
                  "cursor-pointer hover:scale-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500",
                readOnly && "cursor-default"
              )}
              aria-label={`${starValue} star${starValue !== 1 ? "s" : ""}`}
            >
              <Star
                className={cn(
                  SIZE_MAP[size],
                  "transition-colors duration-100",
                  isFilled
                    ? "fill-amber-400 text-amber-400"
                    : isHalfFilled
                    ? "fill-amber-200 text-amber-400"
                    : "fill-transparent text-slate-300 dark:text-slate-600"
                )}
              />
            </button>
          );
        })}
      </div>

      {showValue && (
        <span
          className={cn(
            "font-semibold text-foreground tabular-nums",
            TEXT_SIZE_MAP[size]
          )}
        >
          {value.toFixed(1)}
        </span>
      )}
    </div>
  );
}

// Display-only compact rating
export function RatingDisplay({
  rating,
  count,
  size = "sm",
}: {
  rating: number | string;
  count?: number;
  size?: "sm" | "md";
}) {
  const ratingNum =
    typeof rating === "string" ? parseFloat(rating) : rating;

  if (ratingNum === 0) return null;

  return (
    <div className="flex items-center gap-1">
      <Star
        className={cn(
          "fill-amber-400 text-amber-400",
          size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4"
        )}
      />
      <span
        className={cn(
          "font-semibold tabular-nums text-foreground",
          size === "sm" ? "text-xs" : "text-sm"
        )}
      >
        {ratingNum.toFixed(1)}
      </span>
      {count !== undefined && count > 0 && (
        <span
          className={cn(
            "text-muted-foreground",
            size === "sm" ? "text-xs" : "text-sm"
          )}
        >
          ({count.toLocaleString()})
        </span>
      )}
    </div>
  );
}
