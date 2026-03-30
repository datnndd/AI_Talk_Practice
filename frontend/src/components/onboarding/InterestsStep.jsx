import React from "react";
import { motion } from "framer-motion";
import { 
  TerminalWindow, Coin, Palette, Flask, MusicNote, GameController, AirplaneTilt, FilmStrip, Scroll, Tree, Check, Brain
} from "@phosphor-icons/react";

const Topics = [
  { id: "technology", label: "Technology", icon: TerminalWindow, color: "primary" },
  { id: "business", label: "Business", icon: Coin, color: "zinc" },
  { id: "art", label: "Art", icon: Palette, color: "zinc" },
  { id: "science", label: "Science", icon: Flask, color: "zinc", colSpan: 2, desc: "Biology, Physics, Chemistry" },
  { id: "music", label: "Music", icon: MusicNote, color: "zinc" },
  { id: "gaming", label: "Gaming", icon: GameController, color: "zinc" },
  { id: "travel", label: "Travel", icon: AirplaneTilt, color: "primary" },
  { id: "movies", label: "Movies", icon: FilmStrip, color: "zinc" },
  { id: "history", label: "History", icon: Scroll, color: "zinc" },
  { id: "nature", label: "Nature", icon: Tree, color: "zinc" },
];

const InterestsStep = ({ formData, updateData }) => {
  // Convert comma separated string to array or handle array natively
  // The existing backend schema expects a string, so we store it as a string but manage array here
  const selectedTopics = formData.favorite_topics 
    ? formData.favorite_topics.split(",").map(s => s.trim()).filter(Boolean) 
    : [];

  const toggleTopic = (topicId) => {
    let newTopics = [...selectedTopics];
    if (newTopics.includes(topicId)) {
      newTopics = newTopics.filter(t => t !== topicId);
    } else {
      newTopics.push(topicId);
    }
    updateData("favorite_topics", newTopics.join(", "));
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1, 
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.9, y: 20 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  return (
    <motion.section 
      initial="hidden"
      animate="visible"
      exit="hidden"
      className="max-w-6xl mx-auto w-full px-6 flex flex-col items-center justify-center py-12 relative overflow-hidden"
    >
      <div className="absolute -right-20 top-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary-container blur-[100px] opacity-15 rounded-full animate-pulse-slow -z-10"></div>
      <div className="absolute -left-40 top-1/4 w-[300px] h-[300px] bg-secondary/10 blur-[100px] rounded-full -z-10"></div>
      
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Content Column */}
        <motion.div variants={itemVariants} className="lg:col-span-5 space-y-8">
          <div className="space-y-4">
            <span className="inline-block px-3 py-1 bg-surface-variant text-on-surface-variant text-xs font-bold tracking-widest uppercase rounded-sm">Step 03 / 04</span>
            <h1 className="text-5xl lg:text-7xl font-display font-extrabold tracking-tight text-on-surface leading-[1.1]">
              Tailor your <span className="text-primary">curriculum</span>
            </h1>
            <p className="text-lg text-on-surface-variant max-w-md leading-relaxed font-medium">
              Select topics you enjoy. Our AI will personalize your learning path to match your specific interests.
            </p>
          </div>

          <div className="hidden lg:flex items-center gap-6 p-6 bg-surface-container-low rounded-xl border border-outline-variant/10 shadow-sm">
            <div className="w-12 h-12 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container">
              <Brain weight="fill" className="text-2xl" />
            </div>
            <div>
              <div className="text-sm font-bold text-on-surface">Smart Personalization</div>
              <div className="text-xs text-on-surface-variant">Your content evolves with your choices</div>
            </div>
          </div>
        </motion.div>

        {/* Bento Topic Grid Column */}
        <motion.div variants={containerVariants} className="lg:col-span-7">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Topics.map((topic) => {
              const Icon = topic.icon;
              const isSelected = selectedTopics.includes(topic.id);
              
              if (topic.colSpan === 2) {
                return (
                  <motion.button
                    key={topic.id}
                    variants={itemVariants}
                    onClick={() => toggleTopic(topic.id)}
                    className={`group md:col-span-2 p-6 rounded-xl border-2 transition-all duration-300 flex items-center gap-6 h-32 text-left ${isSelected ? 'bg-primary-container text-on-primary-container border-transparent' : 'bg-surface-container-lowest border-outline-variant/30 hover:border-primary/50'}`}
                  >
                    <div className={`w-16 h-16 rounded-lg ${isSelected ? 'bg-white/20' : 'bg-surface-variant'} flex items-center justify-center shrink-0`}>
                      <Icon weight={isSelected ? "fill" : "regular"} className={`text-3xl ${isSelected ? 'text-white' : 'text-on-surface-variant group-hover:text-primary transition-colors'}`} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-display text-xl font-bold">{topic.label}</span>
                      <span className={`text-xs ${isSelected ? 'text-white/80' : 'text-on-surface-variant'}`}>{topic.desc}</span>
                    </div>
                    {isSelected && (
                      <div className="ml-auto bg-white/20 rounded-full p-1">
                        <Check weight="bold" className="text-sm text-white" />
                      </div>
                    )}
                  </motion.button>
                );
              }

              return (
                <motion.button
                  key={topic.id}
                  variants={itemVariants}
                  onClick={() => toggleTopic(topic.id)}
                  className={`group relative overflow-hidden p-6 rounded-xl border-2 transition-all duration-300 flex flex-col justify-between aspect-square md:aspect-auto md:h-32 text-left ${isSelected ? 'bg-primary-container text-on-primary-container border-transparent' : 'bg-surface-container-lowest border-outline-variant/30 hover:border-primary/50'}`}
                >
                  <Icon weight={isSelected ? "fill" : "regular"} className={`text-3xl ${isSelected ? 'opacity-80 group-hover:scale-110 transition-transform text-white' : 'text-on-surface-variant group-hover:text-primary transition-colors'}`} />
                  <span className="font-display text-xl font-bold">{topic.label}</span>
                  {isSelected && (
                    <div className="absolute top-4 right-4 bg-white/20 rounded-full p-1">
                      <Check weight="bold" className="text-sm text-white" />
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
};

export default InterestsStep;
