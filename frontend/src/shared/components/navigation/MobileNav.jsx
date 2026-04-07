import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";

import { isRouteActive, learnerTabItems } from "./navigationData";

const MobileNav = () => {
  const location = useLocation();

  return (
    <footer className="fixed inset-x-0 bottom-0 z-50 lg:hidden">
      <div className="mx-auto max-w-2xl px-4 pb-4">
        <div className="flex items-center justify-around rounded-[28px] border border-[var(--panel-border)] bg-[var(--nav-bg)] px-3 py-3 shadow-[0_-10px_32px_-22px_rgba(15,23,42,0.28)] backdrop-blur-xl">
          {learnerTabItems.map((tab) => {
            const Icon = tab.icon;
            const isActive = isRouteActive(location.pathname, tab.path);
            return (
              <Link key={tab.label} to={tab.path} aria-current={isActive ? "page" : undefined}>
                <motion.div
                  whileTap={{ scale: 0.9 }}
                  className={`flex min-w-[72px] flex-col items-center justify-center gap-1 rounded-2xl px-4 py-2 cursor-pointer transition-all ${
                    isActive
                      ? "bg-primary text-white shadow-lg shadow-primary/20"
                      : "text-[var(--nav-muted)] hover:bg-[var(--chip-neutral-bg)]"
                  }`}
                >
                  <Icon weight={isActive ? "fill" : "regular"} size={22} />
                  <span className="text-[9px] font-black uppercase tracking-[0.18em]">{tab.label}</span>
                </motion.div>
              </Link>
            );
          })}
        </div>
      </div>
    </footer>
  );
};

export default MobileNav;
