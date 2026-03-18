// ============================================================
// app/courses/page.tsx — Public course catalog
// ============================================================
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { CourseCard } from "@/components/common/CourseCard";
import { CourseCardSkeleton } from "@/components/common/LoadingSpinner";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import CourseService, { type CourseFilters } from "@/services/courseService";
import { QUERY_KEYS } from "@/config/constants";
import { cn } from "@/lib/utils";

export default function CoursesPage() {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<CourseFilters>({});
  const [page, setPage] = useState(1);

  const activeFilters: CourseFilters = {
    ...filters,
    search: search || undefined,
    page,
    page_size: 12,
  };

  const { data, isLoading, isFetching } = useQuery({
    queryKey: QUERY_KEYS.courses.list(activeFilters),
    queryFn: () => CourseService.listPublic(activeFilters),
    placeholderData: (prev) => prev,
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const { publicApi } = await import("@/lib/axios");
      const { data } = await publicApi.get("/courses/categories/");
      return data.data as Array<{ id: string; name: string; slug: string }>;
    },
    staleTime: Infinity,
  });

  const clearFilters = () => {
    setSearch("");
    setFilters({});
    setPage(1);
  };

  const hasActiveFilters = search || filters.category__slug || filters.is_free !== undefined;

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-16">
        {/* ── Header ─── */}
        <section className="border-b border-border bg-slate-50 dark:bg-slate-900/50 px-6 py-12">
          <div className="section-container">
            <h1 className="font-display text-3xl font-bold lg:text-4xl">
              Explore Courses
            </h1>
            <p className="mt-2 text-muted-foreground">
              {data?.count
                ? `${data.count.toLocaleString()} courses available`
                : "Browse our full catalog"}
            </p>

            {/* Search */}
            <div className="mt-6 flex max-w-xl gap-2">
              <Input
                placeholder="Search courses, topics, instructors…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                leftIcon={<Search className="h-4 w-4" />}
                containerClassName="flex-1"
              />
              {hasActiveFilters && (
                <Button variant="outline" size="icon" onClick={clearFilters} title="Clear filters">
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Quick filters */}
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => { setFilters((f) => ({ ...f, is_free: f.is_free ? undefined : true })); setPage(1); }}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
                  filters.is_free
                    ? "border-brand-500 bg-brand-500 text-white"
                    : "border-border text-muted-foreground hover:border-brand-500 hover:text-brand-600"
                )}
              >
                Free
              </button>
              {categories?.slice(0, 6).map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setFilters((f) => ({
                      ...f,
                      category__slug: f.category__slug === cat.slug ? undefined : cat.slug,
                    }));
                    setPage(1);
                  }}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
                    filters.category__slug === cat.slug
                      ? "border-brand-500 bg-brand-500 text-white"
                      : "border-border text-muted-foreground hover:border-brand-500 hover:text-brand-600"
                  )}
                >
                  {cat.name}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* ── Course grid ─── */}
        <section className="section-container py-10">
          {isLoading ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <CourseCardSkeleton key={i} />
              ))}
            </div>
          ) : !data?.results.length ? (
            <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
              <Search className="h-12 w-12 text-slate-300" />
              <p className="text-lg font-semibold">No courses found</p>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search or filters
              </p>
              <Button variant="outline" onClick={clearFilters}>
                Clear filters
              </Button>
            </div>
          ) : (
            <>
              <div
                className={cn(
                  "grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
                  isFetching && "opacity-70 transition-opacity"
                )}
              >
                {data.results.map((course) => (
                  <CourseCard key={course.id} course={course} />
                ))}
              </div>

              {/* Pagination */}
              {(data.next || data.previous) && (
                <div className="mt-10 flex items-center justify-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={!data.previous || isFetching}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!data.next || isFetching}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </section>
      </main>
      <Footer />
    </>
  );
}
