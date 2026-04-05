import { motion } from "framer-motion";
import { MagnifyingGlass, UserCircle, Translate, Crown } from "@phosphor-icons/react";
import { useNavigate, Link, useLocation } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

const TopBar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isSubscribed, subscriptionTier } = useAuth();
  const navItems = [
    { label: "Explore", path: "/topics" },
    { label: "My Progress", path: "/dashboard" },
    { label: isSubscribed ? "Subscription" : "Upgrade", path: "/subscription" },
  ];

  return (
    <header className="flex justify-between items-center px-6 h-16 w-full fixed top-0 z-50 bg-white/80 backdrop-blur-md border-b border-zinc-200/50">
      <div className="flex items-center gap-8">
        <div 
          onClick={() => navigate("/")}
          className="flex items-center gap-2 cursor-pointer group"
        >
          <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-white transition-transform group-hover:scale-110">
            <Translate weight="fill" size={20} />
          </div>
          <span className="text-lg font-bold font-display tracking-tight">LingoAI</span>
        </div>
        
        <nav className="hidden md:flex gap-8">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.label}
                to={item.path}
              className={`text-sm font-bold tracking-tight cursor-pointer transition-colors ${
                isActive
                  ? "text-primary border-b-2 border-primary pb-1" 
                  : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              {item.label}
            </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <Link
          to="/subscription"
          className={`hidden md:inline-flex items-center gap-2 rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition-colors ${
            isSubscribed
              ? "bg-zinc-950 text-white"
              : "bg-primary/10 text-primary"
          }`}
        >
          <Crown weight="fill" size={14} />
          {isSubscribed ? subscriptionTier : "Free"}
        </Link>
        <div className="relative hidden sm:block">
          <MagnifyingGlass 
            size={18} 
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" 
          />
          <input 
            className="pl-10 pr-4 py-2 bg-zinc-100 border-none rounded-xl text-xs font-medium focus:ring-2 focus:ring-primary/20 w-64 transition-all focus:bg-white" 
            placeholder="Search topics..." 
            type="text"
          />
        </div>
        <Link to="/profile">
          <motion.div
            whileHover={{ scale: 1.1 }}
            className="cursor-pointer text-zinc-500 hover:text-primary transition-colors"
          >
            <UserCircle size={28} />
          </motion.div>
        </Link>
      </div>
    </header>
  );
};

export default TopBar;
