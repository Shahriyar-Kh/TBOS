// ============================================================
// components/common/ErrorBoundary.tsx + GlobalError + Loading
// ============================================================
"use client";

import React from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

// ── React Error Boundary ──────────────────────────────────────
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <ErrorDisplay
          title="Something went wrong"
          description={this.state.error?.message ?? "An unexpected error occurred."}
          onReset={() => this.setState({ hasError: false, error: null })}
        />
      );
    }
    return this.props.children;
  }
}

// ── Error Display Component ───────────────────────────────────
export function ErrorDisplay({
  title = "Something went wrong",
  description = "An unexpected error occurred. Please try again.",
  onReset,
  showHomeLink = true,
  className,
}: {
  title?: string;
  description?: string;
  onReset?: () => void;
  showHomeLink?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`flex min-h-[400px] flex-col items-center justify-center gap-6 p-8 text-center ${className ?? ""}`}
    >
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/30">
        <AlertTriangle className="h-8 w-8 text-red-500" />
      </div>

      <div className="max-w-sm space-y-2">
        <h2 className="text-xl font-semibold text-foreground">{title}</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>

      <div className="flex gap-3">
        {onReset && (
          <Button variant="outline" onClick={onReset} size="sm">
            <RefreshCw className="h-4 w-4" />
            Try again
          </Button>
        )}
        {showHomeLink && (
          <Button size="sm" asChild>
            <Link href="/">
              <Home className="h-4 w-4" />
              Go home
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Query Error Display ───────────────────────────────────────
export function QueryError({
  error,
  onRetry,
}: {
  error: Error | null;
  onRetry?: () => void;
}) {
  return (
    <ErrorDisplay
      title="Failed to load"
      description={error?.message ?? "Could not load data. Please try again."}
      onReset={onRetry}
      showHomeLink={false}
    />
  );
}
