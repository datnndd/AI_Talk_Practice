import React from "react";
import { motion } from "framer-motion";
import { User, Globe, CalendarBlank, Target, Warning, Lightning } from "@phosphor-icons/react";

const FinalStep = ({ formData, updateData }) => {
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    updateData(name, name === "age" || name === "daily_goal" ? parseInt(value) || "" : value);
  };

  return (
    <motion.section 
      initial="hidden"
      animate="visible"
      exit="hidden"
      variants={{
        visible: { transition: { staggerChildren: 0.1 } }
      }}
      className="max-w-3xl mx-auto w-full px-6 pt-12 pb-32 flex flex-col"
    >
      <motion.div variants={itemVariants} className="mb-12">
        <div className="mb-4 inline-flex items-center px-3 py-1 bg-surface-variant rounded-sm">
          <span className="text-[0.625rem] font-bold tracking-widest uppercase text-on-surface-variant font-label">Step 04 / 04</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-display font-extrabold tracking-tight text-on-surface leading-[1.1] mb-4">
          Almost there!
        </h1>
        <p className="font-body text-lg text-on-surface-variant leading-relaxed">
          Let's finalize your profile so we can get started.
        </p>
      </motion.div>

      <div className="space-y-6">
        {/* Name */}
        <motion.div variants={itemVariants} className="flex flex-col gap-2">
          <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
            <User size={18} /> Display Name
          </label>
          <input 
            type="text" 
            name="display_name"
            value={formData.display_name}
            onChange={handleInputChange}
            placeholder="E.g. Alex"
            className="w-full bg-surface-container-lowest border-2 border-outline-variant/30 focus:border-primary/50 rounded-xl px-4 py-3 outline-none transition-all font-medium text-zinc-900"
          />
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Age */}
          <motion.div variants={itemVariants} className="flex flex-col gap-2">
            <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
              <CalendarBlank size={18} /> Age
            </label>
            <input 
              type="number" 
              name="age"
              value={formData.age}
              onChange={handleInputChange}
              placeholder="Your age"
              min="5" max="100"
              className="w-full bg-surface-container-lowest border-2 border-outline-variant/30 focus:border-primary/50 rounded-xl px-4 py-3 outline-none transition-all font-medium text-zinc-900"
            />
          </motion.div>

          {/* Native Language */}
          <motion.div variants={itemVariants} className="flex flex-col gap-2">
            <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
              <Globe size={18} /> Native Language
            </label>
            <select 
              name="native_language"
              value={formData.native_language}
              onChange={handleInputChange}
              className="w-full bg-surface-container-lowest border-2 border-outline-variant/30 focus:border-primary/50 rounded-xl px-4 py-3 outline-none transition-all font-medium text-zinc-900"
            >
              <option value="vi">Vietnamese</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="zh">Chinese</option>
              <option value="fr">French</option>
            </select>
          </motion.div>
        </div>

        {/* Daily Goal */}
        <motion.div variants={itemVariants} className="flex flex-col gap-2">
          <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
            <Target size={18} /> Daily Goal (Minutes)
          </label>
          <div className="flex gap-3">
            {[5, 15, 30, 60].map(mins => (
              <button
                key={mins}
                type="button"
                onClick={() => updateData("daily_goal", mins)}
                className={`flex-1 py-3 rounded-xl border-2 font-bold transition-all ${formData.daily_goal === mins ? 'bg-primary/10 border-primary text-primary' : 'bg-surface-container-lowest border-outline-variant/30 text-zinc-500 hover:border-primary/30'}`}
              >
                {mins} m
              </button>
            ))}
          </div>
        </motion.div>
        
        {/* Main Challenge */}
        <motion.div variants={itemVariants} className="flex flex-col gap-2">
          <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
            <Lightning size={18} /> Your Main Challenge
          </label>
          <input 
            type="text" 
            name="main_challenge"
            value={formData.main_challenge}
            onChange={handleInputChange}
            placeholder="E.g. Speaking fluently, vocabulary..."
            className="w-full bg-surface-container-lowest border-2 border-outline-variant/30 focus:border-primary/50 rounded-xl px-4 py-3 outline-none transition-all font-medium text-zinc-900"
          />
        </motion.div>

      </div>
    </motion.section>
  );
};

export default FinalStep;
