// ============================================================
// app/student/certificates/page.tsx
// ============================================================
"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Award, Download, ExternalLink, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import CertificateService from "@/services/certificateService";
import { formatDate } from "@/lib/utils";

export default function CertificatesPage() {
  const {
    data: certificates,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["certificates", "my"],
    queryFn: CertificateService.getMyCertificates,
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold lg:text-3xl">My Certificates</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Certificates of completion earned from your courses
        </p>
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {isLoading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-2xl border border-border p-6 space-y-4">
              <Skeleton className="h-12 w-12 rounded-xl" />
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex gap-2">
                <Skeleton className="h-8 flex-1 rounded-lg" />
                <Skeleton className="h-8 flex-1 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoading && !error && certificates?.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border py-24 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/30">
            <Award className="h-8 w-8 text-amber-500" />
          </div>
          <div>
            <p className="font-semibold text-lg">No certificates yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Complete a course to earn your first certificate!
            </p>
          </div>
          <Button size="sm" asChild>
            <Link href="/student/courses">View my courses</Link>
          </Button>
        </div>
      )}

      {!isLoading && certificates && certificates.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {certificates.map((cert) => (
            <div
              key={cert.id}
              className="group relative flex flex-col gap-5 rounded-2xl border border-border bg-card p-6 transition-shadow hover:shadow-md"
            >
              {/* Certificate icon */}
              <div className="flex items-start justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-sm">
                  <Award className="h-6 w-6 text-white" />
                </div>
                <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 dark:bg-emerald-950/30">
                  <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                  <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    Verified
                  </span>
                </div>
              </div>

              {/* Info */}
              <div className="space-y-1.5 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Certificate of Completion
                </p>
                <p className="font-semibold text-foreground leading-snug">
                  {cert.certificate_number}
                </p>
                <p className="text-sm text-muted-foreground">
                  Issued {formatDate(cert.issue_date)}
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {cert.certificate_url && (
                  <Button size="sm" variant="outline" className="flex-1 gap-1.5" asChild>
                    <a
                      href={CertificateService.getDownloadUrl(cert.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </a>
                  </Button>
                )}
                <Button size="sm" variant="brand-outline" className="flex-1 gap-1.5" asChild>
                  <Link href={`/certificates/verify/${cert.id}`}>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Verify
                  </Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
