import { motion } from "framer-motion";
import { Sparkle, ShieldCheck, Users, Robot } from "@phosphor-icons/react";

const BrandIntro = () => {
  return (
    <section className="hidden lg:flex lg:w-7/12 relative bg-zinc-950 items-center justify-center overflow-hidden p-16">
      {/* Asymmetric Background Elements */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[80%] h-[120%] bg-indigo-500/10 [clip-path:polygon(0_0,100%_0,85%_100%,0%_100%)] opacity-50"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[60%] h-[80%] bg-zinc-900/50 rotate-12"></div>
      </div>

      <div className="relative z-10 w-full max-w-2xl">
        {/* Brand Anchor */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          className="mb-12"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Robot weight="fill" size={24} />
            </div>
            <span className="text-3xl font-black tracking-tighter text-white font-display uppercase italic">LingoFlow</span>
          </div>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: "spring", stiffness: 80, damping: 15, delay: 0.1 }}
          className="text-6xl md:text-7xl font-black text-white leading-tight tracking-tighter mb-10"
        >
          Master any <br/>
          <span className="text-indigo-500">language.</span>
        </motion.h1>

        {/* Feature Summary Bento-style */}
        <div className="grid grid-cols-2 gap-4 mb-12">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.2 }}
            className="bg-white/5 backdrop-blur-xl p-8 rounded-[2rem] border border-white/10 shadow-2xl group hover:bg-white/[0.08] transition-colors"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400 group-hover:scale-110 transition-transform">
                <Sparkle weight="fill" size={18} />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-indigo-300">AI Powered</span>
            </div>
            <p className="text-zinc-400 text-sm leading-relaxed font-medium">
              Dynamic conversation engines that adapt to your unique learning pace and vocabulary gaps.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.3 }}
            className="bg-white/5 backdrop-blur-xl p-8 rounded-[2rem] border border-white/10 shadow-2xl group hover:bg-white/[0.08] transition-colors"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400 group-hover:scale-110 transition-transform">
                <ShieldCheck weight="fill" size={18} />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-emerald-300">Accredited</span>
            </div>
            <p className="text-zinc-400 text-sm leading-relaxed font-medium">
              Curriculum designed by world-class linguists and polyglots for maximum retention.
            </p>
          </motion.div>
        </div>

        {/* Premium Graphic Element */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 50, damping: 20, delay: 0.4 }}
          className="relative group cursor-pointer"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-indigo-700 rounded-[2.5rem] blur opacity-10 group-hover:opacity-25 transition duration-1000"></div>
          <div className="relative bg-zinc-900 rounded-[2.5rem] overflow-hidden aspect-video border border-white/10 shadow-2xl">
            <img 
              className="w-full h-full object-cover opacity-60 grayscale group-hover:grayscale-0 group-hover:opacity-80 transition-all duration-700" 
              src="https://picsum.photos/seed/lingoflow_premium/1200/800" 
              alt="Premium Language Learning"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/90 to-transparent"></div>
            
            <div className="absolute bottom-8 left-8 flex items-center gap-6">
              <div className="flex -space-x-3">
                {[1, 2, 3].map((i) => (
                  <img 
                    key={i}
                    className="h-10 w-10 rounded-full border-2 border-zinc-900 shadow-xl" 
                    src={`https://i.pravatar.cc/100?u=${i}`} 
                    alt="User"
                  />
                ))}
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Join the flow</p>
                <p className="text-sm text-zinc-100 font-bold">12k+ active learners today</p>
              </div>
            </div>
            
            <div className="absolute top-6 right-6">
              <div className="bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-[9px] font-black uppercase tracking-widest text-white">Live Engine</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default BrandIntro;
