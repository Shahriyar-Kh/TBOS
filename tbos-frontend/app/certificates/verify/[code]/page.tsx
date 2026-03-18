// ============================================================
// app/certificates/verify/[code]/page.tsx
// ============================================================
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle, XCircle, Shield, GraduationCap, Calendar, Award,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/common/LoadingSpinner";
import CertificateService from "@/services/certificateService";
import { formatDate } from "@/lib/utils";

export default function VerifyCertificatePage() {
  const { code } = useParams<{ code: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["verify-certificate", code],
    queryFn: () => CertificateService.verify(code),
    retry: false,
  });

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 dark:bg-slate-950">
      {/* Header */}
      <Link href="/" className="mb-10 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500">
          <GraduationCap className="h-5 w-5 text-white" />
        </div>
        <span className="font-display text-lg font-bold tracking-tight">
          TechBuilt<span className="text-brand-500">OS</span>
        </span>
      </Link>

      <Card className="w-full max-w-md shadow-xl">
        <CardContent className="p-8">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="mx-auto h-20 w-20 rounded-full" />
              <Skeleton className="mx-auto h-6 w-48" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4 mx-auto" />
            </div>
          ) : error || !data?.is_valid ? (
            <div className="text-center space-y-5">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/30">
                <XCircle className="h-10 w-10 text-red-500" />
              </div>
              <div>
                <h2 className="font-display text-xl font-bold text-foreground">
                  Certificate Not Found
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  This certificate could not be verified. It may be invalid or the
                  verification code is incorrect.
                </p>
              </div>
              <div className="rounded-xl bg-red-50 p-4 dark:bg-red-950/20">
                <p className="text-xs text-red-600 dark:text-red-400 font-mono break-all">
                  Code: {code}
                </p>
              </div>
              <Button variant="outline" asChild className="w-full">
                <Link href="/">Return to homepage</Link>
              </Button>
            </div>
          ) : (
            <div className="text-center space-y-6">
              {/* Valid badge */}
              <div className="relative mx-auto w-fit">
                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/30">
                  <Award className="h-12 w-12 text-emerald-500" />
                </div>
                <div className="absolute -right-1 -top-1 flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500">
                  <CheckCircle className="h-4 w-4 text-white" />
                </div>
              </div>

              <div>
                <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                  <Shield className="h-3.5 w-3.5" />
                  Verified Certificate
                </div>
                <h2 className="font-display text-2xl font-bold text-foreground">
                  Certificate of Completion
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  This certificate is authentic and issued by TechBuilt Open School
                </p>
              </div>

              {/* Certificate details */}
              <div className="rounded-2xl border border-border bg-slate-50 p-5 text-left space-y-4 dark:bg-slate-900">
                <DetailRow
                  icon={<GraduationCap className="h-4 w-4 text-slate-400" />}
                  label="Student"
                  value={data.student_name}
                />
                <DetailRow
                  icon={<Award className="h-4 w-4 text-slate-400" />}
                  label="Course completed"
                  value={data.course_title}
                />
                {data.issue_date && (
                  <DetailRow
                    icon={<Calendar className="h-4 w-4 text-slate-400" />}
                    label="Issue date"
                    value={formatDate(data.issue_date)}
                  />
                )}
              </div>

              <div className="rounded-xl bg-slate-100 px-4 py-2.5 dark:bg-slate-800">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-0.5">
                  Verification code
                </p>
                <p className="font-mono text-xs break-all text-foreground">{code}</p>
              </div>

              <Button asChild className="w-full">
                <Link href="/courses">Browse more courses</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="mt-0.5 text-sm font-semibold text-foreground">{value}</p>
      </div>
    </div>
  );
}
