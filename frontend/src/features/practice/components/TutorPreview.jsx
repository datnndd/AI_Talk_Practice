import { motion } from "framer-motion";
import { Gear, Microphone, Globe, Sparkle } from "@phosphor-icons/react";

const TutorPreview = () => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, x: 30 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      transition={{ delay: 0.4, type: "spring", stiffness: 100, damping: 20 }}
      className="relative"
    >
      <div className="relative animate-float">
        {/* Main Conversation Card */}
        <div className="liquid-glass p-8 rounded-[2.5rem] border border-white/40 shadow-diffusion relative z-20 overflow-hidden bg-white/60">
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-inner">
                <Sparkle weight="fill" size={32} />
              </div>
              <div>
                <h4 className="font-bold text-zinc-900 text-lg">Lingo AI Tutor</h4>
                <div className="text-[11px] text-secondary font-black uppercase tracking-[0.1em] flex items-center gap-2">
                  <span className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
                  Online & Listening
                </div>
              </div>
            </div>
            <div className="w-10 h-10 rounded-2xl bg-zinc-100/50 flex items-center justify-center backdrop-blur-sm cursor-pointer hover:bg-zinc-200 transition-colors">
              <Gear weight="bold" size={20} className="text-zinc-500" />
            </div>
          </div>

          <div className="space-y-6 mb-10">
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="bg-zinc-100/50 p-5 rounded-3xl rounded-tl-none max-w-[85%] border border-zinc-200/50"
            >
              <p className="text-sm text-zinc-800 leading-relaxed font-semibold">
                Bonjour! How would you describe your weekend plans in French?
              </p>
            </motion.div>

            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 1.2 }}
              className="bg-primary p-5 rounded-3xl rounded-tr-none max-w-[85%] ml-auto text-white shadow-xl shadow-primary/20"
            >
              <p className="text-sm leading-relaxed font-semibold">
                Je vais aller au parc avec mes amis ce samedi.
              </p>
            </motion.div>

            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.6 }}
              className="bg-secondary/10 border border-secondary/20 p-5 rounded-3xl flex flex-col gap-3"
            >
              <div className="flex items-center gap-2">
                <Sparkle weight="bold" className="text-secondary" size={18} />
                <p className="text-[11px] font-black text-secondary uppercase tracking-[0.1em]">Smart Feedback</p>
              </div>
              <p className="text-sm text-zinc-700 leading-relaxed italic font-medium">
                That sentence is clear. Try adding one more detail about where you will meet your friends.
              </p>
            </motion.div>
          </div>

          <div className="flex items-center justify-between pt-6 border-t border-zinc-100/50">
            <div className="flex gap-3">
              <button className="w-11 h-11 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-500 hover:bg-zinc-200 transition-colors">
                <Microphone weight="fill" size={22} />
              </button>
              <button className="w-11 h-11 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-500 hover:bg-zinc-200 transition-colors">
                <Globe weight="bold" size={22} />
              </button>
            </div>
            
            <div className="flex -space-x-3">
               <img
                  alt="Current User"
                  src="https://picsum.photos/seed/current/100/100"
                  className="w-11 h-11 rounded-full border-4 border-white shadow-diffusion"
                />
                <div className="w-11 h-11 rounded-full border-4 border-white shadow-diffusion bg-secondary text-white flex items-center justify-center text-[11px] font-black">
                  +10
                </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default TutorPreview;
