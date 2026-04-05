import React from "react";
import { motion } from "framer-motion";
import { Briefcase, GraduationCap, GlobeHemisphereWest, UsersThree, Check } from "@phosphor-icons/react";

const GoalStep = ({ formData, updateData }) => {
  const selectedGoal = formData.learning_purpose;

  const cardVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  const setGoal = (goal) => {
    updateData("learning_purpose", goal);
  };

  return (
    <motion.section 
      initial="hidden"
      animate="visible"
      exit="hidden"
      variants={{
        visible: { transition: { staggerChildren: 0.1 } }
      }}
      className="max-w-6xl mx-auto w-full px-6 md:px-12 pt-8 pb-32"
    >
      <div className="absolute -top-16 -right-16 md:right-12 w-64 h-64 rounded-full liquid-glass flex items-center justify-center -z-10">
        <div className="w-32 h-32 rounded-full bg-primary/10 blur-3xl"></div>
      </div>

      <motion.div variants={cardVariants} className="mb-16 md:mb-24 mt-8">
        <span className="inline-block px-3 py-1 bg-surface-variant text-on-surface-variant text-[10px] font-bold tracking-widest uppercase rounded-sm mb-6">
          Step 01 / 04
        </span>
        <h1 className="font-display text-5xl md:text-7xl font-extrabold tracking-tight text-on-surface leading-[1.1] mb-8 max-w-3xl">
          What is your <br/><span className="text-primary italic">primary</span> goal?
        </h1>
        <p className="font-body text-lg md:text-xl text-on-surface-variant max-w-xl leading-relaxed">
          We'll personalize your learning path based on your objectives to ensure every minute spent brings you closer to mastery.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Card 1: Boost my career */}
        <motion.button 
          variants={cardVariants}
          onClick={() => setGoal("career")}
          className={`md:col-span-7 group relative flex flex-col items-start p-8 rounded-xl shadow-diffusion transition-all duration-300 hover:shadow-xl text-left border ${selectedGoal === 'career' ? 'bg-[#f0f7ff] border-primary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-12 transition-transform group-hover:scale-110">
            <Briefcase weight="fill" className="text-primary text-3xl" />
          </div>
          <div className="mt-auto">
            <h3 className="font-display text-2xl font-bold mb-3">Boost my career</h3>
            <p className="text-on-surface-variant font-medium">Professional growth, interview prep, and business networking.</p>
          </div>
          {selectedGoal === 'career' && (
            <div className="absolute top-6 right-6">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                <Check weight="bold" className="text-white text-sm" />
              </div>
            </div>
          )}
        </motion.button>

        {/* Card 2: Support my education */}
        <motion.button 
          variants={cardVariants}
          onClick={() => setGoal("education")}
          className={`md:col-span-5 group relative flex flex-col items-start p-8 rounded-xl shadow-diffusion transition-all duration-300 hover:shadow-lg text-left border ${selectedGoal === 'education' ? 'bg-[#f0f7ff] border-primary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="w-14 h-14 rounded-full bg-secondary-container/30 flex items-center justify-center mb-12 transition-transform group-hover:scale-110">
            <GraduationCap weight="fill" className="text-secondary text-3xl" />
          </div>
          <div className="mt-auto">
            <h3 className="font-display text-2xl font-bold mb-3">Support my education</h3>
            <p className="text-on-surface-variant font-medium">Ace exams, study abroad, and master academic literature.</p>
          </div>
          {selectedGoal === 'education' && (
            <div className="absolute top-6 right-6 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
              <Check weight="bold" className="text-white text-sm" />
            </div>
          )}
        </motion.button>

        {/* Card 3: Travel the world */}
        <motion.button 
          variants={cardVariants}
          onClick={() => setGoal("travel")}
          className={`md:col-span-5 group relative flex flex-col items-start p-8 rounded-xl shadow-diffusion transition-all duration-300 hover:shadow-lg text-left border ${selectedGoal === 'travel' ? 'bg-[#f0f7ff] border-primary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="w-14 h-14 rounded-full bg-tertiary-fixed-dim/30 flex items-center justify-center mb-12 transition-transform group-hover:scale-110">
            <GlobeHemisphereWest weight="fill" className="text-tertiary text-3xl" />
          </div>
          <div className="mt-auto">
            <h3 className="font-display text-2xl font-bold mb-3">Travel the world</h3>
            <p className="text-on-surface-variant font-medium">Navigate new cities, order food, and meet people globally.</p>
          </div>
          {selectedGoal === 'travel' && (
            <div className="absolute top-6 right-6 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
              <Check weight="bold" className="text-white text-sm" />
            </div>
          )}
        </motion.button>

        {/* Card 4: Socialize with locals */}
        <motion.button 
          variants={cardVariants}
          onClick={() => setGoal("socialize")}
          className={`md:col-span-7 group relative flex flex-col items-start p-8 rounded-xl shadow-diffusion overflow-hidden transition-all duration-300 hover:shadow-lg text-left border ${selectedGoal === 'socialize' ? 'bg-[#f0f7ff] border-primary' : 'bg-surface-container-lowest border-transparent hover:bg-surface-container-low'}`}
        >
          <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
          <div className="w-14 h-14 rounded-full bg-primary-fixed-dim/30 flex items-center justify-center mb-12 transition-transform group-hover:scale-110 relative z-10">
            <UsersThree weight="fill" className="text-on-primary-fixed-variant text-3xl" />
          </div>
          <div className="mt-auto relative z-10">
            <h3 className="font-display text-2xl font-bold mb-3">Socialize with locals</h3>
            <p className="text-on-surface-variant font-medium">Build friendships, understand culture, and speak naturally.</p>
          </div>
          {selectedGoal === 'socialize' && (
            <div className="absolute top-6 right-6 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
              <Check weight="bold" className="text-white text-sm" />
            </div>
          )}
        </motion.button>
      </div>
    </motion.section>
  );
};

export default GoalStep;
