import { Fire, Star, Users } from '@phosphor-icons/react';
import { useAuth } from '@/features/auth/context/AuthContext';

const SidebarStreakCard = () => {
  const { user } = useAuth();
  const streak = user?.stats?.streak || 1;
  const streakFreezes = "1/2";
  
  const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
  const todayIndex = new Date().getDay();

  return (
    <div className="mt-8 mx-2 p-4 rounded-2xl border-2 border-[#e5e5e5] bg-white">
      <div className="flex items-start justify-between gap-2 mb-4">
        <div>
          <h3 className="text-lg font-black text-[#4b4b4b] leading-tight">{streak} day streak</h3>
          <p className="text-[11px] font-bold text-[#777777]">
            You have <strong className="text-[#1cb0f6]">{streakFreezes} Streak Freezes</strong>
          </p>
        </div>
        <Fire size={32} weight="fill" className="shrink-0 text-[#ff9600]" />
      </div>

      <div className="bg-[#f7f7f7] rounded-xl p-3 mb-4">
        <div className="grid grid-cols-7 gap-1 mb-1">
          {days.map((day, i) => (
            <div key={i} className={`text-center text-[10px] font-black ${i === todayIndex ? "text-[#ff9600]" : "text-[#afafaf]"}`}>
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {days.map((_, i) => (
            <div key={i} className="flex justify-center items-center h-6">
              {i === todayIndex ? (
                <Fire size={20} weight="fill" className="text-[#ff9600]" />
              ) : i < todayIndex ? (
                <div className="w-4 h-4 rounded-full bg-[#ff9600] opacity-20" />
              ) : (
                <div className="w-1.5 h-1.5 rounded-full bg-[#e5e5e5]" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 py-3 border-t-2 border-[#e5e5e5]">
        <Users size={40} weight="fill" className="shrink-0 text-[#1cb0f6]" />
        <div className="min-w-0">
          <h4 className="text-[12px] font-black text-[#4b4b4b]">Friend Streaks</h4>
          <p className="text-[10px] font-bold text-[#afafaf] leading-tight">0 active</p>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-3 border-t-2 border-[#e5e5e5]">
        <Star size={40} weight="fill" className="shrink-0 text-[#ffc800]" />
        <div className="min-w-0">
          <h4 className="text-[12px] font-black text-[#4b4b4b]">Streak Society</h4>
          <p className="text-[10px] font-bold text-[#afafaf] leading-tight truncate">Join for exclusive rewards!</p>
        </div>
      </div>
    </div>
  );
};

export default SidebarStreakCard;
