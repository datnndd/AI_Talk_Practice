import { motion } from "framer-motion";
import { ChartLineUp, ClockCountdown, Target } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const GoalProgress = () => {
  const { user } = useAuth();
  const dailyGoal = user?.daily_goal ?? 15;
  const level = user?.level?.toUpperCase?.() || "BEGINNER";
  const targetLanguage = user?.target_language?.toUpperCase?.() || "EN";
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const completionRatio = 0.72;
  const offset = circumference * (1 - completionRatio);

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="app-panel rounded-[2rem] p-7"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">Daily Target</p>
          <h3 className="mt-2 text-2xl font-black text-[var(--page-fg)]">Practice Pulse</h3>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-500">
          <ChartLineUp weight="bold" size={22} />
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-[140px,1fr] md:items-center">
        <div className="relative mx-auto flex h-36 w-36 items-center justify-center">
          <svg className="h-full w-full -rotate-90">
            <circle cx="72" cy="72" r={radius} fill="transparent" stroke="rgba(148,163,184,0.18)" strokeWidth="10" />
            <motion.circle
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
              cx="72"
              cy="72"
              r={radius}
              fill="transparent"
              stroke="#10b981"
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute text-center">
            <span className="block text-4xl font-black tracking-tight text-[var(--page-fg)]">{dailyGoal}</span>
            <span className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">mins per day</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="app-panel-soft rounded-[1.4rem] p-4">
            <div className="flex items-center gap-2 text-[var(--page-fg)]">
              <Target size={16} weight="bold" className="text-primary" />
              <span className="text-sm font-black">Current track</span>
            </div>
            <p className="app-text-muted mt-2 text-sm leading-6">
              {targetLanguage} speaking mode with <span className="font-black text-[var(--page-fg)]">{level}</span> level pacing.
            </p>
          </div>

          <div className="app-panel-soft rounded-[1.4rem] p-4">
            <div className="flex items-center gap-2 text-[var(--page-fg)]">
              <ClockCountdown size={16} weight="bold" className="text-primary" />
              <span className="text-sm font-black">Coaching rhythm</span>
            </div>
            <p className="app-text-muted mt-2 text-sm leading-6">
              Keep the target realistic. Consistency matters more than intensity on speaking retention.
            </p>
          </div>
        </div>
      </div>
    </motion.section>
  );
};

export default GoalProgress;
