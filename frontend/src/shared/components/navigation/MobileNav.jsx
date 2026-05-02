import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { Crown, House, Medal, Notebook, Storefront, UserCircle } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { isRouteActive } from "./navigationData";

const MOBILE_NAV_ITEMS = [
  {
    label: "Học",
    path: "/learn",
    Icon: House,
  },
  {
    label: "Luyện",
    path: "/dashboard",
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
  const hasProAccess = canAccessSubscriptionFeatures(user);

  return (
    <footer className="fixed inset-x-0 bottom-0 z-50 lg:hidden bg-white border-t-2 border-[#e5e5e5] pb-safe">
      <Link
        to="/subscription"
        className={`mx-3 mt-2 flex items-center justify-center gap-2 rounded-2xl px-3 py-2 text-[10px] font-black uppercase tracking-[0.16em] ${
          hasProAccess ? "bg-gradient-to-r from-amber-300 to-purple-500 text-white" : "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
        }`}
      >
        <Crown size={13} weight="fill" />
        {hasProAccess ? "Pro Unlocked" : "Nâng cấp Pro"}
      </Link>
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
                  <div className={`relative h-8 w-8 rounded-full p-[2px] ${
                    hasProAccess
                      ? "bg-gradient-to-br from-amber-200 to-yellow-500 shadow-[0_0_12px_rgba(251,191,36,0.7)]"
                      : "bg-gradient-to-br from-zinc-200 to-zinc-500 shadow-[0_0_6px_rgba(113,113,122,0.25)]"
                  }`}>
                    <div className="h-full w-full overflow-hidden rounded-full bg-[#58CC02]">
                      {user?.avatar ? (
                        <img src={user.avatar} alt="P" className="h-full w-full object-cover" />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center text-[8px] text-white font-black">
                          {profileHandle.slice(0, 1).toUpperCase()}
                        </div>
                      )}
                    </div>
                    <span className={`absolute -right-1 -top-1 flex h-4 w-4 rotate-12 items-center justify-center rounded-full border ${
                      hasProAccess ? "border-amber-200 bg-amber-300 text-amber-900" : "border-zinc-300 bg-zinc-200 text-zinc-500"
                    }`}>
                      <Crown size={9} weight="fill" />
                    </span>
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
