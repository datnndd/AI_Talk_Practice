import { motion } from "framer-motion";
import { GraduationCap, User, Layout, Crown } from "@phosphor-icons/react";
import { Link, useLocation } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

const MobileNav = () => {
  const location = useLocation();
  const { isSubscribed } = useAuth();
  const tabs = [
    { icon: Layout, label: "Dashboard", path: "/dashboard" },
    { icon: GraduationCap, label: "Topics", path: "/topics" },
    { icon: isSubscribed ? User : Crown, label: isSubscribed ? "Profile" : "Upgrade", path: isSubscribed ? "/profile" : "/subscription" },
  ];

  return (
    <footer className="lg:hidden fixed bottom-0 w-full flex justify-around items-center px-4 py-3 z-50 bg-white/90 backdrop-blur-xl border-t border-zinc-200/50 shadow-[0_-4px_12px_rgba(0,0,0,0.05)] rounded-t-3xl">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = location.pathname === tab.path;
        return (
          <Link key={tab.label} to={tab.path}>
            <motion.div
              whileTap={{ scale: 0.9 }}
              className={`flex flex-col items-center justify-center gap-1 px-4 py-1.5 rounded-2xl cursor-pointer transition-all ${
                isActive
                  ? "bg-primary/10 text-primary font-bold"
                  : "text-zinc-500 hover:bg-zinc-100"
              }`}
            >
              <Icon weight={isActive ? "fill" : "regular"} size={22} />
              <span className="text-[10px] uppercase tracking-widest font-bold">{tab.label}</span>
            </motion.div>
          </Link>
        );
      })}
    </footer>
  );
};

export default MobileNav;
