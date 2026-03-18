// ============================================================
// app/student/learn/[id]/page.tsx — Course learning player
// ============================================================
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft, ChevronRight, CheckCircle, Circle, PlayCircle,
  BookOpen, FileText, ClipboardList, Menu, X, Lock, Award,
  ChevronDown, ChevronUp,
} from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import { useEnrollmentProgress, useMarkLessonComplete } from "@/hooks/useEnrollments";
import { useAuthStore } from "@/store/authStore";
import { cn, parseProgress } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import EnrollmentService from "@/services/enrollmentService";
import { QUERY_KEYS } from "@/config/constants";

interface Lesson {
  id: string;
  title: string;
  lesson_type: "video" | "quiz" | "assignment" | "article";
  order: number;
  is_preview: boolean;
  duration_seconds: number;
  article_content?: string;
  section_id: string;
}

interface Section {
  id: string;
  title: string;
  order: number;
  lessons: Lesson[];
}

interface ProgressRecord {
  lesson_id: string;
  is_completed: boolean;
  completed_at: string | null;
}

const LESSON_TYPE_ICON = {
  video: <PlayCircle className="h-3.5 w-3.5" />,
  quiz: <ClipboardList className="h-3.5 w-3.5" />,
  assignment: <FileText className="h-3.5 w-3.5" />,
  article: <BookOpen className="h-3.5 w-3.5" />,
};

