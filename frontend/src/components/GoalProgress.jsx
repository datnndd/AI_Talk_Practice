import { motion } from "framer-motion";
import { ChartLineUp } from "@phosphor-icons/react";

const GoalProgress = () => {
  const percentage = 66;
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="md:col-span-4 bg-white border border-zinc-200 rounded-[2.5rem] p-8 shadow-sm group hover:shadow-xl transition-all duration-300"
    >
      <div className="flex justify-between items-start mb-8">
        <h3 className="font-bold text-lg text-zinc-950 font-display">Daily Goals</h3>
        <div className="p-2 bg-emerald-50 text-emerald-500 rounded-xl">
          <ChartLineUp weight="bold" size={20} />
        </div>
      </div>

      <div className="flex flex-col items-center">
        <div className="relative w-36 h-36 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90">
            <circle
              cx="72"
              cy="72"
              r={radius}
              fill="transparent"
              stroke="#F4F4F5"
              strokeWidth="10"
              className="transition-all"
            />
            <motion.circle
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
              cx="72"
              cy="72"
              r={radius}
              fill="transparent"
              stroke="#10B981"
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute text-center">
            <span className="block text-3xl font-black text-zinc-950 font-mono tracking-tighter">{percentage}%</span>
            <span className="text-[9px] uppercase text-zinc-400 font-black tracking-widest">Daily Progress</span>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1">Current Focus</p>
          <p className="text-xl font-bold text-zinc-950">French (B2)</p>
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-emerald-700 font-bold text-[10px] uppercase tracking-wider">20 / 30 mins</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default GoalProgress;
