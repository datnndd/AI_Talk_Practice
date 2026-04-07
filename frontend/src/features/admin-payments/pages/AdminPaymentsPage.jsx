import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowClockwise, CheckCircle, CreditCard, MagnifyingGlass, ProhibitInset, SquaresFour, UserList } from "@phosphor-icons/react";

import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import { adminPaymentsApi } from "@/features/admin-payments/api/adminPaymentsApi";
import { useTheme } from "@/shared/context/ThemeContext";

const DEFAULT_FILTERS = {
  status: "",
  search: "",
  page: 1,
  page_size: 12,
};

const adminNavItems = [
  { label: "Users", icon: UserList, to: "/admin/users" },
  { label: "Scenario Library", icon: SquaresFour, to: "/admin/scenarios" },
  { label: "Transactions", icon: CreditCard, anchor: "#transaction-library" },
];

const formatCurrency = (amount, currency) => {
  if (currency === "USD") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
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

const AdminPaymentsPage = () => {
  const { theme, toggleTheme } = useTheme();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [overview, setOverview] = useState(null);
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

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === "page" ? value : 1,
    }));
  };

  const loadOverview = useCallback(async () => {
    const data = await adminPaymentsApi.getOverview();
    setOverview(data);
  }, []);

  const loadTransactions = useCallback(async () => {
    setIsLoadingList(true);
    setError("");
    try {
      const data = await adminPaymentsApi.listTransactions(filters);
      setTransactions(data.items);
      setTotal(data.total);
      setSelectedTransactionId((current) => {
        if (current && data.items.some((item) => item.id === current)) {
          return current;
        }
        return data.items[0]?.id || null;
      });
    } catch (listError) {
      setError(listError?.response?.data?.detail || "Failed to load transactions.");
    } finally {
      setIsLoadingList(false);
    }
  }, [filters]);

  const loadTransactionDetail = useCallback(async (paymentId) => {
    if (!paymentId) {
      setSelectedTransaction(null);
      return;
    }
    setIsLoadingDetail(true);
    try {
      const data = await adminPaymentsApi.getTransaction(paymentId);
      setSelectedTransaction(data);
    } catch (detailError) {
      setError(detailError?.response?.data?.detail || "Failed to load transaction detail.");
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    void loadOverview();
    void loadTransactions();
  }, [loadOverview, loadTransactions]);

  useEffect(() => {
    void loadTransactionDetail(selectedTransactionId);
  }, [loadTransactionDetail, selectedTransactionId]);

  const summaryCards = useMemo(() => [
    { label: "Total", value: overview?.total_transactions || 0 },
    { label: "Pending", value: overview?.pending_transactions || 0 },
    { label: "Paid", value: overview?.paid_transactions || 0 },
    { label: "Revenue", value: formatCurrency(overview?.paid_revenue_usd_cents || 0, "USD") },
  ], [overview]);

  const handleApprove = async () => {
    if (!selectedTransactionId) return;
    setIsProcessingAction(true);
    setError("");
    try {
      await adminPaymentsApi.approveTransaction(selectedTransactionId, { reason });
      setNotice("Transaction approved and subscription activated.");
      setReason("");
      await loadOverview();
      await loadTransactions();
      await loadTransactionDetail(selectedTransactionId);
    } catch (actionError) {
      setError(actionError?.response?.data?.detail || "Failed to approve transaction.");
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
      await loadOverview();
      await loadTransactions();
      await loadTransactionDetail(selectedTransactionId);
    } catch (actionError) {
      setError(actionError?.response?.data?.detail || "Failed to cancel transaction.");
    } finally {
      setIsProcessingAction(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / filters.page_size));

  return (
    <AdminShell
      theme={theme}
      onToggleTheme={toggleTheme}
      navItems={adminNavItems}
      title="Payment Operations"
      subtitle="Monitor Stripe transactions, inspect payment state, and handle manual admin approval or cancellation when support workflows require intervention."
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

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {summaryCards.map((card) => (
            <div key={card.label} className="rounded-[28px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                {card.label}
              </p>
              <p className="mt-3 font-display text-4xl font-black tracking-tight">{card.value}</p>
            </div>
          ))}
        </div>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]" id="transaction-library">
          <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Transaction Library</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Stripe Transactions</h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  void loadOverview();
                  void loadTransactions();
                }}
                className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
              >
                <ArrowClockwise size={16} />
                Refresh
              </button>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
              <label className="relative block">
                <MagnifyingGlass size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  value={filters.search}
                  onChange={(event) => updateFilter("search", event.target.value)}
                  placeholder="Search order, checkout id, email..."
                  className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-11 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>
              <select
                value={filters.status}
                onChange={(event) => updateFilter("status", event.target.value)}
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="">All status</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>

            <div className="mt-5 overflow-hidden rounded-[26px] border border-zinc-200 dark:border-zinc-800">
              <div className="grid grid-cols-[140px_120px_120px_minmax(0,1fr)_160px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <span>Status</span>
                <span>Provider</span>
                <span>Amount</span>
                <span>Customer</span>
                <span className="text-right">Created</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingList && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading transactions...</div>
                )}

                {!isLoadingList && transactions.length === 0 && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">No transactions found.</div>
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
                      <span
                        className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                          transaction.status === "paid"
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                            : transaction.status === "pending"
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300"
                              : "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                        }`}
                      >
                        {transaction.status}
                      </span>
                    </div>
                    <div className="flex items-center uppercase text-zinc-600 dark:text-zinc-300">{transaction.provider}</div>
                    <div className="flex items-center text-zinc-600 dark:text-zinc-300">
                      {formatCurrency(transaction.amount, transaction.currency)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-zinc-900 dark:text-zinc-100">
                        {transaction.user_display_name || transaction.user_email}
                      </p>
                      <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">{transaction.user_email}</p>
                      <p className="truncate text-xs text-zinc-400 dark:text-zinc-500">{transaction.order_code}</p>
                    </div>
                    <div className="flex items-center justify-end text-xs text-zinc-500 dark:text-zinc-400">
                      {formatDateTime(transaction.created_at)}
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
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Transaction Detail</p>
              {isLoadingDetail && <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">Loading detail...</p>}
              {!isLoadingDetail && !selectedTransaction && (
                <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">Select a transaction to inspect it.</p>
              )}
              {!isLoadingDetail && selectedTransaction && (
                <div className="mt-4 space-y-4">
                  <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Order</p>
                    <p className="mt-2 font-mono text-sm font-semibold">{selectedTransaction.order_code}</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Customer</p>
                      <p className="mt-2 text-sm font-semibold">{selectedTransaction.user_display_name || "No display name"}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{selectedTransaction.user_email}</p>
                    </div>
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Payment</p>
                      <p className="mt-2 text-sm font-semibold">{formatCurrency(selectedTransaction.amount, selectedTransaction.currency)}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{selectedTransaction.provider.toUpperCase()}</p>
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Status</p>
                      <p className="mt-2 text-sm font-semibold">{selectedTransaction.status}</p>
                      <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{formatDateTime(selectedTransaction.paid_at)}</p>
                    </div>
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Subscription expiry</p>
                      <p className="mt-2 text-sm font-semibold">{formatDateTime(selectedTransaction.expires_at)}</p>
                    </div>
                  </div>
                  <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">Gateway references</p>
                    <p className="mt-2 break-all text-xs text-zinc-600 dark:text-zinc-300">
                      Checkout: {selectedTransaction.external_checkout_id || "N/A"}
                    </p>
                    <p className="mt-1 break-all text-xs text-zinc-600 dark:text-zinc-300">
                      Transaction: {selectedTransaction.external_transaction_id || "N/A"}
                    </p>
                  </div>
                  {selectedTransaction.failure_reason && (
                    <div className="rounded-[24px] border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300">
                      {selectedTransaction.failure_reason}
                    </div>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Admin Actions</p>
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Optional reason for manual approval or cancellation..."
                className="mt-4 min-h-[120px] w-full rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
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
