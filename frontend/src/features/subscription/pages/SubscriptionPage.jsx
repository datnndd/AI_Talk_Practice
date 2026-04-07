import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle,
  CreditCard,
  Crown,
  Lightning,
  Sparkle,
  Wallet,
} from "@phosphor-icons/react";
import { Link, useSearchParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getSubscriptionLabel } from "@/features/auth/utils/subscription";
import { createCheckoutSession } from "@/features/subscription/api/paymentsApi";

const subscriberBenefits = [
  "Unlimited live AI speaking practice sessions",
  "Priority access to advanced roleplay scenarios",
  "Premium tutor flows and richer conversation guidance",
];

const freeBenefits = [
  "Browse topics and preview the learning experience",
  "Complete onboarding and maintain your language profile",
  "Upgrade anytime when you are ready for live practice",
];

const paymentOptions = [
  {
    provider: "stripe",
    title: "Stripe",
    badge: "Global cards",
    description: "Pay by international credit/debit card with Stripe Checkout.",
    amountLabel: "$99.00 / 30 days",
    icon: CreditCard,
  },
  {
    provider: "vnpay",
    title: "VNPay",
    badge: "Vietnam local",
    description: "Pay through Vietnamese banking methods using VNPay redirect checkout.",
    amountLabel: "199,000 VND / 30 days",
    icon: Wallet,
  },
];