export default function LearnPage() {
  const { id: enrollmentId } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const videoRef = useRef<HTMLIFrameElement>(null);

  // Fetch enrollment + progress
  const {
    data: progressData,
    isLoading: progressLoading,
    error: progressError,
    refetch: refetchProgress,
  } = useEnrollmentProgress(enrollmentId);

  // Fetch curriculum
  const { data: curriculumData, isLoading: curriculumLoading } = useQuery({
    queryKey: ["curriculum", enrollmentId],
    queryFn: async () => {
      const progress = await EnrollmentService.getProgress(enrollmentId);
      return progress;
    },
    enabled: !!enrollmentId,
  });

  const { mutate: markComplete, isPending: markingComplete } = useMarkLessonComplete();

  // Build a flat list of all lessons from sections for navigation
  const allLessons: Lesson[] = [];
  const sections: Section[] = progressData?.sections ?? curriculumData?.sections ?? [];

  sections.forEach((section: Section) => {
    section.lessons?.forEach((lesson: Lesson) => {
      allLessons.push({ ...lesson, section_id: section.id });
    });
  });

  const completedLessonIds = new Set<string>(
    (progressData?.lessons as ProgressRecord[] ?? [])
      .filter((l: ProgressRecord) => l.is_completed)
      .map((l: ProgressRecord) => l.lesson_id)
  );

  const activeLesson = activeLessonId
    ? allLessons.find((l) => l.id === activeLessonId)
    : allLessons[0];

  const activeLessonIndex = activeLesson
    ? allLessons.findIndex((l) => l.id === activeLesson.id)
    : 0;

  const prevLesson = activeLessonIndex > 0 ? allLessons[activeLessonIndex - 1] : null;
  const nextLesson =
    activeLessonIndex < allLessons.length - 1
      ? allLessons[activeLessonIndex + 1]
      : null;

  // Auto-expand the section containing the active lesson
  useEffect(() => {
    if (activeLesson?.section_id) {
      setExpandedSections((s) => new Set([...s, activeLesson.section_id]));
    }
  }, [activeLesson?.section_id]);

  // Default to first incomplete lesson on load
  useEffect(() => {
    if (!activeLessonId && allLessons.length > 0) {
      const firstIncomplete = allLessons.find(
        (l) => !completedLessonIds.has(l.id)
      );
      setActiveLessonId(firstIncomplete?.id ?? allLessons[0].id);
    }
  }, [allLessons.length]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      next.has(sectionId) ? next.delete(sectionId) : next.add(sectionId);
      return next;
    });
  };

  const handleMarkComplete = () => {
    if (!activeLesson) return;
    markComplete(
      { enrollmentId, lessonId: activeLesson.id },
      {
        onSuccess: () => {
          refetchProgress();
          if (nextLesson) setActiveLessonId(nextLesson.id);
        },
      }
    );
  };

  const isLessonCompleted = (lessonId: string) =>
    completedLessonIds.has(lessonId);

  const overallProgress = parseProgress(
    progressData?.progress_percentage ?? "0"
  );

  if (progressLoading || curriculumLoading) {
    return <LearnPageSkeleton />;
  }

  if (progressError) {
    return (
      <QueryError
        error={progressError as Error}
        onRetry={refetchProgress}
      />
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-white">
      {/* ── Sidebar ───────────────────────────────── */}
      <aside
        className={cn(
          "flex flex-col border-r border-slate-800 bg-slate-900 transition-all duration-300",
          sidebarOpen ? "w-80 shrink-0" : "w-0 overflow-hidden"
        )}
      >
        {/* Sidebar header */}
        <div className="border-b border-slate-800 p-4">
          <Link
            href="/student/courses"
            className="mb-3 flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back to my courses
          </Link>
          <h2 className="line-clamp-2 text-sm font-semibold leading-snug">
            {progressData?.course_title ?? "Course"}
          </h2>
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>
                {progressData?.completed_lessons_count ?? 0}/
                {progressData?.total_lessons_count ?? 0} lessons
              </span>
              <span className="font-medium text-brand-400">
                {overallProgress}%
              </span>
            </div>
            <Progress
              value={overallProgress}
              className="h-1.5 bg-slate-700"
              indicatorClassName="bg-brand-500"
            />
          </div>
        </div>

        {/* Curriculum */}
        <div className="flex-1 overflow-y-auto py-2">
          {sections.map((section: Section) => {
            const isExpanded = expandedSections.has(section.id);
            const completedInSection = section.lessons?.filter((l: Lesson) =>
              isLessonCompleted(l.id)
            ).length ?? 0;
            const totalInSection = section.lessons?.length ?? 0;

            return (
              <div key={section.id} className="border-b border-slate-800/50">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="flex w-full items-start gap-2 px-4 py-3 text-left hover:bg-slate-800/50 transition-colors"
                >
                  <div className="mt-0.5 shrink-0 text-slate-400">
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-200 leading-snug">
                      {section.title}
                    </p>
                    <p className="mt-0.5 text-[10px] text-slate-500">
                      {completedInSection}/{totalInSection} completed
                    </p>
                  </div>
                </button>

                {isExpanded && (
                  <ul className="pb-1">
                    {section.lessons?.map((lesson: Lesson) => {
                      const completed = isLessonCompleted(lesson.id);
                      const isActive = activeLesson?.id === lesson.id;
                      return (
                        <li key={lesson.id}>
                          <button
                            onClick={() => setActiveLessonId(lesson.id)}
                            className={cn(
                              "flex w-full items-start gap-3 px-4 py-2.5 text-left transition-colors",
                              isActive
                                ? "bg-brand-600/20 text-brand-300"
                                : "hover:bg-slate-800/60 text-slate-400 hover:text-slate-200"
                            )}
                          >
                            {/* Completion indicator */}
                            <div className="mt-0.5 shrink-0">
                              {completed ? (
                                <CheckCircle className="h-4 w-4 text-emerald-400" />
                              ) : (
                                <Circle className="h-4 w-4 text-slate-600" />
                              )}
                            </div>

                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium leading-snug line-clamp-2">
                                {lesson.title}
                              </p>
                              <div className="mt-1 flex items-center gap-2">
                                <span className="text-slate-500">
                                  {LESSON_TYPE_ICON[lesson.lesson_type]}
                                </span>
                                {lesson.duration_seconds > 0 && (
                                  <span className="text-[10px] text-slate-600">
                                    {Math.ceil(lesson.duration_seconds / 60)}min
                                  </span>
                                )}
                              </div>
                            </div>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </aside>

      {/* ── Main content ──────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-900 px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            {activeLesson && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">
                  {LESSON_TYPE_ICON[activeLesson.lesson_type]}
                </span>
                <span className="hidden sm:block font-medium truncate max-w-[300px]">
                  {activeLesson.title}
                </span>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => prevLesson && setActiveLessonId(prevLesson.id)}
              disabled={!prevLesson}
              className="text-slate-400 hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Prev</span>
            </Button>

            {activeLesson && !isLessonCompleted(activeLesson.id) && (
              <Button
                size="sm"
                onClick={handleMarkComplete}
                isLoading={markingComplete}
                loadingText="Marking…"
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <CheckCircle className="h-4 w-4" />
                Mark complete
              </Button>
            )}
            {activeLesson && isLessonCompleted(activeLesson.id) && (
              <Badge variant="success" className="gap-1">
                <CheckCircle className="h-3.5 w-3.5" />
                Completed
              </Badge>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => nextLesson && setActiveLessonId(nextLesson.id)}
              disabled={!nextLesson}
              className="text-slate-400 hover:text-white disabled:opacity-30"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Lesson content */}
        <main className="flex-1 overflow-y-auto">
          {!activeLesson ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <BookOpen className="mx-auto mb-4 h-16 w-16 text-slate-700" />
                <p className="text-lg font-semibold text-slate-400">
                  Select a lesson to begin
                </p>
              </div>
            </div>
          ) : activeLesson.lesson_type === "video" ? (
            <VideoLesson lesson={activeLesson} />
          ) : activeLesson.lesson_type === "article" ? (
            <ArticleLesson lesson={activeLesson} />
          ) : activeLesson.lesson_type === "quiz" ? (
            <QuizLessonPrompt lesson={activeLesson} enrollmentId={enrollmentId} />
          ) : (
            <AssignmentLessonPrompt lesson={activeLesson} />
          )}
        </main>

        {/* Course completion banner */}
        {overallProgress === 100 && (
          <div className="border-t border-emerald-800 bg-emerald-900/30 px-6 py-3">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Award className="h-6 w-6 text-emerald-400 shrink-0" />
                <p className="text-sm font-medium text-emerald-300">
                  🎉 Congratulations! You&apos;ve completed this course.
                </p>
              </div>
              <Button size="sm" variant="success" asChild>
                <Link href="/student/certificates">View certificate</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Video lesson renderer ─────────────────────────────────────
function VideoLesson({ lesson }: { lesson: Lesson }) {
  // The video URL should come from the lesson's associated video record.
  // We load it via the lesson video endpoint.
  const { data: videos, isLoading } = useQuery({
    queryKey: ["lesson-video", lesson.id],
    queryFn: async () => {
      const { api } = await import("@/lib/axios");
      const { data } = await api.get(`/lessons/${lesson.id}/video/`);
      return data.data as Array<{ youtube_id: string; cloudinary_url: string; source_type: string; title: string }>;
    },
  });

  const video = videos?.[0];

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* Video player */}
      <div className="relative bg-black" style={{ paddingBottom: "56.25%" }}>
        {video ? (
          video.source_type === "youtube" ? (
            <iframe
              className="absolute inset-0 h-full w-full"
              src={`https://www.youtube.com/embed/${video.youtube_id}?rel=0&modestbranding=1`}
              title={lesson.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <video
              className="absolute inset-0 h-full w-full"
              src={video.cloudinary_url}
              controls
              title={lesson.title}
            />
          )
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
            <div className="text-center">
              <PlayCircle className="mx-auto mb-3 h-16 w-16 text-slate-700" />
              <p className="text-sm text-slate-500">Video not available</p>
            </div>
          </div>
        )}
      </div>

      {/* Lesson info below player */}
      <div className="p-6 max-w-4xl">
        <h1 className="font-display text-2xl font-bold">{lesson.title}</h1>
      </div>
    </div>
  );
}

// ── Article lesson renderer ───────────────────────────────────
function ArticleLesson({ lesson }: { lesson: Lesson }) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-6 flex items-center gap-2 text-slate-400">
        <BookOpen className="h-5 w-5" />
        <span className="text-sm font-medium">Article</span>
      </div>
      <h1 className="mb-8 font-display text-3xl font-bold">{lesson.title}</h1>
      {lesson.article_content ? (
        <div
          className="prose prose-invert prose-sm max-w-none lg:prose-base"
          dangerouslySetInnerHTML={{ __html: lesson.article_content }}
        />
      ) : (
        <p className="text-slate-400">No content available for this lesson.</p>
      )}
    </div>
  );
}

// ── Quiz lesson prompt ────────────────────────────────────────
function QuizLessonPrompt({
  lesson,
  enrollmentId,
}: {
  lesson: Lesson;
  enrollmentId: string;
}) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-brand-600/20">
          <ClipboardList className="h-10 w-10 text-brand-400" />
        </div>
        <div>
          <h2 className="font-display text-2xl font-bold">{lesson.title}</h2>
          <p className="mt-2 text-slate-400">
            Ready to test your knowledge? Complete this quiz to continue.
          </p>
        </div>
        <Button size="lg" className="w-full" asChild>
          <Link href={`/student/quiz/${lesson.id}`}>
            Start quiz
            <ChevronRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}

// ── Assignment lesson prompt ──────────────────────────────────
function AssignmentLessonPrompt({ lesson }: { lesson: Lesson }) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-violet-600/20">
          <FileText className="h-10 w-10 text-violet-400" />
        </div>
        <div>
          <h2 className="font-display text-2xl font-bold">{lesson.title}</h2>
          <p className="mt-2 text-slate-400">
            Complete this assignment and submit your work for review.
          </p>
        </div>
        <Button size="lg" variant="outline" className="w-full border-slate-600 text-white hover:bg-slate-800">
          View assignment details
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ── Loading skeleton ──────────────────────────────────────────
function LearnPageSkeleton() {
  return (
    <div className="flex h-screen bg-slate-950">
      <div className="w-80 shrink-0 border-r border-slate-800 bg-slate-900 p-4 space-y-3">
        <Skeleton className="h-4 w-32 bg-slate-800" />
        <Skeleton className="h-5 w-full bg-slate-800" />
        <Skeleton className="h-2 w-full bg-slate-800 rounded-full" />
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full bg-slate-800" />
        ))}
      </div>
      <div className="flex-1 bg-black flex items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      </div>
    </div>
  );
}
