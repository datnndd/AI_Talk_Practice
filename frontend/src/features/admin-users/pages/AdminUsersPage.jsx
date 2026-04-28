import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowClockwise,
  CrownSimple,
  FloppyDiskBack,
  GraduationCap,
  MagnifyingGlass,
  ProhibitInset,
  Sparkle,
  SquaresFour,
  UserList,
} from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminUsersApi } from "@/features/admin-users/api/adminUsersApi";
import AdminShell from "@/features/admin-scenarios/components/AdminShell";

const DEFAULT_FILTERS = {
  search: "",
  status: "active",
  role: "",
  subscription_tier: "",
  page: 1,
  page_size: 12,
};

const adminNavItems = [
  { label: "User Directory", icon: UserList, to: "/admin/users" },
  { label: "Scenarios", icon: SquaresFour, to: "/admin/scenarios" },
  { label: "Curriculum", icon: GraduationCap, to: "/admin/curriculum" },
  { label: "Payments", icon: CrownSimple, to: "/admin/payments" },
];

const LANGUAGE_OPTIONS = [
  { value: "vi", label: "Vietnamese" },
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "zh", label: "Chinese" },
  { value: "fr", label: "French" },
];

const LEVEL_OPTIONS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "A1", label: "A1" },
  { value: "A2", label: "A2" },
  { value: "B1", label: "B1" },
  { value: "B2", label: "B2" },
  { value: "C1", label: "C1" },
  { value: "C2", label: "C2" },
];

const PLAN_OPTIONS = [
  { value: "FREE", label: "Free" },
  { value: "PRO", label: "Pro" },
  { value: "ENTERPRISE", label: "Enterprise" },
];

const toCommaSeparated = (value) => {
  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "string") {
    return value;
  }

  return "";
};

const parseCommaSeparated = (value) => {
  const entries = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return entries.length ? entries : null;
};

