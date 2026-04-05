import React from "react";
import { motion } from "framer-motion";
import { Sparkle, TrendUp, TreeStructure, CheckCircle, Circle } from "@phosphor-icons/react";

const LevelStep = ({ formData, updateData }) => {
  const selectedLevel = formData.level;

  const cardVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 30 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  const setLevel = (level) => {
    updateData("level", level);
  };

  return (
    <motion.section 
      initial="hidden"
      animate="visible"
      exit="hidden"
      variants={{
        visible: { transition: { staggerChildren: 0.1 } }
      }}
      className="max-w-5xl mx-auto w-full px-6 pt-12 pb-32 flex flex-col items-center"
    >
      <motion.div variants={cardVariants} className="w-full mt-12 mb-20">
        <div className="mb-4 inline-flex items-center px-3 py-1 bg-surface-variant rounded-sm">
          <span className="text-[0.625rem] font-bold tracking-widest uppercase text-on-surface-variant font-label">Step 02 / 04</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-display font-extrabold tracking-tight text-on-surface max-w-2xl leading-[1.1]">
          What is your current level?
        </h1>
      </motion.div>

      <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
        {/* Beginner Card */}
        <motion.div 
          variants={cardVariants}
          onClick={() => setLevel("beginner")}
          className={`group relative rounded-xl p-8 flex flex-col h-full border transition-all duration-300 cursor-pointer shadow-diffusion ${selectedLevel === 'beginner' ? 'bg-[#f0f7ff] border-primary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="mb-8 w-14 h-14 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
            <Sparkle weight="fill" className="text-3xl" />
          </div>
          <div className="flex-grow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold font-sans text-secondary uppercase tracking-widest">A1 - A2</span>
            </div>
            <h3 className="text-2xl font-display font-bold text-on-surface mb-3">Beginner</h3>
            <p className="text-on-surface-variant leading-relaxed text-sm font-medium">
              You are starting from scratch or know a few phrases. We'll build your foundation with core vocabulary and basic structures.
            </p>
          </div>
          <div className="mt-8 flex justify-end">
            {selectedLevel === 'beginner' ? (
              <CheckCircle weight="fill" className="text-primary text-2xl" />
            ) : (
              <Circle className="text-outline group-hover:text-primary transition-colors text-2xl" />
            )}
          </div>
        </motion.div>

        {/* Intermediate Card */}
        <motion.div 
          variants={cardVariants}
          onClick={() => setLevel("intermediate")}
          className={`group relative rounded-xl p-8 flex flex-col h-full border transition-all duration-300 cursor-pointer shadow-diffusion md:-translate-y-4 ${selectedLevel === 'intermediate' ? 'bg-[#f0f7ff] border-[#2F80ED] border-[2px] shadow-[0_0_20px_rgba(47,128,237,0.15)]' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          {selectedLevel !== 'intermediate' && (
            <div className="absolute -top-3 left-8 px-4 py-1 bg-[#2F80ED] text-white text-[10px] font-bold uppercase tracking-[0.2em] rounded-full">
              Recommended
            </div>
          )}
          
          <div className="mb-8 w-14 h-14 rounded-full bg-primary-fixed flex items-center justify-center text-on-primary-fixed">
            <TrendUp weight="fill" className="text-3xl" />
          </div>
          <div className="flex-grow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold font-sans text-[#2F80ED] uppercase tracking-widest">B1 - B2</span>
            </div>
            <h3 className="text-2xl font-display font-bold text-on-surface mb-3">Intermediate</h3>
            <p className="text-on-surface-variant leading-relaxed text-sm font-medium">
              You can hold basic conversations. We'll focus on fluid transitions, complex tenses, and natural idiomatic expressions.
            </p>
          </div>
          <div className="mt-8 flex justify-end">
            {selectedLevel === 'intermediate' ? (
              <CheckCircle weight="fill" className="text-[#2F80ED] text-2xl" />
            ) : (
              <Circle className="text-outline group-hover:text-[#2F80ED] transition-colors text-2xl" />
            )}
          </div>
        </motion.div>

        {/* Advanced Card */}
        <motion.div 
          variants={cardVariants}
          onClick={() => setLevel("advanced")}
          className={`group relative rounded-xl p-8 flex flex-col h-full border transition-all duration-300 cursor-pointer shadow-diffusion ${selectedLevel === 'advanced' ? 'bg-[#f0f7ff] border-tertiary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="mb-8 w-14 h-14 rounded-full bg-tertiary-fixed flex items-center justify-center text-on-tertiary-fixed">
            <TreeStructure weight="fill" className="text-3xl" />
          </div>
          <div className="flex-grow">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold font-sans text-tertiary uppercase tracking-widest">C1 - C2</span>
            </div>
            <h3 className="text-2xl font-display font-bold text-on-surface mb-3">Advanced</h3>
            <p className="text-on-surface-variant leading-relaxed text-sm font-medium">
              You speak fluently but seek nuance. We'll refine your professional vocabulary and master native-level rhetoric.
            </p>
          </div>
          <div className="mt-8 flex justify-end">
            {selectedLevel === 'advanced' ? (
              <CheckCircle weight="fill" className="text-tertiary text-2xl" />
            ) : (
              <Circle className="text-outline group-hover:text-tertiary transition-colors text-2xl" />
            )}
          </div>
        </motion.div>
      </div>
      
      <div className="fixed top-1/2 -right-24 -z-10 w-96 h-96 bg-primary-container/5 rounded-full blur-[100px]"></div>
      <div className="fixed bottom-0 -left-24 -z-10 w-64 h-64 bg-secondary-container/5 rounded-full blur-[80px]"></div>
    </motion.section>
  );
};

export default LevelStep;
