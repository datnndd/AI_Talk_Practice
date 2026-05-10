import React from "react";
import { motion } from "framer-motion";
import { CheckCircle, Circle, Sparkle, TrendUp, TreeStructure } from "@phosphor-icons/react";

const levels = [
  { value: "A1", title: "A1 Starter", group: "Starter", description: "You know a few words and want to build core phrases.", icon: Sparkle, color: "text-secondary", iconBg: "bg-secondary-container text-on-secondary-container" },
  { value: "A2", title: "A2 Elementary", group: "Starter", description: "You can handle simple sentences and everyday topics.", icon: Sparkle, color: "text-secondary", iconBg: "bg-secondary-container text-on-secondary-container" },
  { value: "B1", title: "B1 Independent", group: "Recommended", description: "You can hold basic conversations and want smoother speaking.", icon: TrendUp, color: "text-[#2F80ED]", iconBg: "bg-primary-fixed text-on-primary-fixed" },
  { value: "B2", title: "B2 Independent", group: "Independent", description: "You can discuss familiar topics and want more nuance.", icon: TrendUp, color: "text-[#2F80ED]", iconBg: "bg-primary-fixed text-on-primary-fixed" },
  { value: "C1", title: "C1 Proficient", group: "Proficient", description: "You speak fluently and want professional precision.", icon: TreeStructure, color: "text-tertiary", iconBg: "bg-tertiary-fixed text-on-tertiary-fixed" },
  { value: "C2", title: "C2 Mastery", group: "Proficient", description: "You want native-like control, rhetoric, and polish.", icon: TreeStructure, color: "text-tertiary", iconBg: "bg-tertiary-fixed text-on-tertiary-fixed" },
];

const LevelStep = ({ formData, updateData }) => {
  const selectedLevel = formData.level;

  const cardVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 30 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } },
  };

  return (
    <motion.section
      initial="hidden"
      animate="visible"
      exit="hidden"
      variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
      className="mx-auto flex w-full max-w-6xl flex-col items-center px-6 pb-32 pt-12"
    >
      <motion.div variants={cardVariants} className="mb-14 mt-12 w-full">
        <div className="mb-4 inline-flex items-center rounded-sm bg-surface-variant px-3 py-1">
          <span className="font-label text-[0.625rem] font-bold uppercase tracking-widest text-on-surface-variant">Step 02 / 04</span>
        </div>
        <h1 className="max-w-2xl font-display text-5xl font-extrabold leading-[1.1] tracking-tight text-on-surface md:text-6xl">
          What is your current level?
        </h1>
      </motion.div>

      <div className="relative z-10 grid w-full grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {levels.map((level) => {
          const Icon = level.icon;
          const selected = selectedLevel === level.value;
          return (
            <motion.button
              key={level.value}
              type="button"
              variants={cardVariants}
              onClick={() => updateData("level", level.value)}
              className={`group relative flex h-full cursor-pointer flex-col rounded-xl border p-6 text-left shadow-diffusion transition-all duration-300 ${
                selected ? "border-primary bg-[#f0f7ff] shadow-[0_0_20px_rgba(47,128,237,0.15)]" : "border-transparent bg-surface-container-lowest hover:bg-surface-container-low"
              }`}
            >
              <div className={`mb-6 flex h-14 w-14 items-center justify-center rounded-full ${level.iconBg}`}>
                <Icon weight="fill" className="text-3xl" />
              </div>
              <div className="flex-grow">
                <div className="mb-2 flex items-center gap-2">
                  <span className={`font-sans text-xs font-bold uppercase tracking-widest ${level.color}`}>{level.value} · {level.group}</span>
                </div>
                <h3 className="mb-3 font-display text-2xl font-bold text-on-surface">{level.title}</h3>
                <p className="text-sm font-medium leading-relaxed text-on-surface-variant">{level.description}</p>
              </div>
              <div className="mt-8 flex justify-end">
                {selected ? <CheckCircle weight="fill" className="text-2xl text-primary" /> : <Circle className="text-2xl text-outline transition-colors group-hover:text-primary" />}
              </div>
            </motion.button>
          );
        })}
      </div>

      <div className="fixed -right-24 top-1/2 -z-10 h-96 w-96 rounded-full bg-primary-container/5 blur-[100px]" />
      <div className="fixed -bottom-0 -left-24 -z-10 h-64 w-64 rounded-full bg-secondary-container/5 blur-[80px]" />
    </motion.section>
  );
};

export default LevelStep;
