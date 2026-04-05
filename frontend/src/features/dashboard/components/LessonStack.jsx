import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { CaretRight } from "@phosphor-icons/react";

const LessonItem = ({ emoji, title, level, duration, xp, delay }) => (
  <motion.div
    layout
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ duration: 0.5, delay }}
    className="flex items-center p-5 bg-white border border-zinc-100 rounded-3xl hover:border-primary/30 transition-all cursor-pointer group shadow-sm hover:shadow-md"
  >
    <div className="w-14 h-14 rounded-2xl bg-zinc-50 flex items-center justify-center text-3xl shadow-inner mr-5 group-hover:scale-110 transition-transform">
      {emoji}
    </div>
    <div className="flex-grow">
      <h4 className="font-black text-zinc-950 text-sm font-display tracking-tight">{title}</h4>
      <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-1">
        {level} • {duration} mins
      </p>
    </div>
    <div className="flex items-center gap-6">
      <span className="number-mono text-xs font-black text-emerald-600">+{xp} XP</span>
      <div className="w-9 h-9 rounded-full flex items-center justify-center bg-zinc-50 group-hover:bg-primary group-hover:text-white transition-all">
        <CaretRight weight="bold" size={16} />
      </div>
    </div>
  </motion.div>
);

const LessonStack = () => {
  const [lessons, setLessons] = useState([
    { id: 1, emoji: "☕", title: "Cafe Conversations", level: "Intermediate", duration: 8, xp: 45 },
    { id: 2, emoji: "✈️", title: "Airport Logistics", level: "Beginner", duration: 12, xp: 30 },
    { id: 3, emoji: "💼", title: "Business Etiquette", level: "Advanced", duration: 15, xp: 60 },
  ]);

  useEffect(() => {
    const timer = setInterval(() => {
      setLessons((prev) => {
        const [first, ...rest] = prev;
        return [...rest, first];
      });
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="md:col-span-8 md:row-span-2 bento-card rounded-[2.5rem] p-8 shadow-lg flex flex-col h-full overflow-hidden">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-xl font-black font-display text-zinc-950 flex items-center gap-3">
          The Intelligent List
          <span className="bg-zinc-100 text-[9px] py-1 px-2.5 rounded-full text-zinc-500 font-black tracking-widest uppercase">Auto-Sorting</span>
        </h2>
        <button className="text-primary text-[10px] font-black uppercase tracking-[0.2em] hover:underline">View Roadmap</button>
      </div>

      <div className="space-y-4 pr-1 overflow-y-auto custom-scrollbar flex-grow">
        <AnimatePresence mode="popLayout">
          {lessons.map((lesson, index) => (
            <LessonItem key={lesson.id} {...lesson} delay={index * 0.1} />
          ))}
        </AnimatePresence>
      </div>
    </section>
  );
};

export default LessonStack;
