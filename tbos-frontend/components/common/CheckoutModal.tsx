// ============================================================
// components/common/CheckoutModal.tsx
// ============================================================
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CreditCard, ShoppingBag } from "lucide-react";

import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
} from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCheckout } from "@/hooks/usePayments";
import { formatCurrency } from "@/lib/utils";
import type { Course } from "@/types/course";

const billingSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  email: z.string().email("Valid email required"),
  country: z.string().min(2, "Required"),
  city: z.string().min(1, "Required"),
  postal_code: z.string().min(3, "Required"),
  address: z.string().min(5, "Full address required"),
  phone_number: z.string().optional(),
});

type BillingFormData = z.infer<typeof billingSchema>;

interface CheckoutModalProps {
  course: Course;
  open: boolean;
  onClose: () => void;
}

export function CheckoutModal({ course, open, onClose }: CheckoutModalProps) {
  const { mutate: checkout, isPending } = useCheckout();
  const price = parseFloat(course.effective_price ?? course.price);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BillingFormData>({ resolver: zodResolver(billingSchema) });

  const onSubmit = (data: BillingFormData) => {
    checkout({ courseId: course.id, billingDetails: data });
  };

  return (
    <Modal open={open} onOpenChange={(v) => !v && onClose()}>
      <ModalContent className="max-w-2xl">
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2">
            <ShoppingBag className="h-5 w-5 text-brand-500" />
            Complete Purchase
          </ModalTitle>
          <ModalDescription>
            You&apos;re purchasing{" "}
            <span className="font-semibold text-foreground">{course.title}</span>{" "}
            for{" "}
            <span className="font-bold text-brand-600">{formatCurrency(price)}</span>
          </ModalDescription>
        </ModalHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First name"
              error={errors.first_name?.message}
              {...register("first_name")}
            />
            <Input
              label="Last name"
              error={errors.last_name?.message}
              {...register("last_name")}
            />
          </div>
          <Input
            label="Email"
            type="email"
            error={errors.email?.message}
            {...register("email")}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Country"
              placeholder="e.g. US"
              error={errors.country?.message}
              {...register("country")}
            />
            <Input
              label="City"
              error={errors.city?.message}
              {...register("city")}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Postal code"
              error={errors.postal_code?.message}
              {...register("postal_code")}
            />
            <Input
              label="Phone (optional)"
              type="tel"
              {...register("phone_number")}
            />
          </div>
          <Input
            label="Address"
            error={errors.address?.message}
            {...register("address")}
          />

          <div className="rounded-xl bg-slate-50 dark:bg-slate-800/50 p-4 text-xs text-muted-foreground space-y-1">
            <p className="font-semibold text-foreground">Secure checkout via Stripe</p>
            <p>You&apos;ll be redirected to Stripe to complete payment. Your card details are never stored on our servers.</p>
          </div>

          <ModalFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={isPending}
              loadingText="Redirecting…"
            >
              <CreditCard className="h-4 w-4" />
              Pay {formatCurrency(price)}
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
