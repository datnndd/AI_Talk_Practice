import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { isRouteActive } from "./navigationData";

const NAV_ITEMS = [
  {
    label: "Learn",
    path: "/dashboard",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/784035717e2ff1d448c0f6cc4efc89fb.svg",
  },
  {
    label: "Letters",
    path: "/topics",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/80a60f598d6a6b0493aeb4d7b93fc0e3.svg",
  },
  {
    label: "Practice",
    path: "/practice-hub", // Mapping to a hub if exists, or just dashboard
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/5187f6694476a769d4a4e28149867e3e.svg",
    badge: true,
  },
  {
    label: "Leaderboards",
    path: "/leaderboard",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/ca9178510134b4b0893dbac30b6670aa.svg",
  },
  {
    label: "Quests",
    path: "/quests",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/7ef36bae3f9d68fc763d3451b5167836.svg",
  },
  {
    label: "Shop",
    path: "/subscription",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/0e58a94dda219766d98c7796b910beee.svg",
  },
];

const DuolingoSidebar = () => {
  const location = useLocation();
  const { user } = useAuth();
  
  const profileHandle = user?.display_name || user?.email?.split("@")[0] || "Learner";

  return (
    <nav className="fixed left-0 top-0 hidden h-full w-[256px] flex-col border-r-2 border-[#e5e5e5] bg-white px-4 py-8 lg:flex">
      {/* Logo */}
      <Link to="/dashboard" className="mb-10 px-4">
        <img 
          src="https://d35aaqx5ub95lt.cloudfront.net/vendor/70a4be81077a8037698067f583816ff9.svg" 
          alt="Duolingo Logo" 
          className="w-32"
        />
      </Link>

      {/* Nav Items */}
      <div className="flex flex-1 flex-col gap-2">
        {NAV_ITEMS.map((item) => {
          const isActive = isRouteActive(location.pathname, item.path);
          return (
            <Link
              key={item.label}
              to={item.path}
              className={`group flex items-center gap-4 rounded-xl px-4 py-3 font-black uppercase tracking-wide transition-all ${
                isActive
                  ? "border-2 border-b-4 border-[#84d8ff] bg-[#ddf4ff] text-[#1cb0f6]"
                  : "border-2 border-transparent hover:bg-[#f7f7f7] text-[#777777]"
              }`}
            >
              <div className="relative h-8 w-8 shrink-0">
                <img src={item.icon} alt={item.label} className="h-full w-full object-contain" />
                {item.badge && (isActive ? null : (
                  <div className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-[#ff4b4b] border-2 border-white" />
                ))}
              </div>
              <span className="text-[15px]">{item.label}</span>
            </Link>
          );
        })}

        {/* Profile Link */}
        <Link
          to="/profile"
          className={`group flex items-center gap-4 rounded-xl px-4 py-3 font-black uppercase tracking-wide transition-all ${
            isRouteActive(location.pathname, "/profile")
              ? "border-2 border-b-4 border-[#84d8ff] bg-[#ddf4ff] text-[#1cb0f6]"
              : "border-2 border-transparent hover:bg-[#f7f7f7] text-[#777777]"
          }`}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-[#e5e5e5]">
            {user?.avatar ? (
              <img src={user.avatar} alt="Profile" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-[#58CC02] text-[10px] text-white">
                {profileHandle.slice(0, 2).toUpperCase()}
              </div>
            )}
          </div>
          <span className="text-[15px]">Profile</span>
        </Link>
      </div>

      {/* More Button */}
      <button className="mt-auto flex items-center gap-4 rounded-xl border-2 border-transparent px-4 py-3 font-black uppercase tracking-wide text-[#777777] transition-all hover:bg-[#f7f7f7]">
        <div className="h-8 w-8 shrink-0">
          <img src="https://d35aaqx5ub95lt.cloudfront.net/vendor/7159c0b5d4250a5aea4f396d53f17f0c.svg" alt="More" />
        </div>
        <span className="text-[15px]">More</span>
      </button>
    </nav>
  );
};

export default DuolingoSidebar;
