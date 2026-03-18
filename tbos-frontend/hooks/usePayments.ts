// ============================================================
// hooks/usePayments.ts
// ============================================================
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import PaymentService, { type BillingDetails } from "@/services/paymentService";
import { QUERY_KEYS } from "@/config/constants";
import { extractApiError } from "@/lib/utils";

export function useMyOrders() {
  return useQuery({
    queryKey: ["payments", "orders"],
    queryFn: PaymentService.listMyOrders,
  });
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: ["payments", "order", id],
    queryFn: () => PaymentService.getOrder(id),
    enabled: !!id,
  });
}

export function useCheckout() {
  const router = useRouter();
  return useMutation({
    mutationFn: ({
      courseId,
      billingDetails,
    }: {
      courseId: string;
      billingDetails: BillingDetails;
    }) =>
      PaymentService.checkout({
        course_id: courseId,
        billing_details: billingDetails,
      }),
    onSuccess: (data) => {
      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useVerifyPayment() {
  const queryClient = useQueryClient();
  const router = useRouter();
  return useMutation({
    mutationFn: ({
      orderId,
      transactionId,
    }: {
      orderId: string;
      transactionId: string;
    }) =>
      PaymentService.verifyPayment({
        order_id: orderId,
        transaction_id: transactionId,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.enrollments.list });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      toast.success("Payment verified! You're now enrolled.");
      router.push("/student/courses");
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}
