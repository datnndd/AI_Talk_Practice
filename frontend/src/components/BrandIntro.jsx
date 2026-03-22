import { motion } from "framer-motion";

const BrandIntro = () => {
  return (
    <section className="hidden lg:flex lg:w-3/5 relative bg-zinc-950 items-center justify-center overflow-hidden">
      {/* Background Visual */}
      <div className="absolute inset-0 z-0">
        <img 
          src="https://picsum.photos/seed/lingoflow_login/1600/1200" 
          alt="Immersive Brand Visual" 
          className="w-full h-full object-cover opacity-40 grayscale"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-zinc-950 via-zinc-950/80 to-transparent"></div>
      </div>

      {/* Liquid Glass Content Overlay */}
      <div className="relative z-10 w-full max-w-xl px-12">
        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="liquid-glass p-12 rounded-[2.5rem] space-y-8 backdrop-blur-3xl border border-white/10 shadow-2xl"
        >
          <div className="inline-flex items-center space-x-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-white text-[10px] font-black tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span>Global Communication</span>
          </div>
          
          <h1 className="text-5xl font-black text-white leading-[1.1] tracking-tighter font-display">
            Master any language <br/>
            <span className="text-zinc-500">with precision.</span>
          </h1>
          
          <p className="text-base text-zinc-400 font-medium leading-relaxed max-w-md">
            Experience the next generation of linguistic fluency. LingoFlow combines cognitive science with adaptive flow to make you conversational in weeks, not years.
          </p>
          
          <div className="grid grid-cols-2 gap-8 pt-6">
            <div className="space-y-1">
              <span className="text-primary text-3xl font-black font-mono tracking-tighter">50+</span>
              <p className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">Supported Languages</p>
            </div>
            <div className="space-y-1">
              <span className="text-primary text-3xl font-black font-mono tracking-tighter">1.2M</span>
              <p className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest">Active Learners</p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="absolute bottom-12 left-12 z-10">
        <span className="text-white font-black tracking-tighter text-2xl font-display">LingoFlow</span>
      </div>
    </section>
  );
};

export default BrandIntro;
