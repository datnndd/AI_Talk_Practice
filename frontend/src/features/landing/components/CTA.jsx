import { motion } from "framer-motion";
import { CheckCircle } from "@phosphor-icons/react";

const CTA = () => {
  return (
    <section className="py-32" id="cta">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
           initial={{ opacity: 0, y: 40 }}
           whileInView={{ opacity: 1, y: 0 }}
           viewport={{ once: true }}
           transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
           className="bg-primary rounded-[3rem] p-12 md:p-24 text-center relative overflow-hidden shadow-2xl shadow-primary/30"
        >
          {/* Animated Background Blobs */}
          <motion.div 
            animate={{ 
              scale: [1, 1.2, 1],
              x: [0, 50, 0],
              y: [0, -30, 0]
            }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-0 right-0 w-[500px] h-[500px] bg-white/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2" 
          />
          <motion.div 
            animate={{ 
              scale: [1, 1.3, 1],
              x: [0, -40, 0],
              y: [0, 50, 0]
            }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-secondary/20 blur-[100px] rounded-full translate-y-1/2 -translate-x-1/2" 
          />

          <div className="relative z-10 max-w-3xl mx-auto space-y-10">
            <h2 className="text-4xl md:text-7xl font-black text-white tracking-tighter font-display leading-[0.9]">
              Begin Your 14-Day <br />Journey Today.
            </h2>
            <p className="text-white/80 text-xl md:text-2xl font-medium max-w-2xl mx-auto leading-relaxed">
              Join 500,000+ learners who are breaking language barriers every single day. No credit card required.
            </p>
            
            <div className="flex flex-col sm:row items-center justify-center gap-8 pt-4">
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className="bg-tertiary-fixed text-tertiary md:text-2xl font-black px-12 py-6 rounded-2xl shadow-2xl shadow-black/20 relative group overflow-hidden"
              >
                <span className="relative z-10">Start Free Trial</span>
                <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover:animate-shimmer" />
              </motion.button>
              
              <div className="flex items-center gap-2 text-white/70 font-bold tracking-tight">
                <CheckCircle weight="fill" size={24} className="text-secondary-container" />
                Cancel anytime
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CTA;
