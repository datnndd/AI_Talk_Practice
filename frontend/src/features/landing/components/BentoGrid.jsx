import { motion } from "framer-motion";
import { ChatCircleDots, Sparkle, ChartBar, Globe } from "@phosphor-icons/react";

const BentoGrid = () => {
  return (
    <section className="py-32 bg-[#f9fafb] scroll-mt-32" id="features">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-20 space-y-4">
          <span className="font-sans font-black text-primary uppercase tracking-[0.3em] text-[10px]">Capabilities</span>
          <h2 className="text-4xl md:text-5xl font-black tracking-tighter text-zinc-900 max-w-2xl">
            Designed for Depth, <br />Built for Speed.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
          {/* Card 1: Real-time Conversations */}
          <div className="md:col-span-7 space-y-6 group">
            <div className="relative h-[320px] bg-white rounded-[2.5rem] border border-slate-200/50 shadow-diffusion overflow-hidden flex items-center justify-center p-12 transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-primary/5 group-hover:-translate-y-1">
              <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,theme(colors.primary),transparent)] blur-3xl" />
              </div>
              <div className="relative z-10 space-y-8 w-full">
                 <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary shadow-inner transition-transform duration-500 group-hover:scale-110 group-hover:rotate-3">
                    <ChatCircleDots weight="fill" size={32} />
                 </div>
                 {/* Perpetual Motion: Active Waveform */}
                 <div className="flex items-end gap-1 h-12">
                    {[0.4, 0.7, 1, 0.6, 0.8, 0.5, 0.9, 0.7, 1, 0.8].map((h, i) => (
                        <motion.div
                            key={i}
                            animate={{ height: [`${h * 40}px`, `${h * 100}px`, `${h * 40}px`] }}
                            transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                            className="flex-1 bg-primary/20 rounded-full"
                        />
                    ))}
                 </div>
              </div>
            </div>
            <div className="px-4">
               <h3 className="text-xl font-black font-display mb-2 text-zinc-900">Real-time conversations</h3>
               <p className="text-zinc-500 font-medium leading-relaxed max-w-sm">Engage in natural, unscripted dialogues with an AI that adapts to your pace instantly.</p>
            </div>
          </div>

          {/* Card 2: Personalized Curriculum */}
          <div className="md:col-span-5 space-y-6 group">
            <div className="relative h-[320px] bg-primary rounded-[2.5rem] shadow-diffusion overflow-hidden p-12 flex flex-col justify-between transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-primary/30 group-hover:-translate-y-1">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:scale-110 transition-transform duration-700" />
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white border border-white/20 shadow-lg group-hover:rotate-6 transition-transform">
                   <Sparkle weight="bold" size={32} />
                </div>
                {/* Perpetual Motion: Floating Sparkles */}
                <div className="flex flex-col gap-2">
                   <div className="flex items-center gap-3">
                        <div className="px-4 py-2 bg-white/10 backdrop-blur text-white/90 text-[11px] font-black rounded-full border border-white/10">Dynamic Parsing</div>
                        <div className="px-4 py-2 bg-white/10 backdrop-blur text-white/90 text-[11px] font-black rounded-full border border-white/10 animate-pulse">Live Analysis</div>
                   </div>
                   <div className="px-4 py-2 bg-white/20 backdrop-blur text-white text-[11px] font-black rounded-full border border-white/20 w-fit">Context-Aware AI</div>
                </div>
            </div>
            <div className="px-4">
               <h3 className="text-xl font-black font-display mb-2 text-zinc-900">Personalized curriculum</h3>
               <p className="text-zinc-500 font-medium leading-relaxed">No generic lessons. Our AI crafts paths based on your industry and hobbies.</p>
            </div>
          </div>

          {/* Card 3: Gamified Progress */}
          <div className="md:col-span-5 space-y-6 group">
             <div className="relative h-[320px] bg-white rounded-[2.5rem] border border-slate-200/50 shadow-diffusion overflow-hidden p-12 flex flex-col justify-between transition-all duration-500 group-hover:shadow-2xl group-hover:shadow-secondary/5 group-hover:-translate-y-1">
                <div className="w-16 h-16 rounded-2xl bg-secondary/10 flex items-center justify-center text-secondary shadow-inner group-hover:-rotate-6 transition-transform">
                   <ChartBar weight="fill" size={32} />
                </div>
                {/* Perpetual Motion: Animated Progress Bars */}
                <div className="flex items-end gap-2 h-20">
                    {[30, 50, 40, 70, 100].map((h, i) => (
                        <div key={i} className="flex-1 bg-zinc-50 rounded-lg relative overflow-hidden h-full">
                            <motion.div
                                initial={{ height: 0 }}
                                whileInView={{ height: `${h}%` }}
                                transition={{ delay: 0.5 + (i * 0.1), duration: 1 }}
                                className="absolute bottom-0 left-0 w-full bg-secondary rounded-lg"
                            />
                        </div>
                    ))}
                </div>
             </div>
             <div className="px-4">
               <h3 className="text-xl font-black font-display mb-2 text-zinc-900">Gamified progress</h3>
               <p className="text-zinc-500 font-medium leading-relaxed">Earn streaks, unlock achievements, and visualize your fluency growth with data.</p>
            </div>
          </div>

          {/* Card 4: 30+ Languages */}
          <div className="md:col-span-7 space-y-6 group">
            <div className="relative h-[320px] bg-zinc-100 rounded-[2.5rem] shadow-diffusion overflow-hidden p-12 flex flex-col md:flex-row items-center gap-10 transition-all duration-500 group-hover:shadow-2xl group-hover:-translate-y-1">
                <div className="flex-1 space-y-6">
                    <div className="w-16 h-16 rounded-2xl bg-white shadow-sm flex items-center justify-center text-zinc-900 transition-transform group-hover:scale-110">
                       <Globe weight="bold" size={32} />
                    </div>
                </div>
                {/* Perpetual Motion: Horizontal Carousel of Languages */}
                <div className="flex-1 grid grid-cols-3 gap-3 w-full">
                    {["FR", "DE", "JP", "ES", "CN", "IT"].map((lang) => (
                        <motion.div
                            key={lang}
                            whileHover={{ scale: 1.05, rotate: 2 }}
                            className="aspect-square bg-white rounded-2xl flex items-center justify-center font-black text-xs shadow-sm border border-zinc-200/50 text-zinc-400 group-hover:text-primary transition-colors"
                        >
                            {lang}
                        </motion.div>
                    ))}
                </div>
            </div>
            <div className="px-4">
               <h3 className="text-xl font-black font-display mb-2 text-zinc-900">30+ languages</h3>
               <p className="text-zinc-500 font-medium leading-relaxed">From Spanish to specialized Mandarin, master the world's most spoken tongues.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BentoGrid;