const formatDateTime = (value) => {
  if (!value) return "Not available";
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const buildUpdatePayload = (formData) => ({
  display_name: formData.display_name.trim() || null,
  age: formData.age === "" ? null : Number(formData.age),
  native_language: formData.native_language || null,
  target_language: formData.target_language || null,
  level: formData.level || null,
  daily_goal: formData.daily_goal === "" ? null : Number(formData.daily_goal),
  learning_purpose: parseCommaSeparated(formData.learning_purpose),
  favorite_topics: parseCommaSeparated(formData.favorite_topics),
  main_challenge: formData.main_challenge.trim() || null,
});

const toFormState = (user) => ({
  display_name: user?.display_name ?? "",
  age: user?.age ?? "",
  native_language: user?.native_language ?? "vi",
  target_language: user?.target_language ?? "en",
  level: user?.level ?? "intermediate",
  daily_goal: user?.daily_goal ?? "",
  learning_purpose: toCommaSeparated(user?.learning_purpose),
  favorite_topics: toCommaSeparated(user?.favorite_topics),
  main_challenge: user?.main_challenge ?? "",
});

const getRoleBadge = (user) => (user?.is_admin ? "Admin" : "Learner");
const getPlanBadge = (user) => String(user?.subscription?.tier || "FREE").toUpperCase();
const getStatusBadge = (user) => (user?.deleted_at ? "Inactive" : "Active");

const FieldLabel = ({ children }) => (
  <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
    {children}
  </label>
);

const AdminUsersPage = () => {
  const { user: currentUser } = useAuth();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState("FREE");
  const [formData, setFormData] = useState(() => toFormState(null));
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isRunningAction, setIsRunningAction] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === "page" ? value : 1,
    }));
  };

  const loadUsers = useCallback(async () => {
    setIsLoadingList(true);
    setError("");
    try {
      const data = await adminUsersApi.listUsers(filters);
      setUsers(data.items);
      setTotal(data.total);
      setSelectedUserId((current) => {
        if (current && data.items.some((item) => item.id === current)) {
          return current;
        }
        return data.items[0]?.id || null;
      });
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || "Failed to load users.");
    } finally {
      setIsLoadingList(false);
    }
  }, [filters]);

  const loadUserDetail = useCallback(async (userId) => {
    if (!userId) {
      setSelectedUser(null);
      return;
    }

    setIsLoadingDetail(true);
    try {
      const data = await adminUsersApi.getUser(userId);
      setSelectedUser(data);
    } catch (detailError) {
      setError(detailError?.response?.data?.detail || "Failed to load user detail.");
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    void loadUserDetail(selectedUserId);
  }, [loadUserDetail, selectedUserId]);

  useEffect(() => {
    setFormData(toFormState(selectedUser));
  }, [selectedUser]);

  useEffect(() => {
    setSelectedPlan(getPlanBadge(selectedUser));
  }, [selectedUser]);

  const currentPayload = useMemo(() => buildUpdatePayload(formData), [formData]);
  const baselinePayload = useMemo(() => buildUpdatePayload(toFormState(selectedUser)), [selectedUser]);
  const hasFormChanges = JSON.stringify(currentPayload) !== JSON.stringify(baselinePayload);
  const hasPlanChange = selectedPlan !== getPlanBadge(selectedUser);
  const isSelfSelected = selectedUser?.id === currentUser?.id;
  const totalPages = Math.max(1, Math.ceil(total / filters.page_size));

  const handleSave = async (event) => {
    event.preventDefault();
    if (!selectedUserId || !hasFormChanges) return;

    setIsSaving(true);
    setError("");
    try {
      const updatedUser = await adminUsersApi.updateUser(selectedUserId, currentPayload);
      setSelectedUser(updatedUser);
      setUsers((current) => current.map((item) => (item.id === updatedUser.id ? updatedUser : item)));
      setNotice("User profile updated.");
    } catch (saveError) {
      setError(saveError?.response?.data?.detail || "Failed to save user profile.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefresh = async () => {
    await loadUsers();
    if (selectedUserId) {
      await loadUserDetail(selectedUserId);
    }
  };

  const runAction = async (request, successMessage) => {
    if (!selectedUserId) return;

    setIsRunningAction(true);
    setError("");
    try {
      const updatedUser = await request(selectedUserId);
      setSelectedUser(updatedUser);
      setNotice(successMessage);
      await loadUsers();
      await loadUserDetail(updatedUser.id);
    } catch (actionError) {
      setError(actionError?.response?.data?.detail || "Unable to apply admin action.");
    } finally {
      setIsRunningAction(false);
    }
  };

  return (
    <AdminShell
      title="User Operations"
      subtitle="Search learners, inspect account state, edit profile metadata, and control operational access without leaving the admin workspace."
      navItems={adminNavItems}
    >
      <div className="space-y-6">
        {(notice || error) && (
          <div
            className={`rounded-[26px] px-5 py-4 text-sm font-semibold ${
              error
                ? "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
            }`}
          >
            {error || notice}
          </div>
        )}

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]" id="user-directory">
          <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">User Directory</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Accounts & Roles</h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  void handleRefresh();
                }}
                className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
              >
                <ArrowClockwise size={16} />
                Refresh
              </button>
            </div>

            <div className="mt-5 grid gap-3 xl:grid-cols-[minmax(0,1fr)_160px_160px_170px]">
              <label className="relative block">
                <MagnifyingGlass size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  value={filters.search}
                  onChange={(event) => updateFilter("search", event.target.value)}
                  placeholder="Search email or display name..."
                  className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-11 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <select
                value={filters.status}
                onChange={(event) => updateFilter("status", event.target.value)}
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="">All status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>

              <select
                value={filters.role}
                onChange={(event) => updateFilter("role", event.target.value)}
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="">All roles</option>
                <option value="learner">Learners</option>
                <option value="admin">Admins</option>
              </select>

              <select
                value={filters.subscription_tier}
                onChange={(event) => updateFilter("subscription_tier", event.target.value)}
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="">All plans</option>
                <option value="FREE">Free</option>
                <option value="PRO">Pro</option>
                <option value="ENTERPRISE">Enterprise</option>
              </select>
            </div>

            <div className="mt-5 overflow-hidden rounded-[26px] border border-zinc-200 dark:border-zinc-800">
              <div className="grid grid-cols-[minmax(0,1.6fr)_120px_120px_120px_160px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <span>User</span>
                <span>Role</span>
                <span>Plan</span>
                <span>Status</span>
                <span className="text-right">Updated</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingList && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading users...</div>
                )}

                {!isLoadingList && users.length === 0 && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">No users matched the current filters.</div>
                )}

                {!isLoadingList && users.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedUserId(item.id)}
                    className={`grid w-full grid-cols-[minmax(0,1.6fr)_120px_120px_120px_160px] gap-3 px-4 py-4 text-left text-sm transition ${
                      selectedUserId === item.id ? "bg-primary/5 dark:bg-primary/10" : ""
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-zinc-900 dark:text-zinc-100">
                        {item.display_name || item.email}
                      </p>
                      <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">{item.email}</p>
                    </div>
                    <div className="flex items-center">
                      <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                        item.is_admin
                          ? "bg-primary/10 text-primary dark:bg-primary/15 dark:text-white"
                          : "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                      }`}>
                        {getRoleBadge(item)}
                      </span>
                    </div>
                    <div className="flex items-center text-zinc-600 dark:text-zinc-300">{getPlanBadge(item)}</div>
                    <div className="flex items-center">
                      <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                        item.deleted_at
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
                          : "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                      }`}>
                        {getStatusBadge(item)}
                      </span>
                    </div>
                    <div className="flex items-center justify-end text-xs text-zinc-500 dark:text-zinc-400">
                      {formatDateTime(item.updated_at)}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
              <span>
                Page {filters.page} / {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={filters.page <= 1}
                  onClick={() => updateFilter("page", filters.page - 1)}
                  className="rounded-2xl border border-zinc-200 px-4 py-2 font-semibold transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={filters.page >= totalPages}
                  onClick={() => updateFilter("page", filters.page + 1)}
                  className="rounded-2xl border border-zinc-200 px-4 py-2 font-semibold transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <section className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">User Detail</p>
              {isLoadingDetail && <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">Loading detail...</p>}
              {!isLoadingDetail && !selectedUser && (
                <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">Select a user to inspect the account.</p>
              )}
              {!isLoadingDetail && selectedUser && (
                <div className="mt-4 space-y-4">
                  <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Identity</p>
                    <p className="mt-2 text-sm font-semibold">{selectedUser.display_name || "No display name"}</p>
                    <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{selectedUser.email}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Role & status</p>
                      <p className="mt-2 text-sm font-semibold">{getRoleBadge(selectedUser)}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{getStatusBadge(selectedUser)}</p>
                    </div>
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Subscription</p>
                      <p className="mt-2 text-sm font-semibold">{getPlanBadge(selectedUser)}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                        {selectedUser.subscription?.status || "inactive"}
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Languages</p>
                      <p className="mt-2 text-sm font-semibold">
                        {selectedUser.native_language || "N/A"} → {selectedUser.target_language || "N/A"}
                      </p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">Level: {selectedUser.level || "Not set"}</p>
                    </div>
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Timeline</p>
                      <p className="mt-2 text-sm font-semibold">{formatDateTime(selectedUser.created_at)}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                        Updated {formatDateTime(selectedUser.updated_at)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </section>

            <section className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Edit Profile</p>
              <form className="mt-4 space-y-4" onSubmit={handleSave}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Display Name</FieldLabel>
                    <input
                      value={formData.display_name}
                      onChange={(event) => setFormData((current) => ({ ...current, display_name: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    />
                  </div>
                  <div>
                    <FieldLabel>Age</FieldLabel>
                    <input
                      type="number"
                      min="1"
                      max="120"
                      value={formData.age}
                      onChange={(event) => setFormData((current) => ({ ...current, age: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Native Language</FieldLabel>
                    <select
                      value={formData.native_language}
                      onChange={(event) => setFormData((current) => ({ ...current, native_language: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    >
                      {LANGUAGE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <FieldLabel>Target Language</FieldLabel>
                    <select
                      value={formData.target_language}
                      onChange={(event) => setFormData((current) => ({ ...current, target_language: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    >
                      {LANGUAGE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Level</FieldLabel>
                    <select
                      value={formData.level}
                      onChange={(event) => setFormData((current) => ({ ...current, level: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    >
                      {LEVEL_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <FieldLabel>Daily Goal</FieldLabel>
                    <input
                      type="number"
                      min="1"
                      max="1440"
                      value={formData.daily_goal}
                      onChange={(event) => setFormData((current) => ({ ...current, daily_goal: event.target.value }))}
                      className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                    />
                  </div>
                </div>

                <div>
                  <FieldLabel>Favorite Topics</FieldLabel>
                  <input
                    value={formData.favorite_topics}
                    onChange={(event) => setFormData((current) => ({ ...current, favorite_topics: event.target.value }))}
                    placeholder="travel, interview, networking"
                    className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>

                <div>
                  <FieldLabel>Learning Purpose</FieldLabel>
                  <input
                    value={formData.learning_purpose}
                    onChange={(event) => setFormData((current) => ({ ...current, learning_purpose: event.target.value }))}
                    placeholder="travel, meetings, study abroad"
                    className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>

                <div>
                  <FieldLabel>Main Challenge</FieldLabel>
                  <textarea
                    value={formData.main_challenge}
                    onChange={(event) => setFormData((current) => ({ ...current, main_challenge: event.target.value }))}
                    className="min-h-[110px] w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <button
                    type="submit"
                    disabled={!selectedUserId || !hasFormChanges || isSaving}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <FloppyDiskBack size={16} />
                    Save Changes
                  </button>
                  <button
                    type="button"
                    disabled={!selectedUser}
                    onClick={() => {
                      setFormData(toFormState(selectedUser));
                      setError("");
                    }}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <ArrowClockwise size={16} />
                    Reset Form
                  </button>
                </div>
              </form>
            </section>

            <section className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Admin Actions</p>
              <div className="mt-4 grid gap-3">
                <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                  <div className="flex flex-col gap-3">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">
                        Subscription Plan
                      </p>
                      <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                        Apply a plan change directly from admin controls.
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
                      <select
                        value={selectedPlan}
                        onChange={(event) => setSelectedPlan(event.target.value)}
                        disabled={!selectedUserId || isRunningAction}
                        className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
                      >
                        {PLAN_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>

                      <button
                        type="button"
                        disabled={!selectedUserId || isRunningAction || !hasPlanChange}
                        onClick={() => {
                          void runAction(
                            (userId) => adminUsersApi.updateSubscription(userId, { tier: selectedPlan }),
                            `Subscription updated to ${selectedPlan}.`,
                          );
                        }}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-black text-primary transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-primary/20 dark:bg-primary/15 dark:text-white"
                      >
                        <CrownSimple size={16} weight="fill" />
                        Update Plan
                      </button>
                    </div>

                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      Current plan: <span className="font-semibold">{getPlanBadge(selectedUser)}</span>
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={!selectedUserId || isRunningAction || isSelfSelected}
                  onClick={() => {
                    void runAction(
                      adminUsersApi.toggleAdmin,
                      selectedUser?.is_admin ? "Admin access removed." : "Admin access granted.",
                    );
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-zinc-950 px-4 py-3 text-sm font-black text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-white dark:text-zinc-950"
                >
                  <Sparkle size={16} />
                  {selectedUser?.is_admin ? "Remove Admin Access" : "Grant Admin Access"}
                </button>

                <button
                  type="button"
                  disabled={!selectedUserId || isRunningAction || isSelfSelected}
                  onClick={() => {
                    const request = selectedUser?.deleted_at ? adminUsersApi.restoreUser : adminUsersApi.deactivateUser;
                    const message = selectedUser?.deleted_at ? "User restored." : "User deactivated.";
                    void runAction(request, message);
                  }}
                  className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-black transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 ${
                    selectedUser?.deleted_at
                      ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/10"
                      : "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300"
                  }`}
                >
                  <ProhibitInset size={16} />
                  {selectedUser?.deleted_at ? "Restore User" : "Deactivate User"}
                </button>

                {isSelfSelected ? (
                  <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
                    Self-protection is enabled. Your own admin access and account status cannot be changed here.
                  </p>
                ) : null}
              </div>
            </section>
          </div>
        </section>
      </div>
    </AdminShell>
  );
};

export default AdminUsersPage;
