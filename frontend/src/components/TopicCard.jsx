import { motion } from "framer-motion";
import { Clock, ChatCircle, ArrowRight } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

const TopicCard = ({ card }) => {
  const Icon = card.icon;
  
  return (
    <Link to={`/practice/${card.title.toLowerCase().replace(/ /g, '-')}`} className={card.size}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className={`w-full h-full ${card.bg || 'bg-white'} rounded-3xl p-8 shadow-sm border border-zinc-200/50 relative overflow-hidden group hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer`}
      >
        <div className="relative z-10 flex flex-col h-full">
          <div className="flex justify-between items-start mb-6">
            <div className={`p-4 ${card.iconBg || 'bg-zinc-100'} rounded-2xl transition-transform group-hover:scale-110 group-hover:rotate-3`}>
              <Icon weight="bold" size={32} className={card.iconColor || 'text-zinc-900'} />
            </div>
            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-[0.15em] border ${card.badgeStyles || 'bg-zinc-50 text-zinc-500 border-zinc-100'}`}>
              {card.level}
            </span>
          </div>
          
          <h3 className={`text-2xl font-bold mb-3 font-display ${card.textTitle || 'text-zinc-900'}`}>
            {card.title}
          </h3>
          
          <p className={`text-sm mb-8 leading-relaxed font-medium ${card.textBody || 'text-zinc-500'}`}>
            {card.description}
          </p>
          
          <div className="mt-auto flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-zinc-400 font-mono text-xs">
                <Clock size={16} />
                <span>{card.duration}</span>
              </div>
              <div className="flex items-center gap-1.5 text-zinc-400 font-bold uppercase tracking-wider text-[10px]">
                <ChatCircle size={16} />
                <span>{card.category}</span>
              </div>
            </div>
            <div className="text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all">
              <ArrowRight weight="bold" size={20} />
            </div>
          </div>
        </div>
        
        {card.overlay && (
          <div className="absolute right-0 bottom-0 w-1/3 h-full opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none overflow-hidden">
            <card.overlay />
          </div>
        )}
      </motion.div>
    </Link>
  );
};

export default TopicCard;
