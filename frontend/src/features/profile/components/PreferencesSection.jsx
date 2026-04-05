import { motion } from "framer-motion";
import { ListChecks, Calendar } from "@phosphor-icons/react";
import { useState } from "react";

const PreferencesSection = () => {
  const [feedback, setFeedback] = useState(true);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="md:col-span-6 bg-white border border-zinc-200 rounded-[2.5rem] p-8 shadow-sm hover:shadow-xl transition-all duration-300"
    >
      <h3 className="font-bold text-lg text-zinc-950 font-display mb-8">Learning Preferences</h3>
      
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-bold text-zinc-900 text-sm">Voice Feedback</span>
            <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">Real-time correction</span>
          </div>
          <div 
            onClick={() => setFeedback(!feedback)}
            className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 relative cursor-pointer ${feedback ? 'bg-emerald-500' : 'bg-zinc-200'}`}
          >
            <motion.div 
              animate={{ x: feedback ? 24 : 0 }}
              className="w-4 h-4 bg-white rounded-full shadow-sm"
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-bold text-zinc-900 text-sm">Difficulty Level</span>
            <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">Target proficiency</span>
          </div>
          <select className="bg-zinc-50 border-none rounded-xl text-[10px] font-black uppercase tracking-widest text-primary focus:ring-2 focus:ring-primary/20 cursor-pointer">
            <option>Beginner</option>
            <option selected>Intermediate</option>
            <option>Advanced</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="font-bold text-zinc-900 text-sm">Daily Reminders</span>
            <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest">Notification time</span>
          </div>
          <div className="flex items-center gap-3 px-4 py-2 bg-zinc-50 rounded-xl cursor-pointer hover:bg-zinc-100 transition-colors">
            <span className="text-xs font-mono font-bold text-zinc-900">08:00 AM</span>
            <Calendar weight="bold" size={14} className="text-zinc-400" />
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default PreferencesSection;
