// ============================================================
// components/ui/Input.tsx
// ============================================================

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  containerClassName?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      containerClassName,
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      type = "text",
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id ?? React.useId();

    return (
      <div className={cn("flex flex-col gap-1.5", containerClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-foreground"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <span className="absolute left-3 flex items-center text-muted-foreground">
              {leftIcon}
            </span>
          )}

          <input
            type={type}
            id={inputId}
            ref={ref}
            className={cn(
              "flex h-10 w-full rounded-xl border border-input bg-background px-3.5 py-2",
              "text-sm text-foreground placeholder:text-muted-foreground",
              "transition-colors duration-150",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
              "disabled:cursor-not-allowed disabled:opacity-50",
              leftIcon && "pl-9",
              rightIcon && "pr-9",
              error &&
                "border-destructive focus:ring-destructive/50",
              className
            )}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined
            }
            {...props}
          />

          {rightIcon && (
            <span className="absolute right-3 flex items-center text-muted-foreground">
              {rightIcon}
            </span>
          )}
        </div>

        {error && (
          <p
            id={`${inputId}-error`}
            className="flex items-center gap-1.5 text-xs text-destructive"
            role="alert"
          >
            <svg
              className="h-3.5 w-3.5 shrink-0"
              viewBox="0 0 16 16"
              fill="currentColor"
            >
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm-.75 4.25a.75.75 0 011.5 0v3.5a.75.75 0 01-1.5 0v-3.5zm.75 6.5a.875.875 0 110-1.75.875.875 0 010 1.75z" />
            </svg>
            {error}
          </p>
        )}

        {hint && !error && (
          <p
            id={`${inputId}-hint`}
            className="text-xs text-muted-foreground"
          >
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
