import { motion } from "framer-motion";
import { PlayCircle } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import TutorPreview from "./TutorPreview";

const Hero = () => {
  return (
    <main className="min-h-[100dvh] pt-32 pb-20 overflow-hidden flex items-center">
      <div className="max-w-7xl mx-auto px-6 w-full">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Text Content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10"
          >
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-primary text-[10px] font-bold uppercase tracking-widest mb-6 border border-blue-100"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              Next-Gen Language Learning
            </motion.div>

            <h1 className="text-6xl lg:text-7xl font-bold tracking-tighter leading-[1.05] mb-8 text-zinc-950 font-display text-balance">
              Master any language with <span className="text-primary italic">real‑time</span> AI conversations
            </h1>

            <p className="text-xl text-zinc-500 mb-10 max-w-lg leading-relaxed font-medium">
              Forget repetitive flashcards. Practice speaking naturally with an AI tutor that adapts to your level and interests in real-time.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/topics">
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="bg-primary text-white px-8 py-4 rounded-custom text-lg font-bold shadow-2xl shadow-primary/20 transition-all hover:shadow-primary/30"
                >
                  Start Learning for Free
                </motion.button>
              </Link>
              <button className="px-8 py-4 rounded-custom text-lg font-bold border border-zinc-200 hover:bg-zinc-50 transition-all inline-flex items-center gap-2 group">
                <PlayCircle size={28} className="text-primary transition-transform group-hover:scale-110" />
                Watch Demo
              </button>
            </div>

            <div className="mt-12 flex items-center gap-6">
              <div className="flex -space-x-3">
                {[1, 2, 3].map((i) => (
                  <img
                    key={i}
                    alt={`User ${i}`}
                    className="w-10 h-10 rounded-full border-2 border-white shadow-sm ring-1 ring-zinc-100"
                    src={`https://picsum.photos/seed/user${i}/100/100`}
                  />
                ))}
              </div>
              <p className="text-sm text-zinc-500 font-medium">
                Joined by <span className="text-zinc-900 font-bold">12,000+</span> language learners
              </p>
            </div>
          </motion.div>

          {/* Graphic/Interface */}
          <TutorPreview />
        </div>
      </div>
    </main>
  );
};

export default Hero;
