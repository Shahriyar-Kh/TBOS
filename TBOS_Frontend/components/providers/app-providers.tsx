"use client";

import { Toaster } from "react-hot-toast";
import { QueryProvider } from "@/components/providers/query-provider";

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryProvider>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            border: "1px solid var(--border)",
            background: "var(--card)",
            color: "var(--card-foreground)",
          },
        }}
      />
    </QueryProvider>
  );
}
