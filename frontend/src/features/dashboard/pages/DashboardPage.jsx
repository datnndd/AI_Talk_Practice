import { motion } from "framer-motion";
import ProgressCircle from "@/features/dashboard/components/ProgressCircle";
import StreakCard from "@/features/dashboard/components/StreakCard";
import LessonStack from "@/features/dashboard/components/LessonStack";
import QuickPracticeCard from "@/features/dashboard/components/QuickPracticeCard";
import { useAuth } from "@/features/auth/context/AuthContext";

const Dashboard = () => {
  const { user, isSubscribed, subscriptionTier } = useAuth();
  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-12 flex items-end justify-between gap-6 px-2">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Daily Briefing</p>
          <h1 className="mt-4 text-4xl font-black tracking-tight text-zinc-950 font-display md:text-5xl">
            Good afternoon, <span className="text-primary italic">{displayName}</span>
          </h1>
          <p className="mt-3 text-xs font-bold uppercase tracking-widest text-zinc-500">
            {isSubscribed
              ? `Subscriber mode enabled. ${subscriptionTier} practice is unlocked.`
              : "Free mode enabled. Browse topics and upgrade to start live AI practice."}
          </p>
        </motion.div>

        <div className="hidden items-center -space-x-3 md:flex">
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="h-11 w-11 overflow-hidden rounded-full border-4 border-white shadow-sm"
            >
              <img src={`https://i.pravatar.cc/150?u=${i}`} alt="Buddy" className="h-full w-full object-cover" />
            </motion.div>
          ))}
          <div className="z-10 flex h-11 w-11 cursor-pointer items-center justify-center rounded-full border-4 border-white bg-zinc-100 text-[10px] font-black text-zinc-400 shadow-sm transition-transform hover:scale-110">
            +2
          </div>
        </div>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid auto-rows-[160px] grid-cols-1 gap-6 md:grid-cols-12"
      >
        <ProgressCircle />
        <StreakCard />
        <QuickPracticeCard />
        <LessonStack />
      </motion.div>
    </div>
  );
};

export default Dashboard;
