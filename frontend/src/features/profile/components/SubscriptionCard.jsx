import { motion } from "framer-motion";
import { ShieldCheck } from "@phosphor-icons/react";
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="md:col-span-5 relative overflow-hidden bg-gradient-to-br from-primary to-indigo-600 rounded-[2.5rem] p-8 shadow-2xl text-white group"
    >
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-24 -mt-24 blur-3xl group-hover:bg-white/20 transition-all duration-700" />
      
      <div className="relative z-10 h-full flex flex-col">
        <div className="flex justify-between items-start">
          <div>
            <span className="bg-white/20 border border-white/20 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest mb-4 inline-block">Subscription</span>
            <h3 className="text-3xl font-black font-display tracking-tight">
              {isSubscribed ? `${label} Plan` : "Free Plan"}
            </h3>
          </div>
          <ShieldCheck weight="fill" size={48} className="text-white/40 group-hover:text-white/60 transition-colors" />
        </div>
        
        <p className="mt-4 text-white/70 font-bold text-xs uppercase tracking-widest">
          {hasActiveSubscription
            ? expiresAt
              ? `Active until ${expiresAt}`
              : "Subscription active"
            : "You are on the free plan"}
        </p>
        
        <div className="mt-12 flex-1 flex flex-col justify-end">
          <Link to="/subscription">
            <motion.span
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex bg-amber-400 text-zinc-900 w-full md:w-fit px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl shadow-amber-900/40 btn-spring"
            >
              {isSubscribed ? "View Plan Details" : "Upgrade Access"}
            </motion.span>
          </Link>
        </div>
      </div>
    </motion.div>
  );
};

export default SubscriptionCard;
