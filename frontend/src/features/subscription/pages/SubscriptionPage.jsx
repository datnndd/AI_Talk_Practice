import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, Crown, Lightning } from "@phosphor-icons/react";
import { Link, useSearchParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import {
  createCheckoutSession,
  getCheckoutStatus,
  listSubscriptionPlans,
  quotePromotionCode,
} from "@/features/subscription/api/paymentsApi";

const formatVnd = (amount = 0) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(amount);

const formatDuration = (days) => {
  if (days >= 365) return "1 năm";
  if (days >= 180) return "6 tháng";
  return `${days} ngày`;
};

const planAccent = {
  PRO_30D: "from-amber-300 to-yellow-500",
  PRO_6M: "from-purple-400 to-amber-400",
  PRO_1Y: "from-yellow-300 via-amber-400 to-purple-500",
};

const SubscriptionPage = () => {
  const { user, isSubscribed, refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState([]);
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);
  const [promoCode, setPromoCode] = useState("");
  const [quotes, setQuotes] = useState({});
  const [promoMessage, setPromoMessage] = useState("");
  const [submittingPlan, setSubmittingPlan] = useState(null);
  const [actionError, setActionError] = useState("");
  const [isSyncingPayment, setIsSyncingPayment] = useState(false);

  const paymentStatus = searchParams.get("payment");
  const paymentProvider = searchParams.get("provider");
  const paymentCode = searchParams.get("code");
  const paymentOrderCode = searchParams.get("order_code");

  useEffect(() => {
    let isMounted = true;
    const loadPlans = async () => {
      setIsLoadingPlans(true);
      setActionError("");
      try {
        const data = await listSubscriptionPlans();
        if (isMounted) setPlans(Array.isArray(data) ? data : []);
      } catch (error) {
        if (isMounted) setActionError(error?.response?.data?.detail || "Không thể tải gói Pro.");
      } finally {
        if (isMounted) setIsLoadingPlans(false);
      }
    };
    void loadPlans();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (paymentStatus !== "success" || !paymentOrderCode) return undefined;
    let isCancelled = false;
    let timeoutId;

    const syncPaymentStatus = async () => {
      setIsSyncingPayment(true);
      try {
        for (let attempt = 0; attempt < 6; attempt += 1) {
          const payment = await getCheckoutStatus(paymentOrderCode);
          if (isCancelled) return;
          if (payment.status === "paid") {
            await refreshUser();
            return;
          }
          if (payment.status === "failed" || payment.status === "expired") {
            setActionError(payment.failure_reason || "Payment was not completed successfully.");
            return;
          }
          await new Promise((resolve) => {
            timeoutId = window.setTimeout(resolve, 1500);
          });
        }
        await refreshUser();
      } catch (error) {
        if (!isCancelled) setActionError(error?.response?.data?.detail || "Unable to confirm payment status yet.");
      } finally {
        if (!isCancelled) setIsSyncingPayment(false);
      }
    };

    syncPaymentStatus();
    return () => {
      isCancelled = true;
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [paymentOrderCode, paymentStatus, refreshUser]);

  const paymentMessage = useMemo(() => {
    if (!paymentStatus) return null;
    if (paymentStatus === "success") {
      return {
        tone: "success",
        text: isSyncingPayment
          ? `Thanh toán qua ${paymentProvider?.toUpperCase() || "Stripe"} xong. Đang đồng bộ Pro...`
          : `Thanh toán qua ${paymentProvider?.toUpperCase() || "Stripe"} xong. Gói Pro đã được cập nhật.`,
      };
    }
    if (paymentStatus === "cancelled") {
      return { tone: "neutral", text: "Bạn đã hủy thanh toán. Có thể chọn lại gói bất cứ lúc nào." };
    }
    return { tone: "error", text: `Thanh toán lỗi${paymentCode ? `: ${paymentCode}` : ""}. Vui lòng thử lại.` };
  }, [isSyncingPayment, paymentCode, paymentProvider, paymentStatus]);

  const applyPromoCode = async () => {
    const code = promoCode.trim();
    if (!code) {
      setQuotes({});
      setPromoMessage("");
      return;
    }
    try {
      setActionError("");
      const nextQuotes = {};
      for (const plan of plans) {
        nextQuotes[plan.code] = await quotePromotionCode({ plan_code: plan.code, promo_code: code });
      }
      setQuotes(nextQuotes);
      setPromoMessage(`Đã áp dụng mã ${code.toUpperCase()}.`);
    } catch (error) {
      setQuotes({});
      setPromoMessage("");
      setActionError(error?.response?.data?.detail || "Mã giảm giá không hợp lệ.");
    }
  };

  const handleCheckout = async (plan) => {
    try {
      setActionError("");
      setSubmittingPlan(plan.code);
      const checkout = await createCheckoutSession({
        provider: "stripe",
        plan: "PRO",
        plan_code: plan.code,
        promo_code: promoCode.trim() || undefined,
      });
      window.location.assign(checkout.checkout_url);
    } catch (error) {
      setActionError(error?.response?.data?.detail || "Không thể mở Stripe Checkout.");
      setSubmittingPlan(null);
    }
  };

  const bestMonthly = plans.length
    ? Math.min(...plans.map((plan) => plan.price_amount / Math.max(plan.duration_days / 30, 1)))
    : 0;

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 pb-12">
      {paymentMessage ? (
        <div className={`rounded-[1.5rem] border px-5 py-4 text-sm font-semibold shadow-sm ${
          paymentMessage.tone === "success"
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : paymentMessage.tone === "error"
              ? "border-rose-200 bg-rose-50 text-rose-700"
              : "border-zinc-200 bg-zinc-50 text-zinc-700"
        }`}>
          {paymentMessage.text}
        </div>
      ) : null}

      <section className="overflow-hidden rounded-[2rem] bg-gradient-to-br from-zinc-950 via-purple-950 to-amber-500 p-8 text-white shadow-2xl">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-amber-200">
              <Crown weight="fill" size={14} /> Pro Pricing
            </span>
            <h1 className="mt-4 font-display text-4xl font-black tracking-tight">
              {isSubscribed ? "Gia hạn Pro theo nhu cầu" : "Chọn gói Pro phù hợp"}
            </h1>
            <p className="mt-3 max-w-xl text-sm font-semibold leading-7 text-white/75">
              Mở khóa kịch bản VIP, AI tutor và phản hồi nâng cao. Thanh toán bằng Stripe, thời hạn được cộng dồn nếu bạn đang còn Pro.
            </p>
          </div>
          <div className="rounded-3xl bg-white/10 p-5 backdrop-blur">
            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-white/55">Trạng thái</p>
            <p className="mt-2 text-2xl font-black">{isSubscribed ? "Pro active" : "Free account"}</p>
            {user?.subscription?.expires_at ? <p className="mt-1 text-xs font-bold text-amber-100">Hết hạn: {new Date(user.subscription.expires_at).toLocaleDateString("vi-VN")}</p> : null}
          </div>
        </div>
      </section>

      <section className="rounded-[2rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-amber-700">Mã giảm giá</p>
            <p className="mt-1 text-sm font-semibold text-amber-900">Nhập mã admin tạo, ví dụ giảm 10% hoặc 20%.</p>
          </div>
          <div className="flex w-full gap-2 md:w-auto">
            <input value={promoCode} onChange={(event) => setPromoCode(event.target.value)} placeholder="PROMO10" className="min-w-0 flex-1 rounded-2xl border border-amber-200 bg-white px-4 py-3 text-sm font-bold uppercase text-zinc-900 outline-none focus:ring-2 focus:ring-amber-300 md:w-56" />
            <button type="button" onClick={applyPromoCode} className="rounded-2xl bg-zinc-950 px-5 py-3 text-xs font-black uppercase tracking-[0.16em] text-white">
              Áp dụng
            </button>
          </div>
        </div>
        {promoMessage ? <p className="mt-3 text-sm font-black text-emerald-700">{promoMessage}</p> : null}
      </section>

      {isLoadingPlans ? (
        <div className="flex min-h-[260px] items-center justify-center"><div className="h-10 w-10 animate-spin rounded-full border-b-2 border-amber-500" /></div>
      ) : (
        <section className="grid gap-5 lg:grid-cols-3">
          {plans.map((plan) => {
            const quote = quotes[plan.code];
            const amount = quote?.amount ?? plan.price_amount;
            const discountAmount = quote?.discount_amount ?? 0;
            const monthly = plan.price_amount / Math.max(plan.duration_days / 30, 1);
            const savingPercent = bestMonthly && monthly > bestMonthly ? Math.round((1 - bestMonthly / monthly) * 100) : 0;
            return (
              <motion.article key={plan.code} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="relative overflow-hidden rounded-[2rem] border border-zinc-200 bg-white p-7 shadow-sm">
                <div className={`absolute inset-x-0 top-0 h-2 bg-gradient-to-r ${planAccent[plan.code] || "from-amber-300 to-yellow-500"}`} />
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.2em] text-amber-600">{formatDuration(plan.duration_days)}</p>
                    <h2 className="mt-2 font-display text-3xl font-black text-zinc-950">{plan.name}</h2>
                  </div>
                  <div className="rounded-2xl bg-amber-100 p-3 text-amber-700"><Crown size={24} weight="fill" /></div>
                </div>
                <div className="mt-7">
                  <p className="text-4xl font-black tracking-tight text-zinc-950">{formatVnd(amount)}</p>
                  {discountAmount > 0 ? <p className="mt-2 text-sm font-bold text-emerald-600">Đã giảm {formatVnd(discountAmount)} từ {formatVnd(plan.price_amount)}</p> : null}
                  {savingPercent > 0 ? <p className="mt-2 inline-flex rounded-full bg-purple-50 px-3 py-1 text-xs font-black text-purple-700">Tiết kiệm khoảng {savingPercent}%/tháng</p> : null}
                </div>
                <ul className="mt-7 space-y-3 text-sm font-semibold text-zinc-600">
                  {["Kịch bản VIP", "AI tutor không giới hạn", "Advanced feedback"].map((item) => (
                    <li key={item} className="flex items-center gap-2"><CheckCircle size={17} weight="fill" className="text-emerald-500" />{item}</li>
                  ))}
                </ul>
                <button type="button" onClick={() => handleCheckout(plan)} disabled={submittingPlan !== null} className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-zinc-950 px-5 py-3 text-xs font-black uppercase tracking-[0.18em] text-white shadow-lg transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60">
                  <Lightning size={16} weight="fill" />
                  {submittingPlan === plan.code ? "Đang chuyển..." : isSubscribed ? `Gia hạn thêm ${plan.duration_days} ngày` : "Thanh toán với Stripe"}
                </button>
              </motion.article>
            );
          })}
        </section>
      )}

      {actionError ? <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm font-semibold text-rose-700 shadow-sm">{actionError}</div> : null}

      {isSubscribed ? (
        <Link to="/dashboard" className="inline-flex rounded-2xl border border-zinc-200 px-5 py-3 text-sm font-black text-zinc-700 hover:bg-zinc-50">Tiếp tục luyện tập</Link>
      ) : null}
    </div>
  );
};

export default SubscriptionPage;
