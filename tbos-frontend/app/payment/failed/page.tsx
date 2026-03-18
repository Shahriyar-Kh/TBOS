// ============================================================
// app/payment/failed/page.tsx
// ============================================================
"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { XCircle, RefreshCw, ArrowLeft, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

export default function PaymentFailedPage() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-red-50 to-white p-6 dark:from-red-950/10 dark:to-slate-950">
      <Card className="w-full max-w-md shadow-xl">
        <CardContent className="p-8 text-center space-y-6">
          {/* Failed icon */}
          <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/40">
            <XCircle className="h-12 w-12 text-red-500" />
          </div>

          <div className="space-y-2">
            <h1 className="font-display text-2xl font-bold text-foreground">
              Payment Failed
            </h1>
            <p className="text-muted-foreground">
              Your payment could not be processed. No charges were made to your account.
            </p>
          </div>

          {/* Common reasons */}
          <div className="rounded-xl bg-slate-50 p-4 text-left dark:bg-slate-900 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Common reasons
            </p>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {[
                "Insufficient funds",
                "Card declined by bank",
                "Incorrect card details",
                "Connection timeout",
              ].map((reason) => (
                <li key={reason} className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col gap-2">
            {/* Try again — go back to course page if we have order context */}
            <Button className="w-full" size="lg" asChild>
              <Link href="/courses">
                <RefreshCw className="h-4 w-4" />
                Try again
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                Back to home
              </Link>
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            Need help?{" "}
            <Link href="/contact" className="text-brand-500 hover:underline">
              Contact support
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
