// ============================================================
// components/ui/Progress.tsx
// ============================================================

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  indicatorClassName?: string;
  showLabel?: boolean;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, indicatorClassName, showLabel = false, ...props }, ref) => (
  <div className="w-full space-y-1">
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          "h-full w-full flex-1 rounded-full bg-brand-500 transition-all duration-500 ease-out",
          indicatorClassName
        )}
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
    {showLabel && (
      <p className="text-right text-xs font-medium text-muted-foreground">
        {Math.round(value ?? 0)}%
      </p>
    )}
  </div>
));

Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
