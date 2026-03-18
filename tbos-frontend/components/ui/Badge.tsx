// ============================================================
// components/ui/Badge.tsx
// ============================================================

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300",
        secondary: "bg-secondary text-secondary-foreground",
        destructive: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
        success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
        warning: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
        outline: "border border-border text-foreground",
        admin: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
        instructor: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
        student: "bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };


// ============================================================
// components/ui/Skeleton.tsx
// ============================================================

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800",
        "after:absolute after:inset-0 after:translate-x-[-100%]",
        "after:bg-gradient-to-r after:from-transparent after:via-white/40 after:to-transparent",
        "after:animate-[shimmer_1.5s_infinite]",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
