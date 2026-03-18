// ============================================================
// app/admin/users/page.tsx
// ============================================================
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, UserCheck, UserX, MoreHorizontal, Users } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar";
import {
  Dropdown, DropdownTrigger, DropdownContent,
  DropdownItem, DropdownSeparator, DropdownLabel,
} from "@/components/ui/Dropdown";
import { TableRowSkeleton } from "@/components/common/LoadingSpinner";
import { QueryError } from "@/components/common/ErrorBoundary";
import AdminService from "@/services/adminService";
import { formatDate, toInitials, extractApiError } from "@/lib/utils";
import type { User } from "@/types/auth";

type RoleFilter = "all" | "student" | "instructor";

const ROLE_TABS: { value: RoleFilter; label: string }[] = [
  { value: "all", label: "All users" },
  { value: "student", label: "Students" },
  { value: "instructor", label: "Instructors" },
];

const QUERY_MAP: Record<RoleFilter, () => Promise<{ count: number; results: User[] }>> = {
  all: AdminService.getUsers,
  student: AdminService.getStudents,
  instructor: AdminService.getInstructors,
};

export default function AdminUsersPage() {
  const [tab, setTab] = useState<RoleFilter>("all");
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin", "users", tab],
    queryFn: QUERY_MAP[tab],
  });

  const { mutate: activate } = useMutation({
    mutationFn: (id: string) => AdminService.activateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      toast.success("User activated.");
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const { mutate: deactivate } = useMutation({
    mutationFn: (id: string) => AdminService.deactivateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      toast.success("User deactivated.");
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const filtered = data?.results.filter(
    (u) =>
      !search ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
      (u.username ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl">
            User Management
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.count ?? 0} users total
          </p>
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex rounded-xl border border-border overflow-hidden">
          {ROLE_TABS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setTab(value)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                tab === value
                  ? "bg-purple-600 text-white"
                  : "text-muted-foreground hover:bg-slate-50 dark:hover:bg-slate-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <Input
          placeholder="Search by name, email or username…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
          containerClassName="max-w-sm"
        />
      </div>

      {error && <QueryError error={error as Error} onRetry={refetch} />}

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-slate-50 dark:bg-slate-800/50">
            <tr>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                User
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hidden sm:table-cell">
                Role
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hidden md:table-cell">
                Joined
              </th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Status
              </th>
              <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRowSkeleton key={i} cols={5} />
              ))
            ) : !filtered?.length ? (
              <tr>
                <td colSpan={5} className="py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <Users className="h-10 w-10 text-slate-300" />
                    <p className="text-sm text-muted-foreground">
                      {search ? "No users match your search" : "No users found"}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((user) => (
                <tr
                  key={user.id}
                  className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  {/* User */}
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-9 w-9 shrink-0">
                        <AvatarImage src={user.profile?.avatar ?? ""} />
                        <AvatarFallback className="text-xs">
                          {toInitials(
                            `${user.first_name} ${user.last_name}` || user.email
                          )}
                        </AvatarFallback>
                      </Avatar>
                      <div className="min-w-0">
                        <p className="font-semibold text-foreground truncate">
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </td>

                  {/* Role */}
                  <td className="px-5 py-4 hidden sm:table-cell">
                    <Badge
                      variant={
                        user.role === "admin"
                          ? "admin"
                          : user.role === "instructor"
                          ? "instructor"
                          : "student"
                      }
                    >
                      {user.role}
                    </Badge>
                  </td>

                  {/* Joined */}
                  <td className="px-5 py-4 text-muted-foreground hidden md:table-cell">
                    {formatDate(user.date_joined)}
                  </td>

                  {/* Status */}
                  <td className="px-5 py-4">
                    <Badge variant={user.is_active ? "success" : "destructive"}>
                      {user.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>

                  {/* Actions */}
                  <td className="px-5 py-4 text-right">
                    <Dropdown>
                      <DropdownTrigger asChild>
                        <Button variant="ghost" size="icon-sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownTrigger>
                      <DropdownContent align="end">
                        <DropdownLabel>Actions</DropdownLabel>
                        <DropdownSeparator />
                        {user.is_active ? (
                          <DropdownItem
                            onClick={() => deactivate(user.id)}
                            className="text-amber-600 focus:text-amber-600"
                          >
                            <UserX className="h-4 w-4" />
                            Deactivate
                          </DropdownItem>
                        ) : (
                          <DropdownItem
                            onClick={() => activate(user.id)}
                            className="text-emerald-600 focus:text-emerald-600"
                          >
                            <UserCheck className="h-4 w-4" />
                            Activate
                          </DropdownItem>
                        )}
                      </DropdownContent>
                    </Dropdown>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
