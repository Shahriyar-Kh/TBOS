// ============================================================
// components/common/SettingsPanel.tsx
// Shared settings UI used by instructor & admin settings pages
// ============================================================
"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { User, Lock, Bell, Globe, Shield } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Badge } from "@/components/ui/Badge";
import { useMe, useUpdateProfile, useChangePassword } from "@/hooks/useAuth";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/hooks/useNotifications";
import { useAuthStore } from "@/store/authStore";

const profileSchema = z.object({
  bio: z.string().max(1000).optional(),
  headline: z.string().max(200).optional(),
  country: z.string().max(100).optional(),
  city: z.string().max(100).optional(),
  website: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  linkedin: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  github: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  twitter: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  phone_number: z.string().max(20).optional(),
  timezone: z.string().optional(),
});

const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Required"),
    new_password: z
      .string()
      .min(8, "At least 8 characters")
      .regex(/[A-Z]/, "Needs uppercase")
      .regex(/[0-9]/, "Needs number"),
    confirm_new_password: z.string().min(1, "Required"),
  })
  .refine((d) => d.new_password === d.confirm_new_password, {
    message: "Passwords do not match",
    path: ["confirm_new_password"],
  });

type ProfileForm = z.infer<typeof profileSchema>;
type PasswordForm = z.infer<typeof passwordSchema>;

