// ============================================================
// app/instructor/courses/[id]/page.tsx — Edit course
// ============================================================
"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Save, Eye, Send, Archive } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Badge } from "@/components/ui/Badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/Select";
import { Skeleton } from "@/components/common/LoadingSpinner";
import CourseService from "@/services/courseService";
import { extractApiError } from "@/lib/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/config/constants";

const editSchema = z.object({
  title: z.string().min(5, "Title must be at least 5 characters"),
  subtitle: z.string().max(500).optional(),
  description: z.string().min(20, "Description must be at least 20 characters"),
  thumbnail: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  promo_video_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  price: z.coerce.number().min(0),
  discount_price: z.coerce.number().min(0).optional(),
  is_free: z.boolean(),
  certificate_available: z.boolean(),
});

type EditForm = z.infer<typeof editSchema>;

export default function InstructorCourseEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: coursePage, isLoading } = useQuery({
    queryKey: ["instructor-course-edit", id],
    queryFn: async () => {
      const page = await CourseService.listInstructor();
      return page.results.find((c) => c.id === id) ?? null;
    },
    enabled: !!id,
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm<EditForm>({ resolver: zodResolver(editSchema) });

  useEffect(() => {
    if (coursePage) {
      reset({
        title: coursePage.title,
        subtitle: coursePage.subtitle ?? "",
        description: coursePage.description,
        thumbnail: coursePage.thumbnail ?? "",
        promo_video_url: coursePage.promo_video_url ?? "",
        price: parseFloat(coursePage.price) ?? 0,
        discount_price: parseFloat(coursePage.discount_price) || 0,
        is_free: coursePage.is_free,
        certificate_available: coursePage.certificate_available,
      });
    }
  }, [coursePage, reset]);

  const updateMutation = useMutation({
    mutationFn: (data: EditForm) =>
      CourseService.update(id, {
        ...data,
        price: data.price,
        discount_price: data.discount_price ?? 0,
      } as Parameters<typeof CourseService.update>[1]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.courses.instructorList });
      queryClient.invalidateQueries({ queryKey: ["instructor-course-edit", id] });
      toast.success("Course updated successfully!");
      reset(undefined, { keepValues: true });
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const publishMutation = useMutation({
    mutationFn: () => CourseService.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.courses.instructorList });
      toast.success("Course published!");
      router.push("/instructor/courses");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const archiveMutation = useMutation({
    mutationFn: () => CourseService.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.courses.instructorList });
      toast.success("Course archived.");
      router.push("/instructor/courses");
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const isFree = watch("is_free");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-48 w-full rounded-2xl" />
      </div>
    );
  }

  if (!coursePage) {
    return (
      <div className="flex flex-col items-center gap-4 py-20 text-center">
        <p className="text-muted-foreground">Course not found.</p>
        <Button variant="outline" asChild>
          <Link href="/instructor/courses">Back to courses</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon-sm" asChild>
            <Link href="/instructor/courses">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="font-display text-xl font-bold line-clamp-1">
              Edit: {coursePage.title}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge
                variant={
                  coursePage.status === "published"
                    ? "success"
                    : coursePage.status === "archived"
                    ? "secondary"
                    : "warning"
                }
                className="text-[10px] capitalize"
              >
                {coursePage.status}
              </Badge>
              {isDirty && (
                <span className="text-xs text-amber-500 font-medium">• Unsaved changes</span>
              )}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {coursePage.status === "published" && (
            <Button variant="outline" size="sm" asChild>
              <Link href={`/courses/${coursePage.slug}`} target="_blank">
                <Eye className="h-4 w-4" />
                View live
              </Link>
            </Button>
          )}
          {coursePage.status === "draft" && (
            <Button
              size="sm"
              variant="success"
              onClick={() => publishMutation.mutate()}
              isLoading={publishMutation.isPending}
              loadingText="Publishing…"
            >
              <Send className="h-4 w-4" />
              Publish
            </Button>
          )}
          {coursePage.status !== "archived" && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => archiveMutation.mutate()}
              isLoading={archiveMutation.isPending}
              className="text-muted-foreground"
            >
              <Archive className="h-4 w-4" />
              Archive
            </Button>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit((data) => updateMutation.mutate(data))} className="space-y-6">
        {/* Basic info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Title *"
              placeholder="Course title"
              error={errors.title?.message}
              {...register("title")}
            />
            <Input
              label="Subtitle"
              placeholder="A brief subtitle for the course listing"
              error={errors.subtitle?.message}
              {...register("subtitle")}
            />
            <Textarea
              label="Description *"
              placeholder="Describe what students will learn…"
              rows={6}
              error={errors.description?.message}
              {...register("description")}
            />
          </CardContent>
        </Card>

        {/* Pricing */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Pricing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="text-sm font-semibold">Free course</p>
                <p className="text-xs text-muted-foreground">Students enrol without payment</p>
              </div>
              <button
                type="button"
                onClick={() => setValue("is_free", !isFree, { shouldDirty: true })}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  isFree ? "bg-brand-500" : "bg-slate-200 dark:bg-slate-700"
                }`}
                role="switch"
                aria-checked={isFree}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform ${
                    isFree ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {!isFree && (
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Price (USD) *"
                  type="number"
                  min={0}
                  step={0.01}
                  error={errors.price?.message}
                  {...register("price")}
                />
                <Input
                  label="Discount price (USD)"
                  type="number"
                  min={0}
                  step={0.01}
                  hint="Leave 0 for no discount"
                  error={errors.discount_price?.message}
                  {...register("discount_price")}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Media */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Media</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Thumbnail URL"
              placeholder="https://res.cloudinary.com/…"
              hint="Recommended: 1280×720px"
              error={errors.thumbnail?.message}
              {...register("thumbnail")}
            />
            <Input
              label="Promo video URL"
              placeholder="https://www.youtube.com/watch?v=…"
              hint="YouTube link shown on the course detail page"
              error={errors.promo_video_url?.message}
              {...register("promo_video_url")}
            />
          </CardContent>
        </Card>

        {/* Save */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" type="button" asChild>
            <Link href="/instructor/courses">Discard changes</Link>
          </Button>
          <Button
            type="submit"
            isLoading={updateMutation.isPending}
            loadingText="Saving…"
            disabled={!isDirty}
          >
            <Save className="h-4 w-4" />
            Save changes
          </Button>
        </div>
      </form>
    </div>
  );
}
