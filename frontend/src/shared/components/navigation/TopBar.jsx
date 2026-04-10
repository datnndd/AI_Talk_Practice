import { motion } from "framer-motion";
import { Crown, Moon, SignOut, Sun, UserCircle } from "@phosphor-icons/react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { useTheme } from "@/shared/context/ThemeContext";
import BrandMark from "./BrandMark";
import {
  adminWorkspaceNavItems,
  formatPlanLabel,
  isRouteActive,
  learnerNavItems,
} from "./navigationData";

const TopBar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isSubscribed, subscriptionTier, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const planLabel = formatPlanLabel(isSubscribed, subscriptionTier);
  const isAdmin = Boolean(user?.is_admin);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-[1600px] px-4 pt-4 md:px-6">
        <div className="flex h-[72px] items-center justify-between rounded-[28px] border border-[var(--panel-border)] bg-[var(--nav-bg)] px-4 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.28)] backdrop-blur-xl md:px-5">
          <div className="flex min-w-0 items-center gap-6">
            <BrandMark eyebrow="Learner Workspace" />

            <nav className="hidden items-center gap-2 xl:flex">
              {learnerNavItems.map((item) => {
                const isActive = isRouteActive(location.pathname, item.path);

                return (
                  <Link
                    key={item.label}
                    to={item.path}
                    aria-current={isActive ? "page" : undefined}
                    className={`rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition ${
                      isActive
                        ? "bg-primary text-white shadow-lg shadow-primary/20"
                        : "text-[var(--nav-muted)] hover:bg-[var(--chip-neutral-bg)] hover:text-[var(--nav-text)]"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {isAdmin ? (
              <div className="hidden items-center gap-2 2xl:flex">
                <span className="ml-2 rounded-full border border-primary/15 bg-primary/6 px-3 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-primary">
                  Admin
                </span>
                {adminWorkspaceNavItems.map((item) => {
                  const isActive = isRouteActive(location.pathname, item.path);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.label}
                      to={item.path}
                      aria-current={isActive ? "page" : undefined}
                      className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition ${
                        isActive
                          ? "bg-zinc-950 text-white shadow-lg shadow-zinc-950/15"
                          : "text-[var(--nav-muted)] hover:bg-[var(--chip-neutral-bg)] hover:text-[var(--nav-text)]"
                      }`}
                    >
                      <Icon size={14} weight={isActive ? "fill" : "regular"} />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            ) : null}
          </div>

          <div className="flex items-center gap-2 md:gap-3">
            {isAdmin ? (
              <div className="hidden items-center gap-2 md:flex 2xl:hidden">
                {adminWorkspaceNavItems.map((item) => {
                  const isActive = isRouteActive(location.pathname, item.path);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.label}
                      to={item.path}
                      className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition ${
                        isActive
                          ? "bg-primary text-white shadow-lg shadow-primary/20"
                          : "border border-primary/20 bg-primary/8 text-primary hover:-translate-y-0.5"
                      }`}
                    >
                      <Icon size={14} weight={isActive ? "fill" : "regular"} />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            ) : null}

            <Link
              to="/subscription"
              className={`hidden items-center gap-2 rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition md:inline-flex ${
                isSubscribed ? "bg-zinc-950 text-white" : "bg-primary/10 text-primary"
              }`}
            >
              <Crown weight="fill" size={14} />
              {planLabel}
            </Link>

            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={toggleTheme}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-[var(--panel-border)] text-[var(--nav-muted)] transition hover:-translate-y-0.5 hover:text-primary"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
            </motion.button>

            <motion.button
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleLogout}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-bg)] px-3 text-[var(--nav-text)] transition hover:-translate-y-0.5 hover:border-rose-300 hover:text-rose-500 md:px-4"
              aria-label="Logout"
            >
              <SignOut size={18} weight="bold" />
              <span className="hidden text-[10px] font-black uppercase tracking-[0.18em] md:inline">
                Logout
              </span>
            </motion.button>

            <Link to="/profile" className="inline-flex items-center gap-3 rounded-2xl border border-[var(--panel-border)] bg-[var(--panel-bg)] px-3 py-2 transition hover:-translate-y-0.5">
              <UserCircle size={26} className="text-primary" weight="duotone" />
              <div className="hidden text-left md:block">
                <p className="max-w-[11rem] truncate text-xs font-bold text-[var(--nav-text)]">
                  {user?.display_name || user?.email?.split("@")[0] || "Learner"}
                </p>
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--nav-muted)]">
                  {isAdmin ? "Admin access" : `${planLabel} mode`}
                </p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
