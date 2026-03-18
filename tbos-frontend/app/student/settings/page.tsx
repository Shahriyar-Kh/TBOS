// ============================================================
// app/student/settings/page.tsx
// ============================================================
"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { User, Lock, Bell, Globe } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useMe, useUpdateProfile, useChangePassword } from "@/hooks/useAuth";
import { useNotificationPreferences, useUpdateNotificationPreferences } from "@/hooks/useNotifications";
import { useAuthStore } from "@/store/authStore";

// ── Profile form schema ───────────────────────────────────────
const profileSchema = z.object({
  bio: z.string().max(1000).optional(),
  headline: z.string().max(200).optional(),
  country: z.string().max(100).optional(),
  city: z.string().max(100).optional(),
  website: z.string().url().optional().or(z.literal("")),
  linkedin: z.string().url().optional().or(z.literal("")),
  github: z.string().url().optional().or(z.literal("")),
  twitter: z.string().url().optional().or(z.literal("")),
  phone_number: z.string().optional(),
  timezone: z.string().optional(),
});

// ── Password form schema ──────────────────────────────────────
const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Required"),
    new_password: z.string().min(8, "At least 8 characters"),
    confirm_password: z.string().min(1, "Required"),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match",
  });

type ProfileFormData = z.infer<typeof profileSchema>;
type PasswordFormData = z.infer<typeof passwordSchema>;

export default function StudentSettingsPage() {
  const { user } = useAuthStore();
  const { data: me } = useMe();
  const { mutate: updateProfile, isPending: updatingProfile } = useUpdateProfile();
  const { mutate: changePassword, isPending: changingPassword } = useChangePassword();
  const { data: notifPrefs } = useNotificationPreferences();
  const { mutate: updateNotifPrefs, isPending: updatingPrefs } = useUpdateNotificationPreferences();

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      bio: "",
      headline: "",
      country: "",
      city: "",
      website: "",
      linkedin: "",
      github: "",
      twitter: "",
      phone_number: "",
      timezone: "UTC",
    },
  });

  const passwordForm = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  // Populate form from API data
  useEffect(() => {
    if (me?.profile) {
      const p = me.profile;
      profileForm.reset({
        bio: p.bio ?? "",
        headline: p.headline ?? "",
        country: p.country ?? "",
        city: p.city ?? "",
        website: p.website ?? "",
        linkedin: p.linkedin ?? "",
        github: p.github ?? "",
        twitter: p.twitter ?? "",
        phone_number: p.phone_number ?? "",
        timezone: p.timezone ?? "UTC",
      });
    }
  }, [me, profileForm]);

  const onProfileSubmit = (data: ProfileFormData) => {
    updateProfile(data);
  };

  const onPasswordSubmit = (data: PasswordFormData) => {
    changePassword(
      { old_password: data.old_password, new_password: data.new_password },
      { onSuccess: () => passwordForm.reset() }
    );
  };

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your profile, password, and notification preferences
        </p>
      </div>

      {/* Account info banner */}
      <Card>
        <CardContent className="flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 dark:bg-brand-950/30">
            <User className="h-6 w-6 text-brand-600 dark:text-brand-400" />
          </div>
          <div className="flex-1">
            <p className="font-semibold">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <Badge variant="student">Student</Badge>
            {user?.is_verified && <Badge variant="success">Verified</Badge>}
            {user?.google_account && <Badge variant="secondary">Google</Badge>}
          </div>
        </CardContent>
      </Card>

      {/* ── Profile section ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Globe className="h-5 w-5 text-muted-foreground" />
            Profile Information
          </CardTitle>
          <CardDescription>
            Update your public profile visible to instructors and other students.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-5">
            <Input
              label="Headline"
              placeholder="e.g. Full-stack developer, Python enthusiast"
              error={profileForm.formState.errors.headline?.message}
              {...profileForm.register("headline")}
            />
            <div>
              <label className="text-sm font-medium text-foreground">Bio</label>
              <textarea
                className="mt-1.5 flex min-h-24 w-full resize-none rounded-xl border border-input bg-background px-3.5 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Tell others about yourself…"
                {...profileForm.register("bio")}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Country"
                placeholder="e.g. Pakistan"
                {...profileForm.register("country")}
              />
              <Input
                label="City"
                placeholder="e.g. Peshawar"
                {...profileForm.register("city")}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Phone"
                type="tel"
                placeholder="+92 300 0000000"
                {...profileForm.register("phone_number")}
              />
              <Input
                label="Timezone"
                placeholder="UTC"
                {...profileForm.register("timezone")}
              />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input label="Website" placeholder="https://" {...profileForm.register("website")} />
              <Input label="LinkedIn" placeholder="https://linkedin.com/in/…" {...profileForm.register("linkedin")} />
              <Input label="GitHub" placeholder="https://github.com/…" {...profileForm.register("github")} />
              <Input label="Twitter / X" placeholder="https://x.com/…" {...profileForm.register("twitter")} />
            </div>
            <div className="flex justify-end">
              <Button type="submit" isLoading={updatingProfile} loadingText="Saving…">
                Save profile
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ── Password section ─── */}
      {!user?.google_account && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Lock className="h-5 w-5 text-muted-foreground" />
              Change Password
            </CardTitle>
            <CardDescription>
              Use a strong password with uppercase letters, numbers, and symbols.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
              <Input
                label="Current password"
                type="password"
                error={passwordForm.formState.errors.old_password?.message}
                {...passwordForm.register("old_password")}
              />
              <Input
                label="New password"
                type="password"
                hint="At least 8 characters"
                error={passwordForm.formState.errors.new_password?.message}
                {...passwordForm.register("new_password")}
              />
              <Input
                label="Confirm new password"
                type="password"
                error={passwordForm.formState.errors.confirm_password?.message}
                {...passwordForm.register("confirm_password")}
              />
              <div className="flex justify-end">
                <Button type="submit" isLoading={changingPassword} loadingText="Updating…">
                  Update password
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* ── Notification preferences ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bell className="h-5 w-5 text-muted-foreground" />
            Notification Preferences
          </CardTitle>
          <CardDescription>
            Control which notifications you receive via email and in-app.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {notifPrefs &&
            (
              [
                { key: "email_notifications_enabled", label: "Email notifications", description: "Receive notifications by email" },
                { key: "in_app_notifications_enabled", label: "In-app notifications", description: "Show notifications in the app" },
                { key: "course_updates", label: "Course updates", description: "New lessons, announcements from enrolled courses" },
                { key: "assignment_notifications", label: "Assignment reminders", description: "Deadlines and grading updates" },
                { key: "quiz_notifications", label: "Quiz notifications", description: "New quizzes and attempt results" },
              ] as const
            ).map(({ key, label, description }) => (
              <div key={key} className="flex items-start justify-between gap-4 py-2">
                <div>
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={notifPrefs[key]}
                  onClick={() =>
                    updateNotifPrefs({ [key]: !notifPrefs[key] })
                  }
                  disabled={updatingPrefs}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50 ${
                    notifPrefs[key] ? "bg-brand-500" : "bg-slate-200 dark:bg-slate-700"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      notifPrefs[key] ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            ))}
        </CardContent>
      </Card>
    </div>
  );
}
