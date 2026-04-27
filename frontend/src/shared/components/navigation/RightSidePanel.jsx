import { useState } from 'react';
import StreakPanel from './StreakPanel';
import StreakPopover from './StreakPopover';
import { AnimatePresence } from 'framer-motion';
import { BookOpen, Fire, Heart, Hexagon } from '@phosphor-icons/react';
import { useAuth } from '@/features/auth/context/AuthContext';
import './RightSidePanel.css';

const RightSidePanel = () => {
  const { user } = useAuth();
  const [showStreakPopover, setShowStreakPopover] = useState(false);
  
  const stats = {
    courses: user?.preferences?.courses_count || 51,
    streak: user?.stats?.streak || 1,
    gems: user?.stats?.gems || 685,
    hearts: user?.stats?.hearts || 5,
    xp: user?.stats?.daily_xp || 0,
    goalXp: 10,
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Stats Menu */}
      <div className="flex items-center justify-between px-2">
        <div className="stat-item">
          <BookOpen size={24} weight="fill" className="text-[#afafaf]" />
          <span className="stat-value text-[#afafaf]">{stats.courses}</span>
        </div>

        <div 
          className="relative stat-item"
          onClick={() => setShowStreakPopover(!showStreakPopover)}
        >
          <Fire size={24} weight="fill" className="text-[#ff9600]" />
          <span className={`stat-value ${stats.streak > 0 ? "text-[#ff9600]" : "text-[#afafaf]"}`}>{stats.streak}</span>
          
          <AnimatePresence>
            {showStreakPopover && (
              <>
                <div 
                  className="fixed inset-0 z-40 bg-transparent"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowStreakPopover(false);
                  }}
                />
                <div className="z-50 absolute top-full left-1/2 -translate-x-1/2 mt-4 cursor-default">
                   <StreakPopover streak={stats.streak} />
                </div>
              </>
            )}
          </AnimatePresence>
        </div>

        <div className="stat-item">
          <Hexagon size={24} weight="fill" className="text-[#1cb0f6]" />
          <span className="stat-value text-[#1cb0f6]">{stats.gems}</span>
        </div>

        <div className="stat-item">
          <Heart size={24} weight="fill" className="text-[#ff4b4b]" />
          <span className="stat-value text-[#ff4b4b]">{stats.hearts}</span>
        </div>
      </div>

      <StreakPanel />

    </div>
  );
};

export default RightSidePanel;
