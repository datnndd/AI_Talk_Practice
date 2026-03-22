import { motion } from "framer-motion";
import { Cpu, Path, ChartLineUp, Flag } from "@phosphor-icons/react";

const BentoGrid = () => {
  const cards = [
    {
      title: "Contextual AI Conversations",
      description: "Our AI doesn't just read scripts. It understands context, sarcasm, and regional dialects to give you a true immersion experience.",
      icon: <Cpu weight="bold" size={32} />,
      size: "md:col-span-8",
      bg: "bg-white",
      iconBg: "bg-blue-50 text-primary",
      extra: (
        <div className="absolute bottom-0 right-0 w-1/2 opacity-5 group-hover:opacity-10 transition-opacity">
          <Cpu weight="light" size={240} />
        </div>
      )
    },
    {
      title: "Personalized Curriculum",
      description: "Lessons adapt in real-time based on your mistakes and successes.",
      icon: <Path weight="bold" size={32} />,
      size: "md:col-span-4",
      bg: "bg-zinc-950 text-white",
      iconBg: "bg-white/10 text-white",
      extra: (
        <div className="mt-8">
          <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: "75%" }}
              transition={{ duration: 1, delay: 0.5 }}
              className="h-full bg-primary"
            />
          </div>
          <p className="text-[10px] uppercase tracking-widest mt-3 text-zinc-500 font-bold">75% Daily Goal Reached</p>
        </div>
      )
    },
    {
      title: "Granular Analytics",
      description: "Visualize your fluency growth with detailed heatmaps of your vocabulary and grammar strength.",
      icon: <ChartLineUp weight="bold" size={32} />,
      size: "md:col-span-4",
      bg: "bg-white",
      iconBg: "bg-orange-50 text-orange-500",
      extra: (
        <div className="mt-auto pt-8 flex gap-2 items-end h-24">
          {[40, 60, 90, 70, 85].map((h, i) => (
            <motion.div
              key={i}
              initial={{ height: 0 }}
              whileInView={{ height: `${h}%` }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="w-full bg-zinc-100 rounded-t-lg group-hover:bg-primary transition-colors duration-500"
              style={{ opacity: i === 2 ? 1 : 0.4 }}
            />
          ))}
        </div>
      )
    },
    {
      title: "30+ Major Languages",
      description: "From Japanese to Portuguese, learn with native-level AI accuracy across dozens of dialects.",
      icon: <Flag weight="bold" size={32} />,
      size: "md:col-span-8",
      bg: "bg-primary/5 border-primary/10",
      iconBg: "bg-white text-primary shadow-sm",
      extra: (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mt-8">
          {["ESP", "FRA", "GER", "JPN", "ITA", "BRA"].map((lang, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.1, rotate: 5 }}
              className="w-12 h-12 rounded-xl bg-white shadow-sm flex items-center justify-center text-[10px] font-bold text-zinc-400 cursor-default border border-zinc-100 uppercase tracking-tighter"
            >
              {lang}
            </motion.div>
          ))}
        </div>
      )
    }
  ];

  return (
    <section className="py-24 bg-zinc-50/50" id="features">
      <div className="max-w-7xl mx-auto px-6">
        <div className="max-w-2xl mb-16">
          <h2 className="text-4xl font-bold tracking-tight text-zinc-950 mb-4 font-display">
            Mastery built into every interaction
          </h2>
          <p className="text-zinc-500 text-lg font-medium">
            Our platform uses advanced neural processing to create a learning path that's as unique as you are.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {cards.map((card, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`${card.size} ${card.bg} p-10 rounded-4xl border border-zinc-200/50 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.03)] flex flex-col justify-between overflow-hidden relative group hover:shadow-xl transition-all duration-500`}
            >
              <div className="relative z-10">
                <div className={`${card.iconBg} w-14 h-14 rounded-2xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110 group-hover:rotate-3`}>
                  {card.icon}
                </div>
                <h3 className="text-2xl font-bold mb-4 font-display">{card.title}</h3>
                <p className={`${card.bg.includes('zinc-950') ? 'text-zinc-400' : 'text-zinc-500'} max-w-sm font-medium leading-relaxed`}>
                  {card.description}
                </p>
              </div>
              {card.extra}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BentoGrid;