export function SettingsPanel() {
  const { user } = useAuthStore();
  const { data: me } = useMe();
  const { mutate: updateProfile, isPending: updatingProfile } = useUpdateProfile();
  const { mutate: changePassword, isPending: changingPassword } = useChangePassword();
  const { data: prefs } = useNotificationPreferences();
  const { mutate: updatePrefs } = useUpdateNotificationPreferences();

  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(profileSchema) });
  const passwordForm = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) });

  // Pre-fill profile from API
  useEffect(() => {
    if (me?.profile) {
      profileForm.reset({
        bio: me.profile.bio ?? "",
        headline: me.profile.headline ?? "",
        country: me.profile.country ?? "",
        city: me.profile.city ?? "",
        website: me.profile.website ?? "",
        linkedin: me.profile.linkedin ?? "",
        github: me.profile.github ?? "",
        twitter: me.profile.twitter ?? "",
        phone_number: me.profile.phone_number ?? "",
        timezone: me.profile.timezone ?? "UTC",
      });
    }
  }, [me]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account preferences and profile
        </p>
      </div>

      {/* Account info (read-only) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Shield className="h-4 w-4 text-muted-foreground" />
            Account
          </CardTitle>
          <CardDescription>Your core account details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="First name" value={me?.first_name ?? ""} readOnly containerClassName="opacity-70" />
            <Input label="Last name" value={me?.last_name ?? ""} readOnly containerClassName="opacity-70" />
            <Input label="Email address" value={me?.email ?? ""} readOnly containerClassName="opacity-70" />
            <div className="flex flex-col gap-1.5">
              <p className="text-sm font-medium text-foreground">Role</p>
              <div className="flex h-10 items-center">
                <Badge
                  variant={
                    user?.role === "admin"
                      ? "admin"
                      : user?.role === "instructor"
                      ? "instructor"
                      : "student"
                  }
                  className="capitalize"
                >
                  {user?.role}
                </Badge>
                {me?.is_verified && (
                  <Badge variant="success" className="ml-2">Verified</Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="h-4 w-4 text-muted-foreground" />
            Profile
          </CardTitle>
          <CardDescription>Update your public profile information</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={profileForm.handleSubmit((data) => updateProfile(data))}
            className="space-y-4"
          >
            <Input
              label="Headline"
              placeholder="e.g. Senior Frontend Developer · React Enthusiast"
              error={profileForm.formState.errors.headline?.message}
              {...profileForm.register("headline")}
            />
            <Textarea
              label="Bio"
              placeholder="Tell others about yourself…"
              rows={4}
              error={profileForm.formState.errors.bio?.message}
              {...profileForm.register("bio")}
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="City"
                placeholder="Karachi"
                {...profileForm.register("city")}
              />
              <Input
                label="Country"
                placeholder="Pakistan"
                {...profileForm.register("country")}
              />
              <Input
                label="Phone number"
                placeholder="+92 300 0000000"
                {...profileForm.register("phone_number")}
              />
              <Input
                label="Timezone"
                placeholder="UTC"
                {...profileForm.register("timezone")}
              />
            </div>
            <div className="border-t border-border pt-4">
              <p className="mb-3 text-sm font-medium text-foreground">Social links</p>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Input
                  label="Website"
                  placeholder="https://yoursite.com"
                  error={profileForm.formState.errors.website?.message}
                  {...profileForm.register("website")}
                />
                <Input
                  label="LinkedIn"
                  placeholder="https://linkedin.com/in/…"
                  error={profileForm.formState.errors.linkedin?.message}
                  {...profileForm.register("linkedin")}
                />
                <Input
                  label="GitHub"
                  placeholder="https://github.com/…"
                  error={profileForm.formState.errors.github?.message}
                  {...profileForm.register("github")}
                />
                <Input
                  label="Twitter / X"
                  placeholder="https://twitter.com/…"
                  error={profileForm.formState.errors.twitter?.message}
                  {...profileForm.register("twitter")}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                type="submit"
                isLoading={updatingProfile}
                loadingText="Saving…"
              >
                Save profile
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Lock className="h-4 w-4 text-muted-foreground" />
            Change Password
          </CardTitle>
          <CardDescription>
            Update your password. Google-linked accounts may not have a password.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={passwordForm.handleSubmit((data) =>
              changePassword({
                old_password: data.old_password,
                new_password: data.new_password,
              })
            )}
            className="space-y-4 max-w-md"
          >
            <Input
              label="Current password"
              type="password"
              placeholder="Enter current password"
              error={passwordForm.formState.errors.old_password?.message}
              {...passwordForm.register("old_password")}
            />
            <Input
              label="New password"
              type="password"
              placeholder="Min. 8 chars, 1 uppercase, 1 number"
              error={passwordForm.formState.errors.new_password?.message}
              {...passwordForm.register("new_password")}
            />
            <Input
              label="Confirm new password"
              type="password"
              placeholder="Re-enter new password"
              error={passwordForm.formState.errors.confirm_new_password?.message}
              {...passwordForm.register("confirm_new_password")}
            />
            <Button
              type="submit"
              isLoading={changingPassword}
              loadingText="Changing…"
            >
              Change password
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Notification preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bell className="h-4 w-4 text-muted-foreground" />
            Notification Preferences
          </CardTitle>
          <CardDescription>Control which notifications you receive</CardDescription>
        </CardHeader>
        <CardContent>
          {prefs ? (
            <div className="space-y-4">
              {[
                {
                  key: "email_notifications_enabled" as const,
                  label: "Email notifications",
                  description: "Receive notifications via email",
                },
                {
                  key: "in_app_notifications_enabled" as const,
                  label: "In-app notifications",
                  description: "Show notifications in the dashboard",
                },
                {
                  key: "course_updates" as const,
                  label: "Course updates",
                  description: "New lessons and course announcements",
                },
                {
                  key: "assignment_notifications" as const,
                  label: "Assignment deadlines",
                  description: "Reminders about upcoming submissions",
                },
                {
                  key: "quiz_notifications" as const,
                  label: "Quiz availability",
                  description: "When new quizzes become available",
                },
              ].map(({ key, label, description }) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-xl border border-border p-4"
                >
                  <div>
                    <p className="text-sm font-semibold">{label}</p>
                    <p className="text-xs text-muted-foreground">{description}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => updatePrefs({ [key]: !prefs[key] })}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 ${
                      prefs[key]
                        ? "bg-brand-500"
                        : "bg-slate-200 dark:bg-slate-700"
                    }`}
                    role="switch"
                    aria-checked={prefs[key]}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                        prefs[key] ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800"
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
