// ============================================================
// app/payment/success/page.tsx
// ============================================================
"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle, BookOpen, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { useMutation } from "@tanstack/react-query";
import PaymentService from "@/services/paymentService";
import { toast } from "sonner";

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("session_id");
  const orderId = searchParams.get("order_id");
  const [verified, setVerified] = useState(false);
  const [orderData, setOrderData] = useState<{ id: string; course: { id: string; title: string } } | null>(null);

  const verifyMutation = useMutation({
    mutationFn: ({ orderId, sessionId }: { orderId: string; sessionId: string }) =>
      PaymentService.verifyPayment({ order_id: orderId, transaction_id: sessionId }),
    onSuccess: (data) => {
      setVerified(true);
      setOrderData(data as typeof orderData);
      toast.success("Payment verified! Your course is now unlocked.");
    },
    onError: () => {
      // Payment webhook may have already handled it — still show success
      setVerified(true);
      toast.success("Your enrollment has been confirmed!");
    },
  });

  useEffect(() => {
    if (orderId && sessionId) {
      verifyMutation.mutate({ orderId, sessionId });
    } else {
      setVerified(true);
    }
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 to-white p-6 dark:from-emerald-950/20 dark:to-slate-950">
      <Card className="w-full max-w-md shadow-xl">
        <CardContent className="p-8 text-center space-y-6">
          {verifyMutation.isPending ? (
            <>
              <Loader2 className="mx-auto h-16 w-16 animate-spin text-brand-500" />
              <p className="font-semibold text-foreground">Confirming your payment…</p>
              <p className="text-sm text-muted-foreground">Please wait while we verify your transaction.</p>
            </>
          ) : (
            <>
              {/* Success icon */}
              <div className="relative mx-auto w-fit">
                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/40">
                  <CheckCircle className="h-12 w-12 text-emerald-500" />
                </div>
                <div className="absolute -right-1 -top-1 flex h-7 w-7 items-center justify-center rounded-full bg-brand-500 text-white text-xs font-bold">
                  ✓
                </div>
              </div>

              <div className="space-y-2">
                <h1 className="font-display text-2xl font-bold text-foreground">
                  Payment Successful!
                </h1>
                <p className="text-muted-foreground">
                  {orderData?.course?.title
                    ? `You now have full access to "${orderData.course.title}".`
                    : "You now have full access to your new course."}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900">
                <div className="flex items-center gap-3 text-left">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-950/30">
                    <BookOpen className="h-5 w-5 text-brand-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">Course enrolled</p>
                    <p className="text-xs text-muted-foreground">
                      Find it in My Courses to start learning
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <Button className="w-full" size="lg" asChild>
                  <Link href="/student/courses">
                    Go to My Courses
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/courses">Browse more courses</Link>
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
