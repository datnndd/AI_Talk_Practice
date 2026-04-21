import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { isRouteActive } from "./navigationData";

const MOBILE_NAV_ITEMS = [
  {
    label: "Learn",
    path: "/dashboard",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/784035717e2ff1d448c0f6cc4efc89fb.svg",
  },
  {
    label: "Topics",
    path: "/topics",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/80a60f598d6a6b0493aeb4d7b93fc0e3.svg",
  },
  {
    label: "Leader",
    path: "/leaderboard",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/ca9178510134b4b0893dbac30b6670aa.svg",
  },
  {
    label: "Plan",
    path: "/subscription",
    icon: "https://d35aaqx5ub95lt.cloudfront.net/vendor/0e58a94dda219766d98c7796b910beee.svg",
  },
  {
    label: "Profile",
    path: "/profile",
    icon: "profile", // Special case for avatar
  },
];

const MobileNav = () => {
  const location = useLocation();
  const { user } = useAuth();
  
  const profileHandle = user?.display_name || user?.email?.split("@")[0] || "L";

  return (
    <footer className="fixed inset-x-0 bottom-0 z-50 lg:hidden bg-white border-t-2 border-[#e5e5e5] pb-safe">
      <div className="flex items-center justify-around px-2 py-3">
        {MOBILE_NAV_ITEMS.map((item) => {
          const isActive = isRouteActive(location.pathname, item.path);
          return (
            <Link key={item.label} to={item.path} className="flex-1">
              <motion.div
                whileTap={{ scale: 0.9 }}
                className={`flex flex-col items-center justify-center gap-1 rounded-xl py-2 transition-all ${
                  isActive
                    ? "bg-[#ddf4ff] text-[#1cb0f6]"
                    : "text-[#afafaf]"
                }`}
              >
                {item.icon === "profile" ? (
                  <div className={`h-7 w-7 overflow-hidden rounded-full border-2 ${isActive ? 'border-[#1cb0f6]' : 'border-[#e5e5e5]'}`}>
                    {user?.avatar ? (
                      <img src={user.avatar} alt="P" className="h-full w-full object-cover" />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-[#58CC02] text-[8px] text-white font-black">
                        {profileHandle.slice(0, 1).toUpperCase()}
                      </div>
                    )}
                  </div>
                ) : (
                  <img src={item.icon} alt={item.label} className={`h-7 w-7 object-contain ${isActive ? '' : 'grayscale opacity-70'}`} />
                )}
                <span className={`text-[10px] font-black uppercase tracking-wider ${isActive ? 'text-[#1cb0f6]' : 'text-[#afafaf]'}`}>
                  {item.label}
                </span>
              </motion.div>
            </Link>
          );
        })}
      </div>
    </footer>
  );
};

export default MobileNav;
