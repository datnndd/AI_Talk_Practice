import { motion } from "framer-motion";
import { User, Lightning, Palette, ShieldCheck } from "@phosphor-icons/react";

const navItems = [
  { id: "profile", label: "Profile", icon: User, description: "Identity & Personal Info" },
  { id: "learning", label: "Learning", icon: Lightning, description: "Language & Goals" },
  { id: "appearance", label: "Appearance", icon: Palette, description: "Theme & Layout" },
  { id: "account", label: "Account", icon: ShieldCheck, description: "Security & Plan" },
];

const ProfileSidebar = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="md:col-span-3 lg:col-span-3">
      <div className="sticky top-28 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <motion.button
              key={item.id}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(item.id)}
              className={`group flex w-full items-center gap-4 rounded-2xl p-4 text-left transition-all ${
                isActive
                  ? "bg-primary/10 shadow-[inset_0_0_0_1px_rgba(0,90,182,0.1)]"
                  : "hover:bg-white/40"
              }`}
            >
              <div
                className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl transition-all ${
                  isActive
                    ? "bg-primary text-white shadow-lg shadow-primary/20"
                    : "bg-white/50 text-[var(--page-muted)] group-hover:bg-white group-hover:text-primary"
                }`}
              >
                <Icon size={20} weight={isActive ? "fill" : "bold"} />
              </div>
              <div className="flex-1 overflow-hidden">
                <p
                  className={`text-sm font-black transition-colors ${
                    isActive ? "text-primary" : "text-[var(--page-fg)]"
                  }`}
                >
                  {item.label}
                </p>
                <p className="app-text-subtle truncate text-[10px] font-bold uppercase tracking-wider">
                  {item.description}
                </p>
              </div>
              {isActive && (
                <motion.div
                  layoutId="active-pill"
                  className="h-2 w-2 rounded-full bg-primary"
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </aside>
  );
};

export default ProfileSidebar;
