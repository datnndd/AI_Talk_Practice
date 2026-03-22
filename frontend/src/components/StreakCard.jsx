import { motion } from "framer-motion";

const StreakCard = () => {
  return (
    <section className="md:col-span-4 md:row-span-1 bento-card rounded-[2.5rem] p-8 flex items-center justify-between shadow-lg group">
      <div>
        <p className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Current Streak</p>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-5xl font-black text-zinc-950 font-mono tracking-tighter transition-transform group-hover:scale-110 origin-left">12</span>
          <span className="text-zinc-500 font-black uppercase tracking-widest text-xs">days</span>
        </div>
      </div>

      <div className="relative">
        <div className="w-16 h-16 rounded-3xl bg-amber-50 flex items-center justify-center relative">
          <motion.div 
            animate={{ scale: [0.95, 1.05, 0.95], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="absolute inset-0 rounded-3xl bg-amber-400"
          />
          <svg className="w-8 h-8 text-amber-500 relative z-10" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2c-.5 0-1 .4-1 .9v1.1c-3.1.4-5.5 2.8-5.9 5.9H4c-.6 0-1 .4-1 1s.4 1 1 1h1.1c.4 3.1 2.8 5.5 5.9 5.9v1.1c0 .6.4 1 1 1s1-.4 1-1v-1.1c3.1-.4 5.5-2.8 5.9-5.9H20c.6 0 1-.4 1-1s-.4-1-1-1h-1.1c-.4-3.1-2.8-5.5-5.9-5.9V2.9c0-.5-.4-.9-1-.9z" />
          </svg>
        </div>
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border-2 border-white"></span>
        </span>
      </div>
    </section>
  );
};

export default StreakCard;
