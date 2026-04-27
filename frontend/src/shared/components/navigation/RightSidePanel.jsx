import { useEffect, useState } from 'react';
import { BookOpen, Hexagon, Star } from '@phosphor-icons/react';
import { useAuth } from '@/features/auth/context/AuthContext';
import { gamificationApi } from '@/features/gamification/api/gamificationApi';
import './RightSidePanel.css';

const RightSidePanel = () => {
  const { user } = useAuth();
  const [gamification, setGamification] = useState(null);

  useEffect(() => {
    gamificationApi.getDashboard().then(setGamification).catch(() => {});
  }, []);
  
  const stats = {
    courses: user?.preferences?.courses_count || 51,
    level: gamification?.xp?.level || 1,
    coins: gamification?.coin?.balance || 0,
    xp: gamification?.xp?.total || 0,
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Stats Menu */}
      <div className="flex items-center justify-between px-2">
        <div className="stat-item">
          <BookOpen size={24} weight="fill" className="text-[#afafaf]" />
          <span className="stat-value text-[#afafaf]">{stats.courses}</span>
        </div>

        <div className="stat-item">
          <Star size={24} weight="fill" className="text-[#ff9600]" />
          <span className="stat-value text-[#ff9600]">{stats.level}</span>
        </div>

        <div className="stat-item">
          <Hexagon size={24} weight="fill" className="text-[#1cb0f6]" />
          <span className="stat-value text-[#1cb0f6]">{stats.coins}</span>
        </div>

        <div className="stat-item">
          <span className="text-xs font-black text-[#58cc02]">XP</span>
          <span className="stat-value text-[#58cc02]">{stats.xp}</span>
        </div>
      </div>
    </div>
  );
};

export default RightSidePanel;
