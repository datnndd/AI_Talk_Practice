import { motion } from 'framer-motion';
import { Fire, Star, Users } from '@phosphor-icons/react';

const StreakPopover = ({ streak, streakFreezes = "1/2" }) => {
  const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
  const todayIndex = new Date().getDay();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -10 }}
      className="streak-popover"
    >
      <div className="p-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h3 className="text-2xl font-black text-[#4b4b4b] leading-none mb-1">{streak} day streak</h3>
            <p className="text-sm font-bold text-[#777777]">
              You only have <strong className="text-[#1cb0f6]">{streakFreezes} Streak Freezes</strong>!
            </p>
          </div>
          <Fire size={40} weight="fill" className="shrink-0 text-[#ff9600]" />
        </div>

        <div className="bg-[#f7f7f7] rounded-2xl p-4 mb-6">
          <div className="grid grid-cols-7 gap-2 mb-2">
            {days.map((day, i) => (
              <div key={i} className={`text-center text-xs font-black ${i === todayIndex ? "text-[#ff9600]" : "text-[#afafaf]"}`}>
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {days.map((_, i) => (
              <div key={i} className="flex justify-center items-center h-8">
                {i === todayIndex ? (
                  <Fire size={24} weight="fill" className="text-[#ff9600]" />
                ) : i < todayIndex ? (
                  <div className="w-5 h-5 rounded-full bg-[#ff9600] opacity-20" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-[#e5e5e5]" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="border-t-2 border-[#e5e5e5] pt-4 mb-4">
          <div className="flex items-center gap-4">
            <Users size={40} weight="fill" className="text-[#1cb0f6]" />
            <div className="flex-1">
              <h4 className="text-sm font-black text-[#4b4b4b]">Friend Streaks</h4>
              <p className="text-xs font-bold text-[#afafaf]">0 active Friend Streaks</p>
            </div>
            <button className="app-button-secondary py-1.5 px-3 text-[11px]">View List</button>
          </div>
        </div>

        <div className="border-t-2 border-[#e5e5e5] pt-4">
          <div className="flex items-center gap-4 mb-3">
            <Star size={48} weight="fill" className="text-[#ffc800]" />
            <div className="flex-1">
              <h4 className="text-sm font-black text-[#4b4b4b]">Streak Society</h4>
              <p className="text-[11px] font-bold text-[#afafaf] leading-tight">Reach a 7 day streak to join the Streak Society and earn exclusive rewards.</p>
            </div>
          </div>
          <button className="app-button-primary w-full py-2.5 text-xs">View More</button>
        </div>
      </div>
      
      <div className="streak-popover-arrow" />
    </motion.div>
  );
};

export default StreakPopover;
