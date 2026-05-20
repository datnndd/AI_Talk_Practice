import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowClockwise } from "@phosphor-icons/react";

import { adminPaymentsApi } from "@/features/admin-payments/api/adminPaymentsApi";
import AdminShell from "@/shared/components/admin/AdminShell";

const STATS_PERIODS = [
  { value: "day", label: "Ngày" },
  { value: "month", label: "Tháng" },
  { value: "year", label: "Năm" },
];

const formatCurrency = (amount, currency = "VND") => {
  if (currency === "VND") {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(amount || 0);
  }
  return `${amount || 0} ${currency}`;
};

const formatDateTime = (value) => {
  if (!value) return "Not available";
  return new Date(value).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

const getApiErrorMessage = (error, fallback) => error?.response?.data?.detail || fallback;

const KpiCard = ({ label, value, hint }) => (
  <div className="rounded-[28px] border border-border bg-card p-5 shadow-sm">
    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-[var(--page-muted)]">{label}</p>
    <p className="mt-3 font-display text-4xl font-black tracking-tight">{value}</p>
    {hint && <p className="mt-2 text-xs font-semibold text-[var(--page-muted)]">{hint}</p>}
  </div>
);

const ChartCard = ({ eyebrow, title, children, action }) => (
  <section className="rounded-[30px] border border-border bg-card p-5 shadow-sm">
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">{eyebrow}</p>
        <h2 className="mt-1 font-display text-2xl font-black tracking-tight">{title}</h2>
      </div>
      {action}
    </div>
    {children}
  </section>
);

const getXAxisTickIndexes = (itemsLength) => {
  if (itemsLength <= 6) return Array.from({ length: itemsLength }, (_, index) => index);
  const lastIndex = itemsLength - 1;
  return Array.from(new Set([0, Math.round(lastIndex * 0.2), Math.round(lastIndex * 0.4), Math.round(lastIndex * 0.6), Math.round(lastIndex * 0.8), lastIndex]));
};

const buildSmoothPath = (points) => {
  if (!points.length) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x} ${point.y}`;

    const previous = points[index - 1];
    const controlDistance = (point.x - previous.x) / 2;
    return `${path} C ${previous.x + controlDistance} ${previous.y}, ${point.x - controlDistance} ${point.y}, ${point.x} ${point.y}`;
  }, "");
};

const AreaTrendChart = ({ items = [], valueKey, currency, emptyText, titleFormatter, valueFormatter }) => {
  const maxValue = Math.max(...items.map((item) => item[valueKey] || 0), 0);
  if (maxValue <= 0) {
    return <div className="flex h-80 items-center justify-center rounded-[24px] bg-muted text-sm font-bold text-[var(--page-muted)]">{emptyText}</div>;
  }

  const width = Math.max(items.length * 42, 720);
  const height = 300;
  const padding = { top: 34, right: 34, bottom: 54, left: 44 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const baselineY = padding.top + chartHeight;
  const safeItemsLength = Math.max(items.length - 1, 1);
  const points = items.map((item, index) => {
    const value = item[valueKey] || 0;
    const x = padding.left + (index / safeItemsLength) * chartWidth;
    const y = baselineY - (value / maxValue) * chartHeight;
    return { item, value, x, y };
  });
  const linePath = buildSmoothPath(points);
  const areaPath = points.length === 1
    ? `M ${points[0].x - 18} ${baselineY} L ${points[0].x} ${points[0].y} L ${points[0].x + 18} ${baselineY} Z`
    : `${linePath} L ${points[points.length - 1].x} ${baselineY} L ${points[0].x} ${baselineY} Z`;
  const activePoints = points.filter((point) => point.value > 0);
  const tickIndexes = getXAxisTickIndexes(items.length);
  const chartId = `area-trend-${valueKey}`;

  return (
    <div className="overflow-x-auto rounded-[24px] bg-muted p-3">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-80 min-w-[720px] w-full" role="img" aria-label="Dashboard chart">
        <defs>
          <linearGradient id={`${chartId}-fill`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" className="text-primary" stopColor="currentColor" stopOpacity="0.24" />
            <stop offset="100%" className="text-primary" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
          <filter id={`${chartId}-glow`} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="8" stdDeviation="8" floodColor="currentColor" floodOpacity="0.16" />
          </filter>
        </defs>

        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + chartHeight * ratio;
          return (
            <line key={ratio} x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="currentColor" className="text-border/70" strokeDasharray={ratio === 1 ? "0" : "8 8"} strokeWidth={ratio === 1 ? "2" : "1"} />
          );
        })}

        <path d={areaPath} fill={`url(#${chartId}-fill)`} />
        <path d={linePath} fill="none" stroke="currentColor" className="text-primary" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" filter={`url(#${chartId}-glow)`} />

        {activePoints.map((point) => (
          <g key={`${point.item.label}-${point.item.period_start}`}>
            <circle cx={point.x} cy={point.y} r={activePoints.length === 1 ? 6 : 4} className="fill-card stroke-primary transition hover:fill-primary hover:stroke-primary" strokeWidth="3">
              <title>{titleFormatter ? titleFormatter(point.item, currency) : `${point.item.label}: ${point.value}`}</title>
            </circle>
            {activePoints.length === 1 && (
              <text x={point.x} y={Math.max(16, point.y - 14)} textAnchor="middle" className="fill-primary text-[10px] font-black">
                {valueFormatter ? valueFormatter(point.value, point.item) : point.value}
              </text>
            )}
          </g>
        ))}

        {tickIndexes.map((index) => {
          const point = points[index];
          return (
            <text key={`${point.item.label}-${index}`} x={point.x} y={height - 18} textAnchor="middle" className="fill-[var(--page-muted)] text-[10px] font-bold">
              {point.item.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

const StatusBreakdown = ({ items = [] }) => {
  const total = items.reduce((sum, item) => sum + (item.transactions || 0), 0);
  if (!total) {
    return <div className="rounded-[24px] bg-muted p-5 text-sm font-bold text-[var(--page-muted)]">Chưa có giao dịch.</div>;
  }
  return (
    <div className="space-y-3">
      {items.map((item) => {
        const percent = Math.round(((item.transactions || 0) / total) * 100);
        return (
          <div key={item.status}>
            <div className="mb-1 flex items-center justify-between text-sm font-bold">
              <span className="capitalize">{item.status}</span>
              <span>{item.transactions} · {percent}%</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const PlanRevenueSplit = ({ items = [], currency }) => {
  const maxRevenue = Math.max(...items.map((item) => item.paid_revenue_amount || 0), 0);
  if (!maxRevenue) {
    return <div className="rounded-[24px] bg-muted p-5 text-sm font-bold text-[var(--page-muted)]">Chưa có doanh thu theo gói.</div>;
  }
  return (
    <div className="space-y-4">
      {items.map((item) => {
        const percent = Math.max(4, ((item.paid_revenue_amount || 0) / maxRevenue) * 100);
        return (
          <div key={item.plan_code}>
            <div className="mb-1 flex items-center justify-between gap-3 text-sm font-bold">
              <span>{item.plan_code}</span>
              <span>{formatCurrency(item.paid_revenue_amount, currency)} · {item.paid_transactions}</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-emerald-500" style={{ width: `${percent}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const AdminDashboardPage = () => {
  const [period, setPeriod] = useState("day");
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await adminPaymentsApi.getDashboard(period);
      if (mountedRef.current) setDashboard(data);
    } catch (dashboardError) {
      if (mountedRef.current) setError(getApiErrorMessage(dashboardError, "Failed to load dashboard."));
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const overview = dashboard?.overview || {};
  const currency = dashboard?.currency || "VND";
  const kpis = useMemo(() => [
    { label: "Paid Revenue", value: formatCurrency(overview.paid_revenue_amount, overview.paid_revenue_currency || currency), hint: "Total paid payment revenue" },
    { label: "Paid Payments", value: overview.paid_transactions || 0, hint: "Successful transactions" },
    { label: "Pending", value: overview.pending_transactions || 0, hint: "Awaiting payment/review" },
    { label: "Failed / Cancelled", value: (overview.failed_transactions || 0) + (overview.cancelled_transactions || 0), hint: "Unsuccessful transactions" },
  ], [currency, overview]);

  return (
    <AdminShell title="Admin Dashboard" subtitle="Payment analytics, revenue trends, and quick operational snapshots.">
      <div className="space-y-6">
        {error && <div className="rounded-[26px] bg-rose-50 px-5 py-4 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error}</div>}

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex rounded-2xl bg-muted p-1">
            {STATS_PERIODS.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setPeriod(item.value)}
                className={`rounded-xl px-4 py-2 text-sm font-black transition ${period === item.value ? "bg-card text-primary shadow-sm" : "text-[var(--page-muted)] hover:text-[var(--page-fg)]"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <button type="button" onClick={() => void loadDashboard()} className="inline-flex items-center gap-2 rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-[var(--page-muted)] transition hover:bg-muted">
            <ArrowClockwise size={16} /> Refresh
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => <KpiCard key={kpi.label} {...kpi} />)}
        </div>

        {isLoading && <div className="rounded-[30px] border border-border bg-card p-8 text-sm font-bold text-[var(--page-muted)]">Đang tải dashboard...</div>}

        {!isLoading && dashboard && (
          <>
            <div>
              <ChartCard eyebrow="Revenue Trend" title="Doanh thu đã thanh toán">
                <AreaTrendChart
                  items={dashboard.revenue_trend}
                  valueKey="paid_revenue_amount"
                  currency={currency}
                  emptyText="Chưa có doanh thu đã thanh toán."
                  valueFormatter={(value, item) => formatCurrency(value, item.currency || currency)}
                  titleFormatter={(item) => `${item.label}: ${formatCurrency(item.paid_revenue_amount, item.currency || currency)} · ${item.paid_transactions} giao dịch`}
                />
              </ChartCard>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <ChartCard eyebrow="Status Breakdown" title="Trạng thái payment">
                <StatusBreakdown items={dashboard.status_breakdown} />
              </ChartCard>
              <ChartCard eyebrow="Plan Revenue Split" title="Doanh thu theo gói">
                <PlanRevenueSplit items={dashboard.plan_revenue_split} currency={currency} />
              </ChartCard>
            </div>

            <ChartCard
              eyebrow="Recent Payments"
              title="Giao dịch mới nhất"
              action={<Link to="/admin/payments" className="rounded-2xl border border-border px-4 py-3 text-sm font-bold text-primary transition hover:bg-muted">Mở Payments</Link>}
            >
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--page-muted)]">
                    <tr>
                      <th className="px-3 py-2">Order</th>
                      <th className="px-3 py-2">Customer</th>
                      <th className="px-3 py-2">Plan</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Amount</th>
                      <th className="px-3 py-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(dashboard.recent_payments || []).map((payment) => (
                      <tr key={payment.id} className="border-t border-border">
                        <td className="px-3 py-3 font-mono text-xs">{payment.order_code}</td>
                        <td className="px-3 py-3">{payment.user_email}</td>
                        <td className="px-3 py-3">{payment.plan_code || payment.plan}</td>
                        <td className="px-3 py-3 capitalize">{payment.status}</td>
                        <td className="px-3 py-3 font-bold">{formatCurrency(payment.amount, payment.currency)}</td>
                        <td className="px-3 py-3 text-[var(--page-muted)]">{formatDateTime(payment.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(dashboard.recent_payments || []).length === 0 && <p className="rounded-[24px] bg-muted p-5 text-sm font-bold text-[var(--page-muted)]">Chưa có payment gần đây.</p>}
              </div>
            </ChartCard>
          </>
        )}
      </div>
    </AdminShell>
  );
};

export default AdminDashboardPage;
