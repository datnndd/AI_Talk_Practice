import { motion } from "framer-motion";
import { Microphone } from "@phosphor-icons/react";

const QuickPracticeCard = () => {
  return (
    <section className="md:col-span-4 md:row-span-1 bento-card rounded-[2.5rem] p-8 bg-primary/5 shadow-lg border-primary/10 flex items-center justify-between group">
      <div className="flex flex-col gap-1 items-start">
        <span className="text-primary font-black text-[10px] tracking-[0.2em] uppercase mb-2">AI Tutor Live</span>
        <motion.button
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          className="bg-amber-400 hover:bg-amber-500 text-zinc-900 px-6 py-3 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] transition-all shadow-xl shadow-amber-900/10 btn-spring whitespace-nowrap"
        >
          Practice Speaking Now
        </motion.button>
      </div>
      
      <div className="w-14 h-14 rounded-2xl bg-white shadow-sm flex items-center justify-center text-primary group-hover:scale-110 group-hover:rotate-6 transition-all">
        <Microphone weight="fill" size={28} />
      </div>
    </section>
  );
};

export default QuickPracticeCard;
