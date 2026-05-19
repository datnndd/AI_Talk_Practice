import { ChartBar, CreditCard, Gift, GlobeHemisphereWest, GraduationCap, Moon, Robot, Sun, SquaresFour, SignOut, UserList } from "@phosphor-icons/react";
import { useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useTheme } from "@/shared/context/ThemeContext";
import { BrandMark } from "@/shared/components/navigation";

const defaultNavItems = [
  { label: "Dashboard", icon: ChartBar, to: "/admin/dashboard" },
  { label: "Users", icon: UserList, to: "/admin/users" },
  { label: "Scenario Library", icon: SquaresFour, to: "/admin/scenarios" },
  { label: "Characters", icon: Robot, to: "/admin/characters" },
  { label: "Curriculum", icon: GraduationCap, to: "/admin/curriculum" },
  { label: "Shop", icon: Gift, to: "/admin/shop" },
  { label: "Payments", icon: CreditCard, to: "/admin/payments" },
  { label: "Site Settings", icon: GlobeHemisphereWest, to: "/admin/site" },
];

const AdminShell = ({ title, subtitle, navItems = defaultNavItems, children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const initials = useMemo(() => {
    const seed = user?.display_name || user?.email || "A";
    return seed.slice(0, 2).toUpperCase();
  }, [user]);

  return (
    <div className="app-page-shell min-h-[100dvh] font-sans antialiased text-[var(--page-fg)]">
      <div className="min-h-screen text-[var(--page-fg)] transition-colors">
        <div className="grid min-h-screen lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="sticky top-0 hidden h-screen border-r border-border bg-background p-6 backdrop-blur lg:flex lg:flex-col">
            <div className="mb-8">
              <BrandMark eyebrow="Admin Studio" />
            </div>

            <nav className="space-y-1">
              {navItems.map((item) => {
                const ItemIcon = item.icon;
                const isActive = item.to ? location.pathname === item.to : location.hash === item.anchor;
                const className = `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                  isActive
                    ? "border border-primary/40 bg-primary/20 text-[var(--page-fg)] shadow-sm shadow-primary/10"
                    : "border border-transparent text-[var(--page-muted)] hover:border-border hover:bg-muted hover:text-[var(--page-fg)]"
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
            </nav>

            <div className="mt-auto pt-8">
              <div className="rounded-[28px] border border-border bg-card p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue to-primary text-sm font-black text-white">
                    {initials}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{user?.display_name || "Admin user"}</p>
                    <p className="truncate text-xs text-[var(--page-muted)]">{user?.email}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    navigate("/login");
                  }}
                  className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-[var(--page-muted)] transition hover:bg-muted hover:text-[var(--page-fg)]"
                >
                  <SignOut size={16} />
                  Logout
                </button>
              </div>
            </div>
          </aside>

          <div className="min-w-0">
            <header className="sticky top-0 z-30 border-b border-border bg-background px-4 py-3 backdrop-blur md:px-8">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="truncate font-display text-xl font-black tracking-tight md:text-2xl">{title}</h1>
                  {subtitle ? (
                    <p className="mt-0.5 truncate text-xs text-[var(--page-muted)]">{subtitle}</p>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={toggleTheme}
                    aria-label="Chuyển chế độ sáng/tối"
                    title="Chuyển chế độ sáng/tối"
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card text-foreground/70 transition-colors hover:bg-muted"
                  >
                    {isDark ? <Sun size={20} weight="bold" /> : <Moon size={20} weight="bold" />}
                  </button>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2 lg:hidden">
                {navItems.map((item) => {
                  const ItemIcon = item.icon;
                  const isActive = item.to ? location.pathname === item.to : location.hash === item.anchor;
                  const className = `inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition ${
                    isActive
                      ? "border-primary/40 bg-primary/20 text-[var(--page-fg)]"
                      : "border-border bg-card text-[var(--page-muted)] hover:bg-muted hover:text-[var(--page-fg)]"
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
            </header>

            <main className="px-4 py-6 md:px-8 md:py-8">{children}</main>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminShell;
