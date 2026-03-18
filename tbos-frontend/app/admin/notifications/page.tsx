// ============================================================
// app/admin/notifications/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Users } from "lucide-react";
import { toast } from "sonner";
import { NotificationCenter } from "@/components/common/NotificationCenter";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import AdminService from "@/services/adminService";
import { extractApiError } from "@/lib/utils";

export default function AdminNotificationsPage() {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");

  const broadcastMutation = useMutation({
    mutationFn: () => AdminService.broadcastNotification({ title, message }),
    onSuccess: (data) => {
      toast.success(
        `Broadcast sent to ${(data as { recipient_count: number }).recipient_count} users!`
      );
      setTitle("");
      setMessage("");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  return (
    <div className="space-y-8">
      {/* Broadcast panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Send className="h-5 w-5 text-brand-500" />
            Broadcast Notification
          </CardTitle>
          <CardDescription>
            Send a system alert to all active users on the platform at once.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Notification title"
            placeholder="e.g. Platform maintenance on Sunday…"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Textarea
            label="Message"
            placeholder="Write your message to all users…"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
          />
          <div className="flex items-center justify-between gap-4">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Users className="h-3.5 w-3.5" />
              This will notify all active users
            </p>
            <Button
              onClick={() => broadcastMutation.mutate()}
              isLoading={broadcastMutation.isPending}
              loadingText="Sending…"
              disabled={!title.trim() || !message.trim()}
            >
              <Send className="h-4 w-4" />
              Send broadcast
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Own notifications */}
      <NotificationCenter title="Your Notifications" />
    </div>
  );
}
