// ============================================================
// app/admin/payments/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CreditCard, Search, RefreshCw, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem,
} from "@/components/ui/Dropdown";
import { TableRowSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import AdminService from "@/services/adminService";
import { formatCurrency, formatDate, extractApiError } from "@/lib/utils";

type StatusFilter = "" | "PENDING" | "SUCCESS" | "FAILED" | "REFUNDED";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "", label: "All" },
  { value: "SUCCESS", label: "Success" },
  { value: "PENDING", label: "Pending" },
  { value: "FAILED", label: "Failed" },
  { value: "REFUNDED", label: "Refunded" },
];

const STATUS_VARIANT: Record<
  string,
  "success" | "warning" | "destructive" | "secondary"
> = {
  SUCCESS: "success",
  PENDING: "warning",
  FAILED: "destructive",
  REFUNDED: "secondary",
};

export default function AdminPaymentsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin", "payments", statusFilter],
    queryFn: () =>
      AdminService.getPayments(statusFilter ? { status: statusFilter } : {}),
  });

  const { mutate: refundOrder, isPending: refunding } = useMutation({
    mutationFn: (orderId: string) => AdminService.refundOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "payments"] });
      toast.success("Order refunded successfully.");
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const payments = data?.results?.filter(
    (p: { order?: { order_number?: string; student?: { email?: string }; course?: { title?: string } } }) =>
      !search ||
      (p.order?.order_number ?? "").toLowerCase().includes(search.toLowerCase()) ||
      (p.order?.student?.email ?? "").toLowerCase().includes(search.toLowerCase()) ||
      (p.order?.course?.title ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Payments</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Platform payment transactions and refunds
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex rounded-xl border border-border overflow-hidden">
          {STATUS_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setStatusFilter(value)}
              className={`px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                statusFilter === value
                  ? "bg-purple-600 text-white"
                  : "text-muted-foreground hover:bg-slate-50 dark:hover:bg-slate-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <Input
          placeholder="Search by order, email or course…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
          containerClassName="max-w-sm"
        />
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-slate-50 dark:bg-slate-800/50">
            <tr>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Order
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hidden md:table-cell">
                Course
              </th>
              <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Amount
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Status
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hidden lg:table-cell">
                Date
              </th>
              <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={6} />
              ))
            ) : !payments?.length ? (
              <tr>
                <td colSpan={6} className="py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <CreditCard className="h-10 w-10 text-slate-300" />
                    <p className="text-sm text-muted-foreground">
                      No payments found
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              payments.map(
                (payment: {
                  id: string;
                  order?: { order_number?: string; student?: { email?: string; first_name?: string; last_name?: string }; course?: { title?: string }; amount?: string | number; id?: string };
                  payment_provider?: string;
                  payment_status?: string;
                  created_at?: string;
                }) => (
                  <tr
                    key={payment.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="px-5 py-4">
                      <p className="font-mono text-xs font-medium text-foreground">
                        {payment.order?.order_number ?? "—"}
                      </p>
                      <p className="text-xs text-muted-foreground truncate max-w-[140px]">
                        {payment.order?.student?.email ?? "—"}
                      </p>
                    </td>
                    <td className="px-5 py-4 hidden md:table-cell">
                      <p className="text-sm truncate max-w-[200px]">
                        {payment.order?.course?.title ?? "—"}
                      </p>
                    </td>
                    <td className="px-5 py-4 text-right font-semibold">
                      {payment.order?.amount
                        ? formatCurrency(payment.order.amount)
                        : "—"}
                    </td>
                    <td className="px-5 py-4">
                      <Badge
                        variant={
                          STATUS_VARIANT[payment.payment_status ?? ""] ??
                          "secondary"
                        }
                      >
                        {payment.payment_status ?? "—"}
                      </Badge>
                    </td>
                    <td className="px-5 py-4 text-muted-foreground hidden lg:table-cell">
                      {payment.created_at
                        ? formatDate(payment.created_at)
                        : "—"}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {payment.payment_status === "SUCCESS" && payment.order?.id && (
                        <Dropdown>
                          <DropdownTrigger asChild>
                            <Button variant="ghost" size="icon-sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownTrigger>
                          <DropdownContent align="end">
                            <DropdownItem
                              disabled={refunding}
                              onClick={() =>
                                payment.order?.id && refundOrder(payment.order.id)
                              }
                              className="text-amber-600 focus:text-amber-600"
                            >
                              <RefreshCw className="h-4 w-4" />
                              Issue refund
                            </DropdownItem>
                          </DropdownContent>
                        </Dropdown>
                      )}
                    </td>
                  </tr>
                )
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
