import { CreditCard, Moon, Sun, Sparkle, SquaresFour, SignOut, UserList } from "@phosphor-icons/react";
import { useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { BrandMark } from "@/shared/components/navigation";

const defaultNavItems = [
  { label: "Users", icon: UserList, to: "/admin/users" },
  { label: "Scenario Library", icon: SquaresFour, anchor: "#scenario-library" },
  { label: "Generation Queue", icon: Sparkle, anchor: "#generation-queue" },
  { label: "Payments", icon: CreditCard, to: "/admin/payments" },
];

const AdminShell = ({ title, subtitle, theme, onToggleTheme, navItems = defaultNavItems, children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const initials = useMemo(() => {
    const seed = user?.display_name || user?.email || "A";
    return seed.slice(0, 2).toUpperCase();
  }, [user]);

  return (
    <div className={theme === "dark" ? "dark" : ""}>
      <div className="min-h-screen bg-zinc-100 text-zinc-900 transition-colors dark:bg-zinc-950 dark:text-zinc-50">
        <div className="grid min-h-screen lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="hidden border-r border-zinc-200 bg-white/80 p-6 backdrop-blur lg:block dark:border-zinc-800 dark:bg-zinc-900/80">
            <div className="mb-8">
              <BrandMark eyebrow="Admin Studio" />
            </div>

            <div className="space-y-1">
              {navItems.map((item) => {
                const ItemIcon = item.icon;
                const className = `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                  item.to && location.pathname === item.to
                    ? "bg-primary/10 text-primary dark:bg-primary/15 dark:text-white"
                    : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-white"
                }`;
                if (item.to) {
                  return (
                    <Link key={item.label} to={item.to} className={className}>
                      <ItemIcon size={18} />
                      {item.label}
                    </Link>
                  );
                }
                return (
                  <a key={item.label} href={item.anchor} className={className}>
                    <ItemIcon size={18} />
                    {item.label}
                  </a>
                );
              })}
            </div>

            <div className="mt-8 rounded-[28px] bg-gradient-to-br from-primary to-[#1d7df3] p-5 text-white shadow-xl shadow-primary/20">
              <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/70">Workflow</p>
              <h3 className="mt-3 font-display text-2xl font-black tracking-tight">
                Hybrid pre-generation for reusable speaking practice.
              </h3>
              <p className="mt-3 text-sm leading-6 text-white/80">
                Create strong scenario prompts once, then scale them into approved variations for teachers and learners.
              </p>
            </div>

            <div className="mt-auto pt-8">
              <div className="rounded-[28px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-zinc-900 text-sm font-black text-white dark:bg-zinc-100 dark:text-zinc-900">
                    {initials}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{user?.display_name || "Admin user"}</p>
                    <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">{user?.email}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    navigate("/login");
                  }}
                  className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  <SignOut size={16} />
                  Logout
                </button>
              </div>
            </div>
          </aside>

          <div className="min-w-0">
            <header className="sticky top-0 z-30 px-4 pt-4 md:px-8">
              <div className="rounded-[30px] border border-zinc-200/80 bg-white/80 px-5 py-5 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.25)] backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.3em] text-primary">Teacher Workspace</p>
                    <h1 className="mt-1 font-display text-3xl font-black tracking-tight md:text-4xl">{title}</h1>
                    <p className="mt-2 max-w-3xl text-sm text-zinc-500 dark:text-zinc-400">{subtitle}</p>
                  </div>
                  <button
                    type="button"
                    onClick={onToggleTheme}
                    className="inline-flex items-center justify-center gap-2 self-start rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-semibold text-zinc-700 shadow-sm transition hover:-translate-y-0.5 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
                  >
                    {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    {theme === "dark" ? "Light Mode" : "Dark Mode"}
                  </button>
                </div>

                <div className="mt-4 flex flex-wrap gap-2 lg:hidden">
                  {navItems.map((item) => {
                    const ItemIcon = item.icon;
                    const className = `inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition ${
                      item.to && location.pathname === item.to
                        ? "border-primary/30 bg-primary/10 text-primary dark:border-primary/30 dark:bg-primary/15 dark:text-white"
                        : "border-zinc-200 bg-white text-zinc-600 hover:text-primary dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
                    }`;
                    if (item.to) {
                      return (
                        <Link key={item.label} to={item.to} className={className}>
                          <ItemIcon size={14} />
                          {item.label}
                        </Link>
                      );
                    }
                    return (
                      <a key={item.label} href={item.anchor} className={className}>
                        <ItemIcon size={14} />
                        {item.label}
                      </a>
                    );
                  })}
                </div>
              </div>
            </header>

            <main className="px-4 py-6 md:px-8 md:py-8">{children}</main>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminShell;
