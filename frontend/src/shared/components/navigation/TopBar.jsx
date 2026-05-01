import { Link } from "react-router-dom";
import { Fire, Moon, Sun, X } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useTheme } from "@/shared/context/ThemeContext";

const TopBar = () => {
  const { user, gamification, dailyCheckinReward, clearDailyCheckinReward } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const level = gamification?.xp?.level || 1;
  const coins = gamification?.coin?.balance || 0;
  const streak = gamification?.check_in?.current_streak || dailyCheckinReward?.streak_day || 0;
  const initials = user?.display_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "D";

  return (
    <>
      <div className="flex items-center gap-6 px-8 py-4 bg-background border-b border-border sticky top-0 z-40">
        <div className="ml-auto flex items-center gap-1 rounded-full border border-border bg-card px-2 py-1.5 shadow-sm">
          <div className="flex items-center gap-2 px-3 py-1">
            <span className="text-lg leading-none">⭐</span>
            <div className="leading-tight">
              <p className="text-sm font-extrabold text-foreground">{level}</p>
              <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Cấp độ</p>
            </div>
          </div>
          <span className="h-6 w-px bg-border" />
          <div className="flex items-center gap-2 px-3 py-1">
            <span className="text-base leading-none">🔥</span>
            <div className="leading-tight">
              <p className="text-sm font-extrabold text-[#ff9600]">{streak}</p>
              <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Streak</p>
            </div>
          </div>
          <span className="h-6 w-px bg-border" />
          <div className="flex items-center gap-2 px-3 py-1">
            <span className="text-base leading-none">🪙</span>
            <div className="leading-tight">
              <p className="text-sm font-extrabold text-brand-blue">{coins.toLocaleString("en-US")}</p>
              <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Coin</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={toggleTheme}
            aria-label="Chuyển chế độ sáng/tối" 
            className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card hover:bg-muted transition-colors text-foreground/70"
          >
            {isDark ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
          </button>

          <button 
            aria-label="Thông báo" 
            className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card hover:bg-muted transition-colors relative"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-bell h-5 w-5 text-foreground/70" aria-hidden="true">
              <path d="M10.268 21a2 2 0 0 0 3.464 0"></path>
              <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"></path>
            </svg>
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-brand-red border-2 border-card"></span>
          </button>
          
          <Link 
            to="/profile" 
            className="flex h-10 w-10 items-center justify-center rounded-full bg-foreground text-sm font-bold text-background hover:opacity-90 transition-opacity"
          >
            {initials}
          </Link>
        </div>
      </div>

      {dailyCheckinReward ? (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/45 px-4">
          <div className="relative w-full max-w-sm rounded-3xl bg-white p-6 text-center shadow-2xl">
            <button type="button" onClick={clearDailyCheckinReward} className="absolute right-4 top-4 rounded-full p-2 text-zinc-400 hover:bg-zinc-100">
              <X size={18} />
            </button>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-100 text-[#ff9600]">
              <Fire size={34} weight="fill" />
            </div>
            <p className="mt-5 text-[11px] font-black uppercase tracking-[0.22em] text-primary">Điểm danh hằng ngày</p>
            <h2 className="mt-2 text-2xl font-black text-zinc-950">Streak ngày {dailyCheckinReward.streak_day}</h2>
            <p className="mt-2 text-sm font-semibold text-zinc-500">Bạn đã đăng nhập hôm nay và nhận thưởng.</p>
            <div className="mt-5 rounded-2xl bg-amber-50 px-5 py-4 text-3xl font-black text-amber-700">
              +{dailyCheckinReward.coin_earned} Coin
            </div>
            <button type="button" onClick={clearDailyCheckinReward} className="mt-6 w-full rounded-xl bg-zinc-950 px-4 py-3 text-sm font-black text-white">
              Tuyệt vời
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
};

export default TopBar;
