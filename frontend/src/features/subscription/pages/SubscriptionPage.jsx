import { motion } from "framer-motion";
import { CheckCircle, Crown, Sparkle, Lightning } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getSubscriptionLabel } from "@/features/auth/utils/subscription";
import TopBar from "@/shared/components/navigation/TopBar";
import Sidebar from "@/shared/components/navigation/Sidebar";
import MobileNav from "@/shared/components/navigation/MobileNav";

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

const SubscriptionPage = () => {
  const { user, isSubscribed, subscriptionTier, hasActiveSubscription } = useAuth();
  const currentPlanLabel = getSubscriptionLabel(user?.subscription);

  return (
    <div className="min-h-[100dvh] bg-zinc-50 flex flex-col">
      <TopBar />

      <div className="flex flex-1 pt-16">
        <Sidebar />

        <main className="flex-1 lg:ml-64 p-6 md:p-10 mb-24 lg:mb-0 overflow-y-auto">
          <div className="max-w-6xl mx-auto space-y-8">
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
                    Backend subscription state is now connected to the frontend.
                    Free accounts can browse and prepare. Active subscribers unlock the live AI practice flow.
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
                    {isSubscribed ? "Go to practice topics" : "Contact support to upgrade"}
                  </Link>
                </div>
              </motion.article>
            </section>
          </div>
        </main>
      </div>

      <MobileNav />
    </div>
  );
};

export default SubscriptionPage;
