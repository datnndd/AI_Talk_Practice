import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowClockwise,
  CrownSimple,
  FloppyDiskBack,
  Gift,
  MagnifyingGlass,
  ProhibitInset,
  Sparkle,
  X,
} from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminUsersApi } from "@/features/admin-users/api/adminUsersApi";
import AdminShell from "@/shared/components/admin/AdminShell";

const DEFAULT_FILTERS = {
  search: "",
  status: "active",
  role: "",
  subscription_tier: "",
  page: 1,
  page_size: 12,
};

const LEVEL_OPTIONS = [
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
  level: formData.level || null,
  learning_purpose: parseCommaSeparated(formData.learning_purpose),
  favorite_topics: parseCommaSeparated(formData.favorite_topics),
  main_challenge: formData.main_challenge.trim() || null,
});

const toFormState = (user) => ({
  display_name: user?.display_name ?? "",
  age: user?.age ?? "",
  level: user?.level ?? "A1",
  learning_purpose: toCommaSeparated(user?.learning_purpose),
  favorite_topics: toCommaSeparated(user?.favorite_topics),
  main_challenge: user?.main_challenge ?? "",
});

const getRoleBadge = (user) => (user?.is_admin ? "Admin" : "Learner");
const getPlanBadge = (user) => String(user?.subscription?.tier || "FREE").toUpperCase();
const getStatusBadge = (user) => (user?.deleted_at ? "Inactive" : "Active");
const getCoinBalance = (user) => Number(user?.gamification?.coin?.balance ?? user?.coin_balance ?? 0);

const FieldLabel = ({ children }) => (
  <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-subtle)]">
    {children}
  </label>
);

