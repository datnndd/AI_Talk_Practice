import { motion } from "framer-motion";
import { PlayCircle, ArrowRight } from "@phosphor-icons/react";
import { Link } from "react-router-dom";
import TutorPreview from "@/features/practice/components/TutorPreview";

const Hero = () => {
  return (
    <section className="min-h-[100dvh] pt-32 pb-20 overflow-hidden flex items-center relative bg-[#f9fafb]">
      {/* Background Decorative Blobs */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-secondary/5 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2" />

      <div className="max-w-7xl mx-auto px-6 w-full relative z-10">
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          {/* Text Content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-secondary-container/30 text-secondary text-[11px] font-bold uppercase tracking-[0.2em] mb-8 border border-secondary-container/50"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
              </span>
              Next-Gen Learning
            </motion.div>

            <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8 text-zinc-900 font-display">
              Speak Fluently <br />
              <span className="text-primary">with AI.</span>
            </h1>

            <p className="text-xl text-zinc-500 mb-12 max-w-lg leading-relaxed font-medium">
              Real-time speaking practice and personalized learning paths designed for your unique professional and personal goals.
            </p>

            <div className="flex flex-col sm:row gap-5">
              <Link to="/topics">
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="bg-tertiary-fixed text-tertiary text-lg font-bold px-10 py-5 rounded-2xl shadow-xl shadow-tertiary/10 flex items-center justify-center gap-3 group transition-all"
                >
                  Start Free Trial
                  <ArrowRight weight="bold" className="transition-transform group-hover:translate-x-1" />
                </motion.button>
              </Link>
              <button className="px-10 py-5 rounded-2xl text-lg font-bold bg-white text-zinc-700 border border-zinc-200 hover:bg-zinc-50 transition-all flex items-center justify-center gap-3 group">
                <PlayCircle weight="fill" size={24} className="text-zinc-400 transition-colors group-hover:text-primary" />
                Watch Demo
              </button>
            </div>

            <div className="mt-16 flex items-center gap-6">
              <div className="flex -space-x-3">
                {[1, 2, 3, 4].map((i) => (
                  <img
                    key={i}
                    alt={`User ${i}`}
                    className="w-12 h-12 rounded-full border-4 border-white shadow-diffusion object-cover"
                    src={`https://picsum.photos/seed/face${i}/100/100`}
                  />
                ))}
                <div className="w-12 h-12 rounded-full border-4 border-white shadow-diffusion bg-zinc-100 flex items-center justify-center text-[11px] font-black text-zinc-400">
                  +30
                </div>
              </div>
              <p className="text-sm text-zinc-500 font-bold">
                Join <span className="text-zinc-900">500,000+</span> language learners
              </p>
            </div>
          </motion.div>

          {/* AI Interface Preview */}
          <div className="relative">
            <TutorPreview />
            {/* Contextual Badges */}
            <motion.div 
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -top-10 -left-10 liquid-glass px-4 py-2 rounded-xl shadow-diffusion hidden lg:block"
            >
              <p className="text-[10px] font-black uppercase tracking-widest text-primary flex items-center gap-2">
                <span className="w-2 h-2 bg-primary rounded-full" />
                Live Feedback
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
