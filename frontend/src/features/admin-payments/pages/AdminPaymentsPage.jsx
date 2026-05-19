import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowClockwise, CheckCircle, MagnifyingGlass, ProhibitInset } from "@phosphor-icons/react";

import AdminShell from "@/shared/components/admin/AdminShell";
import { adminPaymentsApi } from "@/features/admin-payments/api/adminPaymentsApi";

const DEFAULT_FILTERS = {
  status: "",
  search: "",
  page: 1,
  page_size: 12,
};

const formatCurrency = (amount, currency) => {
  if (currency === "VND") {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(amount || 0);
  }
  return `${amount} ${currency}`;
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

const getApiErrorMessage = (error, fallback) => error?.response?.data?.detail || fallback;

const StatusPill = ({ status }) => {
  const tone =
    status === "paid"
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
      : status === "pending"
        ? "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300"
        : "bg-[var(--surface-strong)] text-[var(--page-muted)]  ";

  return (
    <span className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${tone}`}>
      {status}
    </span>
  );
};

const FeedbackMessage = ({ error, notice }) => {
  if (!error && !notice) return null;

  return (
    <div
      className={`rounded-[26px] px-5 py-4 text-sm font-semibold ${
        error
          ? "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
          : "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
      }`}
    >
      {error || notice}
    </div>
  );
};

const DetailCard = ({ label, children }) => (
  <div className="rounded-[24px] bg-muted p-4 ">
    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)] ">{label}</p>
    {children}
  </div>
);

const AdminPaymentsPage = () => {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedTransactionId, setSelectedTransactionId] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isProcessingAction, setIsProcessingAction] = useState(false);
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [plans, setPlans] = useState([]);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === "page" ? value : 1,
    }));
  };

  const loadTransactions = useCallback(async () => {
    setIsLoadingList(true);
    setError("");
    try {
      const data = await adminPaymentsApi.listTransactions(filters);
      if (!mountedRef.current) {
        return;
      }
      setTransactions(data.items);
      setTotal(data.total);
      setSelectedTransactionId((current) => {
        if (current && data.items.some((item) => item.id === current)) {
          return current;
        }
        return data.items[0]?.id || null;
      });
    } catch (listError) {
      if (mountedRef.current) {
        setError(getApiErrorMessage(listError, "Failed to load transactions."));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoadingList(false);
      }
    }
  }, [filters]);

  const loadBillingSettings = useCallback(async () => {
    const planData = await adminPaymentsApi.listPlans();
    if (mountedRef.current) {
      setPlans(planData);
    }
  }, []);

  const loadTransactionDetail = useCallback(async (paymentId) => {
    if (!paymentId) {
      setSelectedTransaction(null);
      return;
    }
    setIsLoadingDetail(true);
    try {
      const data = await adminPaymentsApi.getTransaction(paymentId);
      if (mountedRef.current) {
        setSelectedTransaction(data);
      }
    } catch (detailError) {
      if (mountedRef.current) {
        setError(getApiErrorMessage(detailError, "Failed to load transaction detail."));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoadingDetail(false);
      }
    }
  }, []);

  const refreshPaymentData = useCallback(async (paymentId) => {
    await loadTransactions();
    await loadTransactionDetail(paymentId);
  }, [loadTransactionDetail, loadTransactions]);

  useEffect(() => {
    void loadTransactions();
    void loadBillingSettings();
  }, [loadBillingSettings, loadTransactions]);

  useEffect(() => {
    void loadTransactionDetail(selectedTransactionId);
  }, [loadTransactionDetail, selectedTransactionId]);

  const handleApprove = async () => {
    if (!selectedTransactionId) return;
    setIsProcessingAction(true);
    setError("");
    try {
      await adminPaymentsApi.approveTransaction(selectedTransactionId, { reason });
      setNotice("Transaction approved and subscription activated.");
      setReason("");
      await refreshPaymentData(selectedTransactionId);
    } catch (actionError) {
      setError(getApiErrorMessage(actionError, "Failed to approve transaction."));
    } finally {
      setIsProcessingAction(false);
    }
  };

  const handleCancel = async () => {
    if (!selectedTransactionId) return;
    setIsProcessingAction(true);
    setError("");
    try {
      await adminPaymentsApi.cancelTransaction(selectedTransactionId, { reason });
      setNotice("Transaction cancelled.");
      setReason("");
      await refreshPaymentData(selectedTransactionId);
    } catch (actionError) {
      setError(getApiErrorMessage(actionError, "Failed to cancel transaction."));
    } finally {
      setIsProcessingAction(false);
    }
  };

  const updatePlanField = (code, field, value) => {
    setPlans((current) => current.map((plan) => (plan.code === code ? { ...plan, [field]: value } : plan)));
  };

  const savePlan = async (plan) => {
    setError("");
    try {
      await adminPaymentsApi.updatePlan(plan.code, {
        name: plan.name,
        price_amount: Number(plan.price_amount || 0),
        is_active: Boolean(plan.is_active),
        sort_order: Number(plan.sort_order || 0),
      });
      setNotice("Subscription plan saved.");
      await loadBillingSettings();
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Failed to save plan."));
    }
  };
  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / filters.page_size)),
    [filters.page_size, total],
  );

  return (
    <AdminShell
      title="Payment Operations"
      subtitle="Manage subscription plans, inspect transactions, and handle manual approval or cancellation."
    >
      <div className="space-y-6">
        <FeedbackMessage error={error} notice={notice} />

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Subscription Plans</p>
            <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Pro pricing</h2>
            <div className="mt-5 space-y-3">
              {plans.map((plan) => (
                <div key={plan.code} className="grid gap-3 rounded-2xl border border-border p-4  md:grid-cols-[1fr_130px_90px_90px_auto] md:items-center">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-subtle)]">{plan.code} · {plan.duration_days} days</p>
                    <input value={plan.name} onChange={(event) => updatePlanField(plan.code, "name", event.target.value)} className="mt-1 w-full rounded-xl border border-border px-3 py-2 text-sm font-bold  " />
                  </div>
                  <input type="number" min="0" value={plan.price_amount} onChange={(event) => updatePlanField(plan.code, "price_amount", event.target.value)} className="rounded-xl border border-border px-3 py-2 text-sm font-bold  " />
                  <input type="number" value={plan.sort_order} onChange={(event) => updatePlanField(plan.code, "sort_order", event.target.value)} className="rounded-xl border border-border px-3 py-2 text-sm font-bold  " />
                  <label className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-[var(--page-muted)]">
                    <input type="checkbox" checked={Boolean(plan.is_active)} onChange={(event) => updatePlanField(plan.code, "is_active", event.target.checked)} /> Active
                  </label>
                  <button type="button" onClick={() => savePlan(plan)} className="rounded-xl bg-gradient-to-r from-brand-blue to-primary px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-white ">Save</button>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]" id="transaction-library">
          <div className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Transaction Library</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Stripe Transactions</h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  void loadTransactions();
                }}
                className="inline-flex items-center gap-2 rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-[var(--page-muted)] transition hover:bg-muted"
              >
                <ArrowClockwise size={16} />
                Refresh
              </button>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
              <label className="relative block">
                <MagnifyingGlass size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--page-subtle)]" />
                <input
                  value={filters.search}
                  onChange={(event) => updateFilter("search", event.target.value)}
                  placeholder="Search order, checkout id, email..."
                  className="w-full rounded-[22px] border border-border bg-muted px-11 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
                />
              </label>
              <select
                value={filters.status}
                onChange={(event) => updateFilter("status", event.target.value)}
                className="rounded-[22px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
              >
                <option value="">All status</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>

            <div className="mt-5 overflow-hidden rounded-[26px] border border-border ">
              <div className="grid grid-cols-[140px_120px_120px_minmax(0,1fr)_160px] gap-3 bg-muted px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-[var(--page-muted)]  ">
                <span>Status</span>
                <span>Provider</span>
                <span>Amount</span>
                <span>Customer</span>
                <span className="text-right">Created</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingList && (
                  <div className="px-4 py-8 text-sm text-[var(--page-muted)] ">Loading transactions...</div>
                )}

                {!isLoadingList && transactions.length === 0 && (
                  <div className="px-4 py-8 text-sm text-[var(--page-muted)] ">No transactions found.</div>
                )}

                {!isLoadingList && transactions.map((transaction) => (
                  <button
                    key={transaction.id}
                    type="button"
                    onClick={() => setSelectedTransactionId(transaction.id)}
                    className={`grid w-full grid-cols-[140px_120px_120px_minmax(0,1fr)_160px] gap-3 px-4 py-4 text-left text-sm transition ${
                      selectedTransactionId === transaction.id ? "bg-primary/5 dark:bg-primary/10" : ""
                    }`}
                  >
                    <div className="flex items-center">
                      <StatusPill status={transaction.status} />
                    </div>
                    <div className="flex items-center uppercase text-[var(--page-muted)] ">{transaction.provider}</div>
                    <div className="flex items-center text-[var(--page-muted)] ">
                      {formatCurrency(transaction.amount, transaction.currency)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-[var(--page-fg)] ">
                        {transaction.user_display_name || transaction.user_email}
                      </p>
                      <p className="truncate text-xs text-[var(--page-muted)] ">{transaction.user_email}</p>
                      <p className="truncate text-xs text-[var(--page-subtle)] dark:text-[var(--page-muted)]">{transaction.order_code}</p>
                    </div>
                    <div className="flex items-center justify-end text-xs text-[var(--page-muted)] ">
                      {formatDateTime(transaction.created_at)}
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

          <div className="space-y-6">
            <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Transaction Detail</p>
              {isLoadingDetail && <p className="mt-4 text-sm text-[var(--page-muted)] ">Loading detail...</p>}
              {!isLoadingDetail && !selectedTransaction && (
                <p className="mt-4 text-sm text-[var(--page-muted)] ">Select a transaction to inspect it.</p>
              )}
              {!isLoadingDetail && selectedTransaction && (
                <div className="mt-4 space-y-4">
                  <DetailCard label="Order">
                    <p className="mt-2 font-mono text-sm font-semibold">{selectedTransaction.order_code}</p>
                  </DetailCard>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <DetailCard label="Customer">
                      <p className="mt-2 text-sm font-semibold">{selectedTransaction.user_display_name || "No display name"}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">{selectedTransaction.user_email}</p>
                    </DetailCard>
                    <DetailCard label="Payment">
                      <p className="mt-2 text-sm font-semibold">{formatCurrency(selectedTransaction.amount, selectedTransaction.currency)}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">{selectedTransaction.provider.toUpperCase()}</p>
                    </DetailCard>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <DetailCard label="Status">
                      <p className="mt-2 text-sm font-semibold">{selectedTransaction.status}</p>
                      <p className="mt-1 text-xs text-[var(--page-muted)] ">{formatDateTime(selectedTransaction.paid_at)}</p>
                    </DetailCard>
                    <DetailCard label="Subscription expiry">
                      <p className="mt-2 text-sm font-semibold">{formatDateTime(selectedTransaction.expires_at)}</p>
                    </DetailCard>
                  </div>
                  <DetailCard label="Gateway references">
                    <p className="mt-2 break-all text-xs text-[var(--page-muted)] ">
                      Checkout: {selectedTransaction.external_checkout_id || "N/A"}
                    </p>
                    <p className="mt-1 break-all text-xs text-[var(--page-muted)] ">
                      Transaction: {selectedTransaction.external_transaction_id || "N/A"}
                    </p>
                  </DetailCard>
                  {selectedTransaction.failure_reason && (
                    <div className="rounded-[24px] border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300">
                      {selectedTransaction.failure_reason}
                    </div>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm  ">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Admin Actions</p>
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Optional reason for manual approval or cancellation..."
                className="mt-4 min-h-[120px] w-full rounded-[24px] border border-border bg-muted px-4 py-3 text-sm font-medium outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]  "
              />
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={!selectedTransactionId || isProcessingAction}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-black text-white shadow-lg shadow-emerald-900/10 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <CheckCircle size={16} />
                  Approve Payment
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={!selectedTransactionId || isProcessingAction}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-black text-rose-700 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300"
                >
                  <ProhibitInset size={16} />
                  Cancel Transaction
                </button>
              </div>
            </section>
          </div>
        </section>
      </div>
    </AdminShell>
  );
};

export default AdminPaymentsPage;

