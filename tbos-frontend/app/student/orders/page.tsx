// ============================================================
// app/student/orders/page.tsx — Student order history
// ============================================================
"use client";

import Link from "next/link";
import { ShoppingBag, ExternalLink, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { useMyOrders } from "@/hooks/usePayments";
import { formatCurrency, formatDate } from "@/lib/utils";

const STATUS_BADGE = {
  COMPLETED: "success" as const,
  PENDING: "warning" as const,
  FAILED: "destructive" as const,
  REFUNDED: "secondary" as const,
};

export default function StudentOrdersPage() {
  const { data, isLoading, error, refetch } = useMyOrders();
  const orders = data?.results ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Order History</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your course purchases and payment history
        </p>
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-2xl border border-border p-4">
              <div className="flex items-center gap-4">
                <Skeleton className="h-14 w-20 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-1/4" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
            </div>
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border py-20 text-center">
          <ShoppingBag className="h-12 w-12 text-slate-300" />
          <div>
            <p className="font-semibold">No orders yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Your course purchases will appear here
            </p>
          </div>
          <Button size="sm" asChild>
            <Link href="/courses">Browse courses</Link>
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card key={order.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex items-center gap-4 p-4">
                  {/* Course thumbnail */}
                  <div className="h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
                    {order.course.thumbnail && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={order.course.thumbnail}
                        alt={order.course.title}
                        className="h-full w-full object-cover"
                      />
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{order.course.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {order.course.instructor_name} · Order #{order.order_number}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatDate(order.created_at)} · {order.payment_method}
                    </p>
                  </div>

                  {/* Amount & status */}
                  <div className="shrink-0 text-right space-y-1.5">
                    <p className="font-bold text-foreground">
                      {formatCurrency(order.amount, order.currency)}
                    </p>
                    <Badge
                      variant={STATUS_BADGE[order.status as keyof typeof STATUS_BADGE] ?? "secondary"}
                      className="text-[10px]"
                    >
                      {order.status}
                    </Badge>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between border-t border-border bg-slate-50/50 px-4 py-2 dark:bg-slate-900/50">
                  <span className="text-xs text-muted-foreground font-mono">
                    {order.order_number}
                  </span>
                  <div className="flex gap-2">
                    {order.status === "COMPLETED" && (
                      <Button size="sm" variant="ghost" asChild>
                        <Link href={`/student/courses`}>
                          Go to course
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Link>
                      </Button>
                    )}
                    {order.status === "FAILED" && (
                      <Button size="sm" variant="ghost" asChild>
                        <Link href={`/courses/${order.course.id}`}>
                          <RefreshCw className="h-3.5 w-3.5" />
                          Retry
                        </Link>
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
