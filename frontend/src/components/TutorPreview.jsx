import { motion } from "framer-motion";
import { Gear, Microphone, CheckCircle } from "@phosphor-icons/react";

const TutorPreview = () => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ delay: 0.4, type: "spring", stiffness: 100, damping: 20 }}
      className="relative"
    >
      {/* Background decorative element */}
      <div className="absolute -top-20 -right-20 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      
      <div className="relative animate-float">
        {/* Liquid Glass Interface Preview */}
        <div className="liquid-glass p-8 rounded-4xl border border-white/40 shadow-2xl relative z-20 overflow-hidden">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-zinc-100 rounded-full overflow-hidden border border-zinc-200">
                <img
                  alt="Isabella - AI Tutor"
                  src="https://picsum.photos/seed/isabella/100/100"
                  className="w-full h-full object-cover"
                />
              </div>
              <div>
                <h4 className="font-bold text-zinc-900">Isabella</h4>
                <div className="text-[10px] text-green-500 font-bold uppercase tracking-wider flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                  AI Tutor Online
                </div>
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-zinc-100/50 flex items-center justify-center backdrop-blur-sm cursor-pointer hover:bg-zinc-200 transition-colors">
              <Gear size={18} className="text-zinc-500" />
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="bg-zinc-100/80 p-4 rounded-2xl rounded-tl-none max-w-[85%] shadow-sm"
            >
              <p className="text-sm text-zinc-800 leading-relaxed font-medium">
                ¡Hola! ¿Cómo estuvo tu día hoy? Me gustaría saber qué hiciste de especial.
              </p>
            </motion.div>

            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 1.2 }}
              className="bg-primary p-4 rounded-2xl rounded-tr-none max-w-[85%] ml-auto text-white shadow-lg shadow-primary/20"
            >
              <p className="text-sm leading-relaxed font-medium">
                Hoy fui al mercado central y compré muchas frutas frescas.
              </p>
            </motion.div>

            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.6 }}
              className="bg-white/50 border border-white/60 p-4 rounded-2xl backdrop-blur-md shadow-sm"
            >
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle weight="fill" className="text-primary" size={16} />
                <p className="text-[10px] font-bold text-primary uppercase tracking-widest">Live Feedback</p>
              </div>
              <p className="text-xs text-zinc-600 leading-relaxed italic">
                Great job! <span className="text-zinc-900 font-bold text-mono">"Frutas"</span> is plural, and you used the correct conjugation for <span className="text-zinc-900 font-bold text-mono">"compré"</span>.
              </p>
            </motion.div>
          </div>

          <div className="flex justify-center">
            <motion.div
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-white shadow-xl shadow-primary/40 cursor-pointer relative group"
            >
              <div className="absolute inset-x-0 inset-y-0 bg-primary rounded-full animate-ping opacity-25 group-hover:opacity-40" />
              <Microphone weight="fill" size={32} className="relative z-10" />
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default TutorPreview;
