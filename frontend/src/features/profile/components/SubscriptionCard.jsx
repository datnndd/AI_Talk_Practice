import { motion } from "framer-motion";
import { ArrowUpRight, Crown, ShieldCheck } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getSubscriptionLabel } from "@/features/auth/utils/subscription";

const SubscriptionCard = () => {
  const { user, isSubscribed, hasActiveSubscription } = useAuth();
  const label = getSubscriptionLabel(user?.subscription);
  const expiresAt = user?.subscription?.expires_at
    ? new Date(user.subscription.expires_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="overflow-hidden rounded-[2rem] border border-primary/15 bg-[linear-gradient(145deg,rgba(0,90,182,0.12),rgba(14,165,233,0.08)_58%,rgba(255,255,255,0.02))] p-7 shadow-[0_24px_60px_-32px_rgba(0,90,182,0.34)]"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.22em] text-primary/80">Plan Status</p>
          <h3 className="mt-2 text-3xl font-black tracking-tight text-[var(--page-fg)]">
            {isSubscribed ? `${label} Plan` : "Free Plan"}
          </h3>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/60 text-primary shadow-sm">
          {isSubscribed ? <ShieldCheck weight="fill" size={24} /> : <Crown weight="fill" size={24} />}
        </div>
      </div>

      <p className="app-text-muted mt-4 text-sm leading-6">
        {hasActiveSubscription
          ? expiresAt
            ? `Access is active through ${expiresAt}.`
            : "Your plan is active and ready for premium speaking sessions."
          : "You are currently on the free plan. Upgrade to unlock premium topics and advanced coaching."}
      </p>

      <div className="mt-6 grid gap-3">
        <div className="app-panel-soft rounded-[1.35rem] p-4">
          <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">Access level</p>
          <p className="mt-2 text-lg font-black text-[var(--page-fg)]">{isSubscribed ? "Premium coaching unlocked" : "Core practice unlocked"}</p>
        </div>
      </div>

      <Link to="/subscription" className="mt-6 block">
        <motion.span
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
          className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-primary px-5 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20"
        >
          {isSubscribed ? "Manage plan" : "Upgrade access"}
          <ArrowUpRight weight="bold" size={16} />
        </motion.span>
      </Link>
    </motion.section>
  );
};

export default SubscriptionCard;
