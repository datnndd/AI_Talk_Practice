import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { Sparkle, Microphone, PaperPlaneRight } from "@phosphor-icons/react";

const TypewriterInput = () => {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const phrases = [
    "Ask me about French cuisine...",
    "How do I say 'delicious' in French?",
    "Tell me a joke in French...",
    "Translate 'I want to travel'..."
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setPhraseIndex((prev) => (prev + 1) % phrases.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <footer className="p-8 pt-2">
      <div className="flex flex-col gap-4">
        <div className="liquid-glass rounded-full flex items-center px-6 py-3 border border-white/40 shadow-xl focus-within:shadow-primary/10 transition-all refraction">
          <div className="flex items-center gap-2 pr-4 border-r border-zinc-200/50 mr-4">
            <button className="p-2 text-primary hover:bg-primary/5 rounded-full transition-colors">
              <Sparkle weight="fill" size={20} />
            </button>
          </div>
          
          <div className="flex-1 relative h-6 overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.span
                key={phraseIndex}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.5, ease: "anticipate" }}
                className="absolute inset-0 text-sm font-medium text-zinc-400 font-sans"
              >
                {phrases[phraseIndex]}
              </motion.span>
            </AnimatePresence>
            <input 
              type="text" 
              className="absolute inset-0 bg-transparent border-none focus:ring-0 text-sm font-semibold text-zinc-950 opacity-0 focus:opacity-100 transition-opacity w-full"
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center shadow-lg shadow-primary/30 ml-4 btn-spring"
          >
            <Microphone weight="fill" size={20} />
          </motion.button>
        </div>

        <div className="px-8 flex items-center gap-3">
          <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
            <Sparkle weight="fill" className="text-primary/60" size={12} />
            Suggested
          </div>
          <motion.div
            whileHover={{ x: 4 }}
            className="liquid-glass rounded-xl px-4 py-2 border border-white/30 cursor-pointer hover:bg-white/50 transition-colors shadow-sm refraction"
          >
            <p className="text-[11px] italic text-zinc-400 font-medium">
              "Je voudrais en savoir plus sur les vins de Bordeaux..."
            </p>
          </motion.div>
        </div>
      </div>
    </footer>
  );
};

export default TypewriterInput;
