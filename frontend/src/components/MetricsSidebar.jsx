import { motion } from "framer-motion";
import { Sparkle, Clock, BookOpen, SignOut } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";

const MetricBar = ({ label, score, color }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-end">
      <label className="text-sm font-bold text-zinc-900">{label}</label>
      <span className={`text-xs font-mono font-bold ${color}`}>{score}%</span>
    </div>
    <div className="w-full bg-zinc-100 rounded-full h-1.5 overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${score}%` }}
        className={`h-full rounded-full ${color.replace('text', 'bg')}`}
      />
    </div>
  </div>
);

const MetricsSidebar = () => {
  const navigate = useNavigate();

  return (
    <aside className="lg:col-span-4 flex flex-col gap-6 h-full">
      <section className="liquid-glass rounded-4xl p-8 flex-1 border border-white/20 shadow-xl refraction">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-10">Real-time Feedback</h3>
        <div className="space-y-10">
          <MetricBar label="Pronunciation" score={88} color="text-emerald-500" />
          <MetricBar label="Grammar" score={92} color="text-primary" />
          <MetricBar label="Fluency" score={74} color="text-amber-500" />
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="mt-12 p-5 rounded-2xl bg-primary/5 border border-primary/10"
        >
          <div className="flex items-center gap-2 mb-3">
            <Sparkle weight="fill" className="text-primary" size={16} />
            <h4 className="text-[10px] font-bold text-primary uppercase tracking-widest">Pro Tip</h4>
          </div>
          <p className="text-xs leading-relaxed text-zinc-600 font-medium">
            Focus on the "R" sound in "Bourguignon". Try placing your tongue slightly further back.
          </p>
        </motion.div>
      </section>

      <section className="liquid-glass rounded-4xl p-8 h-fit border border-white/20 shadow-xl refraction">
        <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-6">Session Info</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-100">
            <div className="flex items-center gap-2 mb-1 text-zinc-400">
              <Clock size={14} />
              <span className="text-[9px] font-bold uppercase tracking-wider">Duration</span>
            </div>
            <span className="text-xl font-mono font-bold text-zinc-900">12:45</span>
          </div>
          <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-100">
            <div className="flex items-center gap-2 mb-1 text-zinc-400">
              <BookOpen size={14} />
              <span className="text-[9px] font-bold uppercase tracking-wider">Vocab</span>
            </div>
            <span className="text-xl font-mono font-bold text-zinc-900">+24</span>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate("/topics")}
          className="w-full mt-6 py-4 bg-white border border-zinc-200 rounded-2xl text-[10px] font-bold text-rose-500 hover:bg-rose-50 hover:border-rose-100 transition-all uppercase tracking-[0.2em] flex items-center justify-center gap-2"
        >
          <SignOut weight="bold" />
          End Session
        </motion.button>
      </section>
    </aside>
  );
};

export default MetricsSidebar;
