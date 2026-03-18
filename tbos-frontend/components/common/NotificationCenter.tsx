// ============================================================
// components/common/NotificationCenter.tsx
// Reusable notification list & mark-read UI for all roles
// ============================================================
"use client";

import { useState } from "react";
import { Bell, Check, CheckCheck, Inbox, BookOpen, Award, ClipboardList, FileText, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { useNotifications, useMarkNotificationRead, useMarkAllRead } from "@/hooks/useNotifications";
import { formatRelativeTime, cn } from "@/lib/utils";
import type { Notification } from "@/services/notificationService";

const TYPE_CONFIG: Record<
  string,
  { icon: React.ReactNode; color: string; bg: string }
> = {
  COURSE_UPDATE: {
    icon: <BookOpen className="h-4 w-4" />,
    color: "text-brand-500",
    bg: "bg-brand-50 dark:bg-brand-950/30",
  },
  NEW_LESSON: {
    icon: <BookOpen className="h-4 w-4" />,
    color: "text-indigo-500",
    bg: "bg-indigo-50 dark:bg-indigo-950/30",
  },
  QUIZ_AVAILABLE: {
    icon: <ClipboardList className="h-4 w-4" />,
    color: "text-violet-500",
    bg: "bg-violet-50 dark:bg-violet-950/30",
  },
  ASSIGNMENT_DEADLINE: {
    icon: <FileText className="h-4 w-4" />,
    color: "text-orange-500",
    bg: "bg-orange-50 dark:bg-orange-950/30",
  },
  CERTIFICATE_ISSUED: {
    icon: <Award className="h-4 w-4" />,
    color: "text-emerald-500",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  SYSTEM_ALERT: {
    icon: <Zap className="h-4 w-4" />,
    color: "text-amber-500",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
};

const DEFAULT_TYPE = {
  icon: <Bell className="h-4 w-4" />,
  color: "text-slate-500",
  bg: "bg-slate-100 dark:bg-slate-800",
};

type Filter = "all" | "unread";

interface NotificationCenterProps {
  title?: string;
}

export function NotificationCenter({ title = "Notifications" }: NotificationCenterProps) {
  const [filter, setFilter] = useState<Filter>("all");

  const {
    data: allData,
    isLoading: allLoading,
    error,
    refetch,
  } = useNotifications();

  const {
    data: unreadData,
    isLoading: unreadLoading,
  } = useNotifications(false);

  const { mutate: markRead, isPending: markingRead } = useMarkNotificationRead();
  const { mutate: markAll, isPending: markingAll } = useMarkAllRead();

  const notifications =
    filter === "unread"
      ? (unreadData?.results ?? [])
      : (allData?.results ?? []);

  const unreadCount = unreadData?.count ?? 0;
  const isLoading = filter === "unread" ? unreadLoading : allLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-3">
            {title}
            {unreadCount > 0 && (
              <Badge variant="default" className="text-xs font-bold">
                {unreadCount} new
              </Badge>
            )}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Stay up to date with your learning activity
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAll()}
            isLoading={markingAll}
            loadingText="Marking…"
          >
            <CheckCheck className="h-4 w-4" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-xl border border-border bg-muted p-1 w-fit">
        {(["all", "unread"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-lg px-4 py-1.5 text-sm font-medium capitalize transition-all",
              filter === f
                ? "bg-white shadow-sm text-foreground dark:bg-slate-800"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {f}
            {f === "unread" && unreadCount > 0 && (
              <span className="ml-1.5 rounded-full bg-brand-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Notification list */}
      <div className="space-y-2">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <NotificationSkeleton key={i} />
          ))
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border py-20 text-center">
            <Inbox className="h-12 w-12 text-slate-300" />
            <div>
              <p className="font-semibold text-foreground">
                {filter === "unread" ? "You're all caught up!" : "No notifications yet"}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {filter === "unread"
                  ? "No unread notifications"
                  : "Notifications about your courses and activity will appear here"}
              </p>
            </div>
            {filter === "unread" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFilter("all")}
              >
                View all notifications
              </Button>
            )}
          </div>
        ) : (
          notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkRead={() => markRead(notification.id)}
              isMarkingRead={markingRead}
            />
          ))
        )}
      </div>
    </div>
  );
}

function NotificationItem({
  notification,
  onMarkRead,
  isMarkingRead,
}: {
  notification: Notification;
  onMarkRead: () => void;
  isMarkingRead: boolean;
}) {
  const typeConfig =
    TYPE_CONFIG[notification.notification_type] ?? DEFAULT_TYPE;

  return (
    <div
      className={cn(
        "flex items-start gap-4 rounded-2xl border border-border p-4 transition-all",
        !notification.is_read
          ? "bg-brand-50/50 border-brand-100 dark:bg-brand-950/10 dark:border-brand-900/50"
          : "bg-card hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
      )}
    >
      {/* Icon */}
      <div
        className={cn(
          "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
          typeConfig.bg
        )}
      >
        <span className={typeConfig.color}>{typeConfig.icon}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p
            className={cn(
              "text-sm leading-snug",
              !notification.is_read
                ? "font-semibold text-foreground"
                : "font-medium text-foreground"
            )}
          >
            {notification.title}
          </p>
          <span className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
            {formatRelativeTime(notification.created_at)}
          </span>
        </div>
        <p className="mt-0.5 text-sm text-muted-foreground leading-relaxed">
          {notification.message}
        </p>
        <div className="mt-2 flex items-center gap-3">
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800">
            {notification.notification_type.replace(/_/g, " ")}
          </span>
          {!notification.is_read && (
            <button
              onClick={onMarkRead}
              disabled={isMarkingRead}
              className="flex items-center gap-1 text-xs font-medium text-brand-500 hover:text-brand-600 transition-colors disabled:opacity-50"
            >
              <Check className="h-3 w-3" />
              Mark as read
            </button>
          )}
          {notification.is_read && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Check className="h-3 w-3" />
              Read
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function NotificationSkeleton() {
  return (
    <div className="flex items-start gap-4 rounded-2xl border border-border p-4">
      <Skeleton className="h-9 w-9 shrink-0 rounded-xl" />
      <div className="flex-1 space-y-2">
        <div className="flex justify-between gap-4">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-3 w-16 shrink-0" />
        </div>
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-5 w-24 rounded-full" />
      </div>
    </div>
  );
}
