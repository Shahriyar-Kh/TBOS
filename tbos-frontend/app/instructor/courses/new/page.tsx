// ============================================================
// app/instructor/courses/new/page.tsx
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, BookOpen } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCreateCourse } from "@/hooks/useCourses";
import { publicApi } from "@/lib/axios";

const courseSchema = z.object({
  title: z.string().min(5, "Title must be at least 5 characters"),
  subtitle: z.string().max(500).optional(),
  description: z.string().min(20, "Description must be at least 20 characters"),
  category_id: z.string().min(1, "Please select a category"),
  level_id: z.string().optional(),
  language_id: z.string().optional(),
  price: z.coerce.number().min(0, "Price cannot be negative").default(0),
  discount_price: z.coerce.number().min(0).optional(),
  is_free: z.boolean().default(false),
  certificate_available: z.boolean().default(false),
  thumbnail: z.string().url().optional().or(z.literal("")),
  promo_video_url: z.string().url().optional().or(z.literal("")),
});

type CourseFormData = z.infer<typeof courseSchema>;

export default function NewCoursePage() {
  const { mutate: createCourse, isPending } = useCreateCourse();

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { data } = await publicApi.get("/courses/categories/");
      return data.data as Array<{ id: string; name: string }>;
    },
    staleTime: Infinity,
  });

  const { data: levels } = useQuery({
    queryKey: ["levels"],
    queryFn: async () => {
      const { data } = await publicApi.get("/courses/levels/");
      return data.data as Array<{ id: string; name: string }>;
    },
    staleTime: Infinity,
  });

  const { data: languages } = useQuery({
    queryKey: ["languages"],
    queryFn: async () => {
      const { data } = await publicApi.get("/courses/languages/");
      return data.data as Array<{ id: string; name: string }>;
    },
    staleTime: Infinity,
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
    defaultValues: { is_free: false, certificate_available: false, price: 0 },
  });

  const isFree = watch("is_free");

  const onSubmit = (data: CourseFormData) => {
    createCourse({
      title: data.title,
      subtitle: data.subtitle,
      description: data.description,
      category_id: data.category_id,
      level_id: data.level_id,
      language_id: data.language_id,
      price: isFree ? 0 : data.price,
      discount_price: data.discount_price,
      is_free: data.is_free,
      certificate_available: data.certificate_available,
      thumbnail: data.thumbnail,
      promo_video_url: data.promo_video_url,
    });
  };

  return (
    <div className="max-w-3xl space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/instructor/courses">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">
            Create New Course
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Fill in the details below to get started
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* ── Basic info ─── */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="h-5 w-5 text-muted-foreground" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <Input
              label="Course title *"
              placeholder="e.g. Complete Python Bootcamp for Beginners"
              error={errors.title?.message}
              hint="At least 5 characters. Make it descriptive and searchable."
              {...register("title")}
            />
            <Input
              label="Subtitle"
              placeholder="A short tagline for your course"
              error={errors.subtitle?.message}
              {...register("subtitle")}
            />
            <div>
              <label className="text-sm font-medium text-foreground">
                Description *
              </label>
              <textarea
                className="mt-1.5 flex min-h-36 w-full resize-none rounded-xl border border-input bg-background px-3.5 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Describe what students will learn in this course. Minimum 20 characters."
                {...register("description")}
              />
              {errors.description && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.description.message}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* ── Categorisation ─── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Categorisation</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            {/* Category */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">Category *</label>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                {...register("category_id")}
              >
                <option value="">Select category</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              {errors.category_id && (
                <p className="text-xs text-destructive">
                  {errors.category_id.message}
                </p>
              )}
            </div>

            {/* Level */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">Level</label>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                {...register("level_id")}
              >
                <option value="">Select level</option>
                {levels?.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium">Language</label>
              <select
                className="h-10 rounded-xl border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                {...register("language_id")}
              >
                <option value="">Select language</option>
                {languages?.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* ── Pricing ─── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Pricing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Free toggle */}
            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="text-sm font-semibold">Free course</p>
                <p className="text-xs text-muted-foreground">
                  Make this course available to everyone at no cost
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={isFree}
                onClick={() => setValue("is_free", !isFree)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  isFree ? "bg-brand-500" : "bg-slate-200 dark:bg-slate-700"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    isFree ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {!isFree && (
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Price (USD)"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="29.99"
                  error={errors.price?.message}
                  {...register("price")}
                />
                <Input
                  label="Discount price (USD)"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="19.99"
                  hint="Optional. Must be less than price."
                  {...register("discount_price")}
                />
              </div>
            )}

            {/* Certificate */}
            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="text-sm font-semibold">Certificate of completion</p>
                <p className="text-xs text-muted-foreground">
                  Students receive a certificate when they finish the course
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={watch("certificate_available")}
                onClick={() =>
                  setValue("certificate_available", !watch("certificate_available"))
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  watch("certificate_available")
                    ? "bg-brand-500"
                    : "bg-slate-200 dark:bg-slate-700"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    watch("certificate_available") ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </CardContent>
        </Card>

        {/* ── Media ─── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Media</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Thumbnail URL"
              placeholder="https://res.cloudinary.com/…"
              hint="Recommended: 1280×720px. Upload to Cloudinary and paste the URL."
              error={errors.thumbnail?.message}
              {...register("thumbnail")}
            />
            <Input
              label="Promo video URL"
              placeholder="https://www.youtube.com/watch?v=…"
              hint="YouTube link shown on the course detail page."
              error={errors.promo_video_url?.message}
              {...register("promo_video_url")}
            />
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" type="button" asChild>
            <Link href="/instructor/courses">Cancel</Link>
          </Button>
          <Button type="submit" isLoading={isPending} loadingText="Creating…" size="lg">
            Create course
          </Button>
        </div>
      </form>
    </div>
  );
}
