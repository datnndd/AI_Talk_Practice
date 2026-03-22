import { motion } from "framer-motion";

const ProgressCircle = () => {
  const percentage = 85;
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <section className="md:col-span-4 md:row-span-2 bento-card rounded-[2.5rem] p-8 flex flex-col items-center justify-center shadow-lg relative overflow-hidden group">
      <div className="absolute top-0 left-0 w-full h-1 bg-emerald-500/10 group-hover:bg-emerald-500/20 transition-colors" />
      
      <div className="relative w-48 h-48">
        <svg className="w-full h-full -rotate-90">
          <circle
            cx="96"
            cy="96"
            r={radius}
            fill="transparent"
            stroke="#F4F4F5"
            strokeWidth="8"
          />
          <motion.circle
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
            cx="96"
            cy="96"
            r={radius}
            fill="transparent"
            stroke="#10B981"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-4xl font-black text-zinc-950 font-mono tracking-tighter">{percentage}%</span>
          <span className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] mt-1">Weekly</span>
        </div>
      </div>

      <div className="mt-8 text-center">
        <h3 className="font-black text-xl text-zinc-950 font-display">Goal Status</h3>
        <p className="text-zinc-500 text-xs font-bold uppercase tracking-widest mt-2">Almost there! 3 more lessons left.</p>
      </div>
    </section>
  );
};

export default ProgressCircle;
