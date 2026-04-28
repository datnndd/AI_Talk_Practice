import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { House, Medal, Notebook, Storefront, UserCircle } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";
import { isRouteActive } from "./navigationData";

const MOBILE_NAV_ITEMS = [
  {
    label: "Học",
    path: "/learn",
    Icon: House,
  },
  {
    label: "Luyện",
    path: "/topics",
    Icon: Notebook,
  },
  {
    label: "BXH",
    path: "/leaderboard",
    Icon: Medal,
  },
  {
    label: "Shop",
    path: "/shop",
    Icon: Storefront,
  },
  {
    label: "Hồ sơ",
    path: "/profile",
    Icon: UserCircle,
    usesAvatar: true,
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
          const Icon = item.Icon;
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
                {item.usesAvatar ? (
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
                  <Icon size={28} weight={isActive ? "fill" : "bold"} />
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
