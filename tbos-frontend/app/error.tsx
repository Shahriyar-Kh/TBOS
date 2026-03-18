// ============================================================
// app/error.tsx — Next.js Error UI
// ============================================================
"use client";

import { useEffect } from "react";
import { ErrorDisplay } from "@/components/common/ErrorBoundary";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <html>
      <body className="min-h-screen bg-white font-sans">
        <ErrorDisplay
          title="Something went wrong"
          description={error.message ?? "An unexpected application error occurred."}
          onReset={reset}
          className="min-h-screen"
        />
      </body>
    </html>
  );
}
