import { useAuth } from "@/features/auth/context/AuthContext";
import { Link } from "react-router-dom";
import { useTheme } from "@/shared/context/ThemeContext";
import { Sun, Moon } from "@phosphor-icons/react";

const TopBar = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  
  // Use real data if available, fallback to provided mock values
  const level = user?.level || 51;
  const streak = user?.streak || 1;
  const gems = user?.gems || 685;
  const lives = user?.lives || 5;
  const initials = user?.display_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || "D";

  return (
    <div className="flex items-center gap-6 px-8 py-4 bg-background border-b border-border sticky top-0 z-40">
      {/* Search Bar */}
      <div className="relative mr-auto max-w-md flex-1">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-search absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true">
          <path d="m21 21-4.34-4.34"></path>
          <circle cx="11" cy="11" r="8"></circle>
        </svg>
        <input 
          type="text" 
          placeholder="Nhập từ khóa để tìm kiếm..." 
          className="h-10 w-full rounded-full border border-border bg-card pl-11 pr-4 text-sm outline-none focus:border-primary transition-all"
        />
      </div>

      {/* Stats Area */}
      <div className="flex items-center gap-1 rounded-full border border-border bg-card px-2 py-1.5 shadow-sm">
        {/* Level */}
        <div className="flex items-center gap-2 px-3 py-1">
          <span className="text-lg leading-none">⭐</span>
          <div className="leading-tight">
            <p className="text-sm font-extrabold text-foreground">{level}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Cấp độ</p>
          </div>
        </div>
        
        <span className="h-6 w-px bg-border"></span>
        
        {/* Streak */}
        <button className="flex items-center gap-2 rounded-full px-3 py-1 transition-colors hover:bg-muted" type="button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-flame h-5 w-5 fill-brand-orange text-brand-orange" aria-hidden="true">
            <path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4"></path>
          </svg>
          <div className="text-left leading-tight">
            <p className="text-sm font-extrabold text-foreground">{streak}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Streak</p>
          </div>
        </button>
        
        <span className="h-6 w-px bg-border"></span>
        
        {/* Gems */}
        <div className="flex items-center gap-2 px-3 py-1">
          <span className="text-base leading-none">💎</span>
          <div className="leading-tight">
            <p className="text-sm font-extrabold text-brand-blue">{gems}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Gems</p>
          </div>
        </div>
        
        <span className="h-6 w-px bg-border"></span>
        
        {/* Lives */}
        <div className="flex items-center gap-2 px-3 py-1">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-heart h-5 w-5 fill-brand-red text-brand-red" aria-hidden="true">
            <path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"></path>
          </svg>
          <div className="leading-tight">
            <p className="text-sm font-extrabold text-brand-red">{lives}</p>
            <p className="-mt-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">Lives</p>
          </div>
        </div>
      </div>

      {/* Actions & Profile */}
      <div className="flex items-center gap-3">
        {/* Theme Toggle */}
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
  );
};

export default TopBar;
