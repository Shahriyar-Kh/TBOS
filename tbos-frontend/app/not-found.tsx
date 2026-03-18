// ============================================================
// app/not-found.tsx — 404 page
// ============================================================

import Link from "next/link";
import { Home, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background px-6 text-center">
      {/* Large 404 */}
      <div className="relative">
        <p className="font-display text-[120px] font-bold leading-none text-slate-100 dark:text-slate-800 select-none lg:text-[180px]">
          404
        </p>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="space-y-2">
            <p className="font-display text-2xl font-bold text-foreground">
              Page not found
            </p>
            <p className="text-sm text-muted-foreground">
              The page you&apos;re looking for doesn&apos;t exist or has been moved.
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" asChild>
          <Link href="/courses">
            <Search className="h-4 w-4" />
            Browse courses
          </Link>
        </Button>
        <Button asChild>
          <Link href="/">
            <Home className="h-4 w-4" />
            Go home
          </Link>
        </Button>
      </div>
    </div>
  );
}
