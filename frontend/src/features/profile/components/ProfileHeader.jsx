import { motion } from "framer-motion";
import { Crown, PencilSimple, Target } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getSubscriptionLabel } from "@/features/auth/utils/subscription";

const ProfileHeader = () => {
  const { user, isSubscribed } = useAuth();
  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";
  const subtitle = [
    user?.level?.toUpperCase?.(),
    user?.native_language?.toUpperCase?.(),
    user?.target_language?.toUpperCase?.(),
  ].filter(Boolean).join(" | ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="md:col-span-8 bg-white border border-zinc-200 rounded-[2.5rem] p-8 shadow-sm flex flex-col md:flex-row items-center gap-8 group hover:shadow-xl transition-all duration-300"
    >
      <div className="relative">
        <div className="w-32 h-32 rounded-3xl overflow-hidden shadow-2xl relative z-10 bg-primary/10 flex items-center justify-center text-4xl font-black text-primary">
          {displayName.charAt(0).toUpperCase()}
        </div>
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3 }}
          className="absolute -bottom-2 -right-2 bg-primary text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg z-20 border-2 border-white"
        >
          {getSubscriptionLabel(user?.subscription)}
        </motion.div>
      </div>

      <div className="text-center md:text-left flex-1">
        <h2 className="text-3xl font-black text-zinc-950 font-display">{displayName}</h2>
        <div className="flex items-center justify-center md:justify-start gap-2 mt-2 text-zinc-400 font-bold uppercase tracking-widest text-[10px]">
          <Target size={14} weight="bold" className="text-primary" />
          <span>{subtitle || "Complete your profile to personalize practice."}</span>
        </div>
        
        <div className="mt-8 flex flex-wrap gap-3 justify-center md:justify-start">
          <motion.button
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
            className="bg-primary text-white px-6 py-2.5 rounded-2xl font-bold text-xs shadow-lg shadow-primary/20 flex items-center gap-2 btn-spring"
          >
            <PencilSimple weight="bold" size={16} />
            Edit Profile
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
            className="bg-zinc-100 text-zinc-900 px-6 py-2.5 rounded-2xl font-bold text-xs hover:bg-zinc-200 transition-colors flex items-center gap-2"
          >
            <Crown weight="bold" size={16} />
            {isSubscribed ? "Subscription Active" : "Free Plan"}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

export default ProfileHeader;
