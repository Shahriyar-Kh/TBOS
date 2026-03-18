// ============================================================
// components/common/DataTable.tsx
// Generic table with pagination, empty state, loading skeletons
// ============================================================
"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { ChevronLeft, ChevronRight, Inbox } from "lucide-react";

interface Column<T> {
  key: string;
  header: string;
  cell: (row: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  skeletonRows?: number;
  emptyIcon?: React.ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
  // Pagination
  page?: number;
  totalCount?: number;
  pageSize?: number;
  hasNext?: boolean;
  hasPrev?: boolean;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  className?: string;
}

export function DataTable<T extends { id?: string }>({
  columns,
  data,
  isLoading = false,
  skeletonRows = 8,
  emptyIcon = <Inbox className="h-10 w-10 text-slate-300" />,
  emptyTitle = "No data",
  emptyDescription = "Nothing to show here yet.",
  emptyAction,
  page,
  totalCount,
  pageSize = 20,
  hasNext,
  hasPrev,
  onNextPage,
  onPrevPage,
  className,
}: DataTableProps<T>) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-border bg-card",
        className
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          {/* Header */}
          <thead className="border-b border-border bg-slate-50 dark:bg-slate-900/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground",
                    col.headerClassName
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <tbody className="divide-y divide-border">
            {isLoading ? (
              // Loading skeleton rows
              Array.from({ length: skeletonRows }).map((_, rowIdx) => (
                <tr key={rowIdx}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-5 py-4">
                      <div className="h-4 w-full animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              // Empty state
              <tr>
                <td colSpan={columns.length} className="px-5 py-16">
                  <div className="flex flex-col items-center gap-3 text-center">
                    {emptyIcon}
                    <div>
                      <p className="font-semibold text-foreground">{emptyTitle}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {emptyDescription}
                      </p>
                    </div>
                    {emptyAction}
                  </div>
                </td>
              </tr>
            ) : (
              // Data rows
              data.map((row, rowIdx) => (
                <tr
                  key={row.id ?? rowIdx}
                  className="transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn("px-5 py-4", col.className)}
                    >
                      {col.cell(row, rowIdx)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      {(hasNext || hasPrev) && page !== undefined && (
        <div className="flex items-center justify-between border-t border-border px-5 py-3">
          <p className="text-xs text-muted-foreground">
            {totalCount !== undefined && (
              <>
                Showing{" "}
                {((page - 1) * pageSize + 1).toLocaleString()}–
                {Math.min(page * pageSize, totalCount).toLocaleString()} of{" "}
                {totalCount.toLocaleString()}
              </>
            )}
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={onPrevPage}
              disabled={!hasPrev || isLoading}
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </Button>
            <span className="min-w-[2rem] text-center text-xs font-medium text-muted-foreground">
              {page}
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={onNextPage}
              disabled={!hasNext || isLoading}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
