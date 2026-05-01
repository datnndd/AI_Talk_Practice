import { useMemo } from 'react';
import { BookOpen, Fire, Hexagon, Star } from '@phosphor-icons/react';
import { useAuth } from '@/features/auth/context/AuthContext';
import './RightSidePanel.css';

const RightSidePanel = () => {
  const { user, gamification } = useAuth();

  const checkIn = gamification?.check_in;
  const streakLabel = useMemo(() => {
    const streak = checkIn?.current_streak || 0;
    return `${streak} day${streak === 1 ? "" : "s"}`;
  }, [checkIn?.current_streak]);

  const stats = {
    courses: user?.preferences?.courses_count || 51,
    level: gamification?.xp?.level || 1,
    coins: gamification?.coin?.balance || 0,
    xp: gamification?.xp?.total || 0,
    streak: checkIn?.current_streak || 0,
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between px-2">
        <div className="stat-item">
          <BookOpen size={24} weight="fill" className="text-[#afafaf]" />
          <span className="stat-value text-[#afafaf]">{stats.courses}</span>
        </div>

        <div className="stat-item group relative">
          <Fire size={24} weight="fill" className="text-[#ff9600]" />
          <span className="stat-value text-[#ff9600]">{stats.streak}</span>
          <div className="pointer-events-none absolute left-1/2 top-9 z-50 -translate-x-1/2 opacity-0 transition group-hover:pointer-events-auto group-hover:opacity-100">
            <div className="streak-popover p-4">
              <div className="streak-popover-arrow" />
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase text-[#afafaf]">Daily streak</p>
                  <p className="mt-1 text-2xl font-black text-[#ff9600]">{streakLabel}</p>
                </div>
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#fff3df]">
                  <Fire size={26} weight="fill" className="text-[#ff9600]" />
                </div>
              </div>

              <div className="mt-4 rounded-lg bg-[#f7f7f7] p-3">
                <div className="flex items-center justify-between text-sm font-extrabold">
                  <span className="text-[#777777]">
                    {checkIn?.checked_in_today ? "Auto checked in today" : "Next login reward"}
                  </span>
                  <span className="text-[#1cb0f6]">+{checkIn?.today_coin_reward || 0} Coin</span>
                </div>
              </div>

              <p className="mt-4 rounded-lg bg-[#fff3df] px-3 py-2 text-center text-xs font-extrabold text-[#ff9600]">
                Coin tự nhận khi bạn đăng nhập mỗi ngày.
              </p>
            </div>
          </div>
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
