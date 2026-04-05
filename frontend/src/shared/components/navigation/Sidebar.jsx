import { motion } from "framer-motion";
import { House, GraduationCap, Layout, MessengerLogo, UserCircle, GearSix, Question } from "@phosphor-icons/react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const menuItems = [
    { icon: House, label: "Home", path: "/" },
    { icon: Layout, label: "Dashboard", path: "/dashboard" },
    { icon: GraduationCap, label: "Topics", path: "/topics" },
    { icon: MessengerLogo, label: "Practice", path: "/practice/cafe-conversations" },
    { icon: UserCircle, label: "Profile", path: "/profile" },
  ];

  return (
    <aside className="hidden lg:flex flex-col fixed left-0 top-16 h-[calc(100dvh-64px)] p-4 bg-zinc-50 border-r border-zinc-200/50 w-64 group">
      <div className="mb-8 px-4">
        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] mb-4">Categories</p>
        <div className="space-y-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <motion.div
                key={item.label}
                whileHover={{ x: 4 }}
                onClick={() => item.path !== "#" && navigate(item.path)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl cursor-pointer transition-all duration-200 ${
                  isActive
                    ? "bg-primary text-white shadow-lg shadow-primary/20 font-bold"
                    : "text-zinc-500 hover:bg-zinc-200/50 hover:text-zinc-900 font-medium"
                }`}
              >
                <Icon weight={isActive ? "bold" : "regular"} size={20} />
                <span className="text-sm">{item.label}</span>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="mt-auto p-4 bg-white rounded-2xl shadow-sm border border-zinc-200/50 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-16 h-16 bg-primary/5 rounded-full -mr-8 -mt-8" />
        <div className="flex items-center gap-3 mb-4 relative z-10">
          <div className="w-10 h-10 rounded-full border-2 border-white shadow-sm overflow-hidden bg-primary/20 flex items-center justify-center text-primary font-bold">
            {user?.display_name?.charAt(0)?.toUpperCase()}
          </div>
          <div>
            <p className="text-xs font-bold text-zinc-900 line-clamp-1">{user?.display_name || "User"}</p>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">{user?.level || "Beginner"}</p>
          </div>
        </div>
        
        <button 
          onClick={() => { logout(); navigate("/login"); }}
          className="w-full relative z-10 mt-2 py-2 text-xs font-bold text-zinc-600 bg-zinc-100 hover:bg-zinc-200 rounded-lg transition-colors"
        >
          Logout
        </button>
      </div>
      {/* Removed skill progress bar for now */}
    </aside>
  );
};

export default Sidebar;
