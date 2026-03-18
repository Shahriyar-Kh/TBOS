// ============================================================
// components/Providers.tsx — Global React providers
// ============================================================
"use client";

import { type ReactNode, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { makeQueryClient } from "@/lib/queryClient";

export function Providers({ children }: { children: ReactNode }) {
  // Use useState so the client is stable across renders on the same
  // client-side navigation (avoids recreating the client on every render)
  const [queryClient] = useState(() => makeQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        enableSystem
        disableTransitionOnChange
      >
        {children}
        <Toaster
          position="top-right"
          richColors
          closeButton
          duration={4000}
          toastOptions={{
            classNames: {
              toast:
                "font-sans text-sm border border-slate-200 dark:border-slate-700 shadow-lg",
              title: "font-semibold",
              description: "text-slate-500 dark:text-slate-400",
            },
          }}
        />
      </ThemeProvider>
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