const AdminUsersPage = () => {
  const { user: currentUser } = useAuth();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchInput, setSearchInput] = useState(DEFAULT_FILTERS.search);
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState("FREE");
  const [subscriptionDurationDays, setSubscriptionDurationDays] = useState("30");
  const [activeUserTab, setActiveUserTab] = useState("overview");
  const [coinDelta, setCoinDelta] = useState("");
  const [coinReason, setCoinReason] = useState("");
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
        return null;
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
    const timeoutId = window.setTimeout(() => {
      setFilters((current) => {
        if (current.search === searchInput) return current;
        return {
          ...current,
          search: searchInput,
          page: 1,
        };
      });
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  useEffect(() => {
    void loadUserDetail(selectedUserId);
  }, [loadUserDetail, selectedUserId]);

  useEffect(() => {
    setFormData(toFormState(selectedUser));
  }, [selectedUser]);

  useEffect(() => {
    setSelectedPlan(getPlanBadge(selectedUser));
    setSubscriptionDurationDays("30");
  }, [selectedUser]);

  const currentPayload = useMemo(() => buildUpdatePayload(formData), [formData]);
  const baselinePayload = useMemo(() => buildUpdatePayload(toFormState(selectedUser)), [selectedUser]);
  const hasFormChanges = JSON.stringify(currentPayload) !== JSON.stringify(baselinePayload);
  const hasPlanChange = selectedPlan !== getPlanBadge(selectedUser);
  const parsedSubscriptionDurationDays = Number(subscriptionDurationDays);
  const requiresSubscriptionDuration = selectedPlan !== "FREE";
  const hasValidSubscriptionDuration =
    !requiresSubscriptionDuration || (Number.isInteger(parsedSubscriptionDurationDays) && parsedSubscriptionDurationDays > 0);
  const parsedCoinDelta = Number(coinDelta);
  const hasCoinAdjustment = coinDelta !== "" && Number.isInteger(parsedCoinDelta) && parsedCoinDelta !== 0;
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

  const handleAdjustCoins = async () => {
    if (!hasCoinAdjustment) return;

    await runAction(
      (userId) =>
        adminUsersApi.adjustBalance(userId, {
          coin_delta: parsedCoinDelta,
          reason: coinReason.trim() || null,
        }),
      `Coin balance adjusted by ${parsedCoinDelta}.`,
    );
    setCoinDelta("");
    setCoinReason("");
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

        <section id="user-directory">
          <div className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
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
                className="inline-flex items-center gap-2 rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-[var(--page-muted)] transition hover:bg-muted"
              >
                <ArrowClockwise size={16} />
                Refresh
              </button>
            </div>

            <div className="mt-5 grid gap-3 xl:grid-cols-[minmax(0,1fr)_160px_160px_170px]">
              <label className="relative block">
                <MagnifyingGlass size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--page-subtle)]" />
                <input
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder="Search email or display name..."
                  className="w-full rounded-[22px] border border-border bg-muted px-11 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                />
              </label>

              <select
                value={filters.status}
                onChange={(event) => updateFilter("status", event.target.value)}
                className="rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
              >
                <option value="">All status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>

              <select
                value={filters.role}
                onChange={(event) => updateFilter("role", event.target.value)}
                className="rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
              >
                <option value="">All roles</option>
                <option value="learner">Learners</option>
                <option value="admin">Admins</option>
              </select>

              <select
                value={filters.subscription_tier}
                onChange={(event) => updateFilter("subscription_tier", event.target.value)}
                className="rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
              >
                <option value="">All plans</option>
                <option value="FREE">Free</option>
                <option value="PRO">Pro</option>
              </select>
            </div>

            <div className="mt-5 overflow-hidden rounded-[26px] border border-border ">
              <div className="grid grid-cols-[minmax(0,1.6fr)_120px_120px_120px_160px] gap-3 bg-muted px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-[var(--page-muted)]  ">
                <span>User</span>
                <span>Role</span>
                <span>Plan</span>
                <span>Status</span>
                <span className="text-right">Updated</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingList && (
                  <div className="px-4 py-8 text-sm text-[var(--page-muted)] ">Loading users...</div>
                )}

                {!isLoadingList && users.length === 0 && (
                  <div className="px-4 py-8 text-sm text-[var(--page-muted)] ">No users matched the current filters.</div>
                )}

                {!isLoadingList && users.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setSelectedUserId(item.id);
                      setActiveUserTab("overview");
                    }}
                    className={`grid w-full grid-cols-[minmax(0,1.6fr)_120px_120px_120px_160px] gap-3 px-4 py-4 text-left text-sm transition ${
                      selectedUserId === item.id ? "bg-primary/5 dark:bg-primary/10" : ""
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-[var(--page-fg)] ">
                        {item.display_name || item.email}
                      </p>
                      <p className="truncate text-xs text-[var(--page-muted)] ">{item.email}</p>
                    </div>
                    <div className="flex items-center">
                      <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                        item.is_admin
                          ? "bg-primary/10 text-primary dark:bg-primary/15 dark:text-white"
                          : "bg-[var(--surface-strong)] text-[var(--page-muted)]  "
                      }`}>
                        {getRoleBadge(item)}
                      </span>
                    </div>
                    <div className="flex items-center text-[var(--page-muted)] ">{getPlanBadge(item)}</div>
                    <div className="flex items-center">
                      <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                        item.deleted_at
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
                          : "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                      }`}>
                        {getStatusBadge(item)}
                      </span>
                    </div>
                    <div className="flex items-center justify-end text-xs text-[var(--page-muted)] ">
                      {formatDateTime(item.updated_at)}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-[var(--page-muted)] ">
              <span>
                Page {filters.page} / {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={filters.page <= 1}
                  onClick={() => updateFilter("page", filters.page - 1)}
                  className="rounded-2xl border border-border px-4 py-2 font-semibold transition hover:bg-muted disabled:opacity-50  hover:bg-muted"
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={filters.page >= totalPages}
                  onClick={() => updateFilter("page", filters.page + 1)}
                  className="rounded-2xl border border-border px-4 py-2 font-semibold transition hover:bg-muted disabled:opacity-50  hover:bg-muted"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <div className={`fixed inset-y-0 right-0 z-50 w-full max-w-2xl overflow-y-auto border-l border-border bg-muted p-4 shadow-2xl transition-transform duration-300   ${selectedUserId ? "translate-x-0" : "translate-x-full"}`}>
            <div className="mb-4 rounded-[30px] border border-border bg-card p-4 shadow-sm  ">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Selected User</p>
                  <h2 className="mt-1 text-xl font-black">{selectedUser?.display_name || selectedUser?.email || "Loading..."}</h2>
                  <p className="mt-1 truncate text-xs text-[var(--page-muted)] ">{selectedUser?.email || "Select a user to inspect"}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedUserId(null)}
                  className="rounded-2xl border border-border p-3 text-[var(--page-muted)] transition hover:bg-muted"
                  aria-label="Close user detail"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 rounded-2xl bg-muted p-1 text-xs font-black ">
                {[
                  ["overview", "Overview"],
                  ["profile", "Profile"],
                  ["actions", "Actions"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setActiveUserTab(value)}
                    className={`rounded-xl px-3 py-2 transition ${activeUserTab === value ? "bg-white text-primary shadow-sm  dark:text-white" : "text-[var(--page-muted)] hover:text-[var(--page-fg)]  dark:hover:text-white"}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {activeUserTab === "overview" && (
            <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">User Detail</p>
              {isLoadingDetail && <p className="mt-4 text-sm text-[var(--page-muted)] ">Loading detail...</p>}
              {!isLoadingDetail && !selectedUser && (
                <p className="mt-4 text-sm text-[var(--page-muted)] ">Select a user to inspect the account.</p>
              )}
              {!isLoadingDetail && selectedUser && (
                <div className="mt-4 space-y-4">
                  <div className="rounded-[24px] bg-muted p-4 ">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">Identity</p>
                    <p className="mt-2 text-sm font-semibold">{selectedUser.display_name || "No display name"}</p>
                    <p className="mt-1 text-xs text-[var(--page-muted)] ">{selectedUser.email}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-muted p-4 ">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">Role & status</p>
                      <p className="mt-2 text-sm font-semibold">{getRoleBadge(selectedUser)}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">{getStatusBadge(selectedUser)}</p>
                    </div>
                    <div className="rounded-[24px] bg-muted p-4 ">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">Subscription</p>
                      <p className="mt-2 text-sm font-semibold">{getPlanBadge(selectedUser)}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">
                        {selectedUser.subscription?.status || "inactive"}
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-muted p-4 ">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">Learning</p>
                      <p className="mt-2 text-sm font-semibold">Level: {selectedUser.level || "Not set"}</p>
                    </div>
                    <div className="rounded-[24px] bg-amber-50 p-4 text-amber-900 dark:bg-amber-500/10 dark:text-amber-100">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-600 dark:text-amber-200">Coin Balance</p>
                      <p className="mt-2 text-2xl font-black">{getCoinBalance(selectedUser).toLocaleString()}</p>
                      <p className="mt-1 text-xs text-amber-700 dark:text-amber-200/80">Available learner coins</p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-muted p-4 ">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">Timeline</p>
                      <p className="mt-2 text-sm font-semibold">{formatDateTime(selectedUser.created_at)}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">
                        Updated {formatDateTime(selectedUser.updated_at)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </section>
            )}

            {activeUserTab === "profile" && (
            <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Edit Profile</p>
              <form className="mt-4 space-y-4" onSubmit={handleSave}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel>Display Name</FieldLabel>
                    <input
                      value={formData.display_name}
                      onChange={(event) => setFormData((current) => ({ ...current, display_name: event.target.value }))}
                      className="w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
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
                      className="w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                    />
                  </div>
                </div>
                <div>
                  <FieldLabel>Level</FieldLabel>
                  <select
                    value={formData.level}
                    onChange={(event) => setFormData((current) => ({ ...current, level: event.target.value }))}
                    className="w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                  >
                    {LEVEL_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <FieldLabel>Favorite Topics</FieldLabel>
                  <input
                    value={formData.favorite_topics}
                    onChange={(event) => setFormData((current) => ({ ...current, favorite_topics: event.target.value }))}
                    placeholder="travel, interview, networking"
                    className="w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                  />
                </div>

                <div>
                  <FieldLabel>Learning Purpose</FieldLabel>
                  <input
                    value={formData.learning_purpose}
                    onChange={(event) => setFormData((current) => ({ ...current, learning_purpose: event.target.value }))}
                    placeholder="travel, meetings, study abroad"
                    className="w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                  />
                </div>

                <div>
                  <FieldLabel>Main Challenge</FieldLabel>
                  <textarea
                    value={formData.main_challenge}
                    onChange={(event) => setFormData((current) => ({ ...current, main_challenge: event.target.value }))}
                    className="min-h-[110px] w-full rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
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
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-[var(--page-muted)] transition hover:bg-muted disabled:opacity-50   hover:bg-muted"
                  >
                    <ArrowClockwise size={16} />
                    Reset Form
                  </button>
                </div>
              </form>
            </section>
            )}

            {activeUserTab === "actions" && (
            <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Admin Actions</p>
              <div className="mt-4 grid gap-3">
                <div className="rounded-[24px] bg-muted p-4 ">
                  <div className="flex flex-col gap-3">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">
                        Subscription Plan
                      </p>
                      <p className="mt-2 text-xs text-[var(--page-muted)] ">
                        Apply a plan change directly from admin controls.
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_150px_180px]">
                      <select
                        value={selectedPlan}
                        onChange={(event) => setSelectedPlan(event.target.value)}
                        disabled={!selectedUserId || isRunningAction}
                        className="w-full rounded-[22px] border border-border bg-card px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)] disabled:opacity-50  "
                      >
                        {PLAN_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>

                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={subscriptionDurationDays}
                        onChange={(event) => setSubscriptionDurationDays(event.target.value)}
                        disabled={!selectedUserId || isRunningAction || selectedPlan === "FREE"}
                        placeholder="Days"
                        className="w-full rounded-[22px] border border-border bg-card px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)] disabled:opacity-50  "
                      />

                      <button
                        type="button"
                        disabled={!selectedUserId || isRunningAction || !hasPlanChange || !hasValidSubscriptionDuration}
                        onClick={() => {
                          const payload = {
                            tier: selectedPlan,
                            ...(selectedPlan !== "FREE" ? { duration_days: parsedSubscriptionDurationDays } : {}),
                          };
                          void runAction(
                            (userId) => adminUsersApi.updateSubscription(userId, payload),
                            `Subscription updated to ${selectedPlan}.`,
                          );
                        }}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-black text-primary transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-primary/20 dark:bg-primary/15 dark:text-white"
                      >
                        <CrownSimple size={16} weight="fill" />
                        Update Plan
                      </button>
                    </div>

                    <p className="text-xs text-[var(--page-muted)] ">
                      Current plan: <span className="font-semibold">{getPlanBadge(selectedUser)}</span>
                      {selectedUser?.subscription?.expires_at ? ` · Expires ${formatDateTime(selectedUser.subscription.expires_at)}` : ""}
                    </p>
                    {requiresSubscriptionDuration && !hasValidSubscriptionDuration ? (
                      <p className="text-xs font-semibold text-rose-600">Paid plans require a positive duration in days.</p>
                    ) : null}
                  </div>
                </div>

                <div className="rounded-[24px] bg-muted p-4 ">
                  <div className="flex flex-col gap-3">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">
                        Coin Balance
                      </p>
                      <p className="mt-2 text-xs text-[var(--page-muted)] ">
                        Add or subtract coins for the selected learner.
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-[150px_minmax(0,1fr)]">
                      <input
                        type="number"
                        step="1"
                        value={coinDelta}
                        onChange={(event) => setCoinDelta(event.target.value)}
                        disabled={!selectedUserId || isRunningAction}
                        placeholder="+100 / -50"
                        className="w-full rounded-[22px] border border-border bg-card px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)] disabled:opacity-50  "
                      />
                      <input
                        value={coinReason}
                        onChange={(event) => setCoinReason(event.target.value)}
                        disabled={!selectedUserId || isRunningAction}
                        placeholder="Reason shown in transaction metadata"
                        className="w-full rounded-[22px] border border-border bg-card px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)] disabled:opacity-50  "
                      />
                    </div>

                    <button
                      type="button"
                      disabled={!selectedUserId || isRunningAction || !hasCoinAdjustment}
                      onClick={() => {
                        void handleAdjustCoins();
                      }}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-black text-amber-700 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"
                    >
                      <Gift size={16} weight="fill" />
                      Apply Coin Change
                    </button>

                    <p className="text-xs text-[var(--page-muted)] ">
                      Current coins: <span className="font-semibold">{getCoinBalance(selectedUser).toLocaleString()}</span>
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
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-blue to-primary px-4 py-3 text-sm font-black text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 "
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
                  <p className="text-xs font-medium text-[var(--page-muted)] ">
                    Self-protection is enabled. Your own admin access and account status cannot be changed here.
                  </p>
                ) : null}
              </div>
            </section>
            )}
          </div>
        </section>
      </div>
    </AdminShell>
  );
};

export default AdminUsersPage;

