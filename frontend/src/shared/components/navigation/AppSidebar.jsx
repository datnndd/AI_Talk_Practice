import { Link, useLocation } from "react-router-dom";
import { ChatCircleText, Crown, GraduationCap, Storefront, Trophy, UserCircle } from "@phosphor-icons/react";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { isRouteActive } from "./navigationData";
import BrandMark from "./BrandMark";

const NAV_ITEMS = [
  { label: "Luyện nói", path: "/dashboard", Icon: ChatCircleText },
  { label: "Lộ trình học", path: "/learn", Icon: GraduationCap },
  { label: "Bảng xếp hạng", path: "/leaderboard", Icon: Trophy },
  { label: "Cửa hàng", path: "/shop", Icon: Storefront },
  { label: "Hồ sơ", path: "/profile", Icon: UserCircle },
];
const AppSidebar = () => {
  const location = useLocation();
  const { user } = useAuth();
  const hasProAccess = canAccessSubscriptionFeatures(user);

  return (
    <aside className="fixed left-0 top-0 hidden h-screen w-64 flex-col border-r border-border bg-card px-4 py-6 lg:flex">
      <div className="mb-10 px-2 flex-shrink-0">
        <BrandMark to="/dashboard" />
      </div>
      
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = isRouteActive(location.pathname, item.path);
          const Icon = item.Icon;
          return (
            <Link
              key={item.label}
              to={item.path}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition ${
                isActive
                  ? "bg-sidebar-active text-sidebar-active-foreground border border-primary/30"
                  : "text-foreground/80 hover:bg-muted border border-transparent"
              }`}
            >
              <Icon size={20} weight={isActive ? "fill" : "bold"} />
              <span className="flex-1 text-left">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6">
        <Link to="/subscription" className={`flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-extrabold shadow-lg transition hover:-translate-y-0.5 hover:opacity-95 active:scale-95 ${
          hasProAccess
            ? "bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 text-amber-950 shadow-amber-300/40"
            : "bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500 text-amber-950 shadow-amber-300/45 ring-1 ring-yellow-200"
        }`}>
          <Crown size={18} weight="fill" />
          {hasProAccess ? "Pro Unlocked" : "Nâng cấp Pro"}
        </Link>
      </div>
    </aside>
  );
};

export default AppSidebar;