const SubscriptionPage = () => {
  const { user, isSubscribed, subscriptionTier, hasActiveSubscription, refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [submittingProvider, setSubmittingProvider] = useState(null);
  const [actionError, setActionError] = useState("");
  const currentPlanLabel = getSubscriptionLabel(user?.subscription);
  const paymentStatus = searchParams.get("payment");
  const paymentProvider = searchParams.get("provider");
  const paymentCode = searchParams.get("code");

  useEffect(() => {
    if (paymentStatus === "success") {
      refreshUser();
    }
  }, [paymentStatus, refreshUser]);

  const paymentMessage = useMemo(() => {
    if (!paymentStatus) {
      return null;
    }

    if (paymentStatus === "success") {
      return {
        tone: "success",
        text: `Payment via ${paymentProvider?.toUpperCase() || "gateway"} completed. Your subscription has been refreshed.`,
      };
    }

    if (paymentStatus === "cancelled") {
      return {
        tone: "neutral",
        text: "Checkout was cancelled. You can retry whenever you are ready.",
      };
    }

    return {
      tone: "error",
      text: `Payment failed${paymentCode ? ` with code ${paymentCode}` : ""}. Please verify the gateway response and retry.`,
    };
  }, [paymentCode, paymentProvider, paymentStatus]);

  const handleCheckout = async (provider) => {
    try {
      setActionError("");
      setSubmittingProvider(provider);
      const payload = provider === "vnpay"
        ? { provider, plan: "PRO", locale: "vn" }
        : { provider, plan: "PRO" };
      const checkout = await createCheckoutSession(payload);
      window.location.assign(checkout.checkout_url);
    } catch (error) {
      setActionError(error?.response?.data?.detail || "Unable to start checkout.");
      setSubmittingProvider(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {paymentMessage && (
        <div
          className={[
            "rounded-[1.5rem] border px-5 py-4 text-sm font-semibold shadow-sm",
            paymentMessage.tone === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : paymentMessage.tone === "error"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-zinc-200 bg-zinc-50 text-zinc-700",
          ].join(" ")}
        >
          {paymentMessage.text}
        </div>
      )}

      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-[2rem] border border-zinc-200 bg-white p-8 shadow-sm"
      >
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-primary">
              <Crown weight="fill" size={14} />
              Subscription
            </span>
            <h1 className="mt-4 text-4xl font-black tracking-tight text-zinc-950 font-display">
              {isSubscribed ? "Your subscription is active." : "Free plan detected."}
            </h1>
            <p className="mt-3 max-w-xl text-sm font-medium leading-7 text-zinc-500">
              Choose Stripe or VNPay to pay online and upgrade immediately.
              The backend verifies each callback before activating premium speaking access.
            </p>
          </div>

          <div className="rounded-[1.5rem] bg-zinc-950 px-6 py-5 text-white shadow-xl">
            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-white/50">Current plan</p>
            <p className="mt-2 text-2xl font-black">{currentPlanLabel}</p>
            <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-emerald-300">
              {hasActiveSubscription ? "Status: active" : "Status: free"}
            </p>
          </div>
        </div>
      </motion.section>

      <section className="grid gap-6 lg:grid-cols-2">
        <motion.article
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-[2rem] border border-zinc-200 bg-white p-8 shadow-sm"
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-400">Free</p>
              <h2 className="mt-2 text-3xl font-black font-display text-zinc-950">Explore mode</h2>
            </div>
            <Sparkle size={32} className="text-zinc-300" />
          </div>

          <ul className="mt-8 space-y-4">
            {freeBenefits.map((benefit) => (
              <li key={benefit} className="flex items-start gap-3 text-sm font-medium text-zinc-600">
                <CheckCircle weight="fill" size={18} className="mt-0.5 shrink-0 text-zinc-400" />
                <span>{benefit}</span>
              </li>
            ))}
          </ul>
        </motion.article>

        <motion.article
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-[2rem] bg-gradient-to-br from-primary to-indigo-600 p-8 text-white shadow-2xl"
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.2em] text-white/60">
                {subscriptionTier === "FREE" ? "Subscription" : currentPlanLabel}
              </p>
              <h2 className="mt-2 text-3xl font-black font-display">
                Unlock live AI speaking practice
              </h2>
            </div>
            <Lightning weight="fill" size={32} className="text-amber-300" />
          </div>

          <ul className="mt-8 space-y-4">
            {subscriberBenefits.map((benefit) => (
              <li key={benefit} className="flex items-start gap-3 text-sm font-medium text-white/85">
                <CheckCircle weight="fill" size={18} className="mt-0.5 shrink-0 text-amber-300" />
                <span>{benefit}</span>
              </li>
            ))}
          </ul>

          <div className="mt-10">
            <Link
              to={isSubscribed ? "/topics" : "/profile"}
              className="inline-flex items-center justify-center rounded-2xl bg-amber-400 px-6 py-3 text-xs font-black uppercase tracking-[0.2em] text-zinc-950 shadow-xl shadow-amber-900/20 transition-transform hover:-translate-y-0.5"
            >
              {isSubscribed ? "Go to practice topics" : "Review your profile"}
            </Link>
          </div>
        </motion.article>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        {paymentOptions.map(({ provider, title, badge, description, amountLabel, icon: Icon }) => (
          <motion.article
            key={provider}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-[2rem] border border-zinc-200 bg-white p-8 shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-400">{badge}</p>
                <h2 className="mt-2 text-3xl font-black font-display text-zinc-950">{title}</h2>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 text-zinc-700">
                <Icon size={24} weight="fill" />
              </div>
            </div>

            <p className="mt-4 text-sm font-medium leading-7 text-zinc-500">{description}</p>
            <p className="mt-6 text-xl font-black tracking-tight text-zinc-950">{amountLabel}</p>

            <button
              type="button"
              onClick={() => handleCheckout(provider)}
              disabled={submittingProvider !== null}
              className="mt-8 inline-flex w-full items-center justify-center rounded-2xl bg-primary px-6 py-3 text-xs font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submittingProvider === provider ? "Redirecting..." : `Pay with ${title}`}
            </button>
          </motion.article>
        ))}
      </section>

      {actionError && (
        <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm font-semibold text-rose-700 shadow-sm">
          {actionError}
        </div>
      )}

      {hasActiveSubscription && (
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[2rem] border border-zinc-200 bg-white p-8 shadow-sm"
        >
          <h2 className="text-2xl font-black tracking-tight text-zinc-950 font-display">Already active</h2>
          <p className="mt-3 max-w-2xl text-sm font-medium leading-7 text-zinc-500">
            Paying again will extend your premium access on top of the remaining subscription period.
          </p>
          <div className="mt-6">
            <Link
              to="/topics"
              className="inline-flex items-center justify-center rounded-2xl border border-zinc-200 px-6 py-3 text-xs font-black uppercase tracking-[0.2em] text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
            >
              Continue practicing
            </Link>
          </div>
        </motion.section>
      )}
    </div>
  );
};

export default SubscriptionPage;
