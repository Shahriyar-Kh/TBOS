// ============================================================
// app/student/quiz/[id]/page.tsx — Quiz-taking page
// ============================================================
"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Clock, CheckCircle, XCircle, ChevronRight, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { cn } from "@/lib/utils";
import { useQuery, useMutation } from "@tanstack/react-query";
import QuizService from "@/services/quizService";
import { toast } from "sonner";

type QuizPhase = "info" | "taking" | "submitted";

export default function QuizPage() {
  const { id: lessonId } = useParams<{ id: string }>();
  const router = useRouter();
  const [phase, setPhase] = useState<QuizPhase>("info");
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [results, setResults] = useState<unknown>(null);

  // Fetch quiz by lesson id
  const { data: quizData, isLoading } = useQuery({
    queryKey: ["quiz-by-lesson", lessonId],
    queryFn: () => QuizService.listStudentQuizzes(),
  });

  // Find the quiz for this lesson
  const quiz = (quizData?.results ?? []).find(
    (q: { lesson: string | null }) => q.lesson === lessonId
  );

  // Timer countdown
  useEffect(() => {
    if (phase !== "taking" || timeLeft === null) return;
    if (timeLeft <= 0) {
      handleSubmit();
      return;
    }
    const timer = setTimeout(() => setTimeLeft((t) => (t ?? 1) - 1), 1000);
    return () => clearTimeout(timer);
  }, [phase, timeLeft]);

  const startMutation = useMutation({
    mutationFn: () => QuizService.startQuiz(quiz!.id),
    onSuccess: (data: { attempt: { id: string }; questions: unknown[] }) => {
      setAttemptId(data.attempt.id);
      if (quiz?.time_limit_minutes) {
        setTimeLeft(quiz.time_limit_minutes * 60);
      }
      setPhase("taking");
    },
    onError: () => toast.error("Could not start quiz. Please try again."),
  });

  const submitMutation = useMutation({
    mutationFn: () => QuizService.submitQuiz(quiz!.id),
    onSuccess: (data: unknown) => {
      setResults(data);
      setPhase("submitted");
    },
    onError: () => toast.error("Submission failed. Please try again."),
  });

  const answerMutation = useMutation({
    mutationFn: ({ questionId, optionId }: { questionId: string; optionId: string }) =>
      QuizService.submitAnswer(quiz!.id, { question_id: questionId, option_id: optionId }),
  });

  const handleSelectAnswer = (questionId: string, optionId: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
    answerMutation.mutate({ questionId, optionId });
  };

  const handleSubmit = useCallback(() => {
    if (!quiz) return;
    submitMutation.mutate();
  }, [quiz, submitMutation]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <LoadingSpinner label="Loading quiz…" />
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-8">
        <div className="text-center space-y-4">
          <AlertTriangle className="mx-auto h-12 w-12 text-amber-400" />
          <p className="text-lg font-semibold">Quiz not found</p>
          <Button onClick={() => router.back()} variant="outline">Go back</Button>
        </div>
      </div>
    );
  }

  const questions = (quizData as { questions?: unknown[] })?.questions ?? [];
  const answeredCount = Object.keys(answers).length;
  const progressPct = questions.length ? (answeredCount / questions.length) * 100 : 0;

  // ── Info phase ────────────────────────────────────────────
  if (phase === "info") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50">
              <CheckCircle className="h-8 w-8 text-brand-500" />
            </div>
            <CardTitle className="text-xl">{quiz.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {quiz.description && (
              <p className="text-sm text-muted-foreground text-center">{quiz.description}</p>
            )}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Questions", value: quiz.question_count ?? "—" },
                { label: "Pass mark", value: `${quiz.passing_score}%` },
                { label: "Max attempts", value: quiz.max_attempts },
                {
                  label: "Time limit",
                  value: quiz.time_limit_minutes
                    ? `${quiz.time_limit_minutes} min`
                    : "Unlimited",
                },
              ].map(({ label, value }) => (
                <div
                  key={label}
                  className="rounded-xl bg-slate-50 p-3 text-center border border-border"
                >
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="mt-0.5 text-lg font-bold text-foreground">{value}</p>
                </div>
              ))}
            </div>
            <Button
              className="w-full"
              size="lg"
              onClick={() => startMutation.mutate()}
              isLoading={startMutation.isPending}
              loadingText="Starting…"
            >
              Start quiz
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" className="w-full" onClick={() => router.back()}>
              Cancel
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Taking phase ──────────────────────────────────────────
  if (phase === "taking") {
    return (
      <div className="min-h-screen bg-slate-50 pb-20">
        {/* Sticky header */}
        <div className="sticky top-0 z-10 border-b border-border bg-white px-6 py-3 shadow-sm">
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold">{quiz.title}</span>
              <Badge variant="secondary">
                {answeredCount}/{questions.length} answered
              </Badge>
            </div>
            <div className="flex items-center gap-4">
              {timeLeft !== null && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold",
                    timeLeft < 60
                      ? "bg-red-100 text-red-600"
                      : timeLeft < 300
                      ? "bg-amber-100 text-amber-600"
                      : "bg-slate-100 text-slate-600"
                  )}
                >
                  <Clock className="h-4 w-4" />
                  {formatTime(timeLeft)}
                </div>
              )}
              <Button
                size="sm"
                onClick={handleSubmit}
                isLoading={submitMutation.isPending}
                loadingText="Submitting…"
              >
                Submit quiz
              </Button>
            </div>
          </div>
          <div className="mx-auto mt-2 max-w-3xl">
            <Progress value={progressPct} className="h-1" />
          </div>
        </div>

        {/* Questions */}
        <div className="mx-auto max-w-3xl space-y-6 px-6 pt-8">
          {questions.map((q: { id: string; question_text: string; points: number; options: Array<{ id: string; option_text: string }> }, idx: number) => (
            <Card key={q.id}>
              <CardContent className="p-6">
                <div className="mb-4 flex items-start justify-between gap-4">
                  <p className="font-semibold leading-snug">
                    <span className="mr-2 text-muted-foreground">Q{idx + 1}.</span>
                    {q.question_text}
                  </p>
                  <Badge variant="secondary" className="shrink-0 text-[10px]">
                    {q.points} pt{q.points !== 1 ? "s" : ""}
                  </Badge>
                </div>
                <div className="space-y-2">
                  {q.options.map((opt: { id: string; option_text: string }) => {
                    const selected = answers[q.id] === opt.id;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => handleSelectAnswer(q.id, opt.id)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-xl border-2 px-4 py-3 text-left text-sm transition-all",
                          selected
                            ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950/30 dark:text-brand-300"
                            : "border-border hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                            selected
                              ? "border-brand-500 bg-brand-500"
                              : "border-slate-300"
                          )}
                        >
                          {selected && (
                            <div className="h-2 w-2 rounded-full bg-white" />
                          )}
                        </div>
                        {opt.option_text}
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // ── Submitted / Results phase ─────────────────────────────
  const res = results as {
    passed: boolean;
    percentage: string;
    score: number;
    total_points: number;
    correct_answers: number;
    total_questions: number;
  } | null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div
            className={cn(
              "mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full",
              res?.passed
                ? "bg-emerald-100 dark:bg-emerald-950/30"
                : "bg-red-100 dark:bg-red-950/30"
            )}
          >
            {res?.passed ? (
              <CheckCircle className="h-10 w-10 text-emerald-500" />
            ) : (
              <XCircle className="h-10 w-10 text-red-500" />
            )}
          </div>
          <CardTitle className="text-2xl">
            {res?.passed ? "Quiz Passed! 🎉" : "Not Quite There"}
          </CardTitle>
          <p className="text-muted-foreground">
            {res?.passed
              ? "Great work! You've passed this quiz."
              : `You needed ${quiz.passing_score}% to pass. Review the material and try again.`}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Score breakdown */}
          <div className="rounded-2xl bg-slate-50 p-5 space-y-4 dark:bg-slate-900">
            <div className="text-center">
              <p className="font-display text-5xl font-bold text-foreground">
                {res?.percentage ?? "0"}%
              </p>
              <p className="text-sm text-muted-foreground mt-1">Final score</p>
            </div>
            <Progress
              value={parseFloat(res?.percentage ?? "0")}
              indicatorClassName={res?.passed ? "bg-emerald-500" : "bg-red-500"}
              showLabel
            />
            <div className="grid grid-cols-2 gap-3 text-center text-sm">
              <div className="rounded-xl bg-white p-3 border border-border dark:bg-slate-800">
                <p className="font-bold text-lg">{res?.correct_answers}</p>
                <p className="text-xs text-muted-foreground">Correct</p>
              </div>
              <div className="rounded-xl bg-white p-3 border border-border dark:bg-slate-800">
                <p className="font-bold text-lg">{res?.total_questions}</p>
                <p className="text-xs text-muted-foreground">Total</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={() => router.back()} className="w-full">
              Continue learning
              <ChevronRight className="h-4 w-4" />
            </Button>
            {!res?.passed && (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setPhase("info");
                  setAnswers({});
                  setAttemptId(null);
                  setResults(null);
                }}
              >
                Try again
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
