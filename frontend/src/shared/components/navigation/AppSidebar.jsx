import { Link, useLocation } from "react-router-dom";
import { isRouteActive } from "./navigationData";
import BrandMark from "./BrandMark";

const NAV_ITEMS = [
  {
    label: "Học tập",
    path: "/learn",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-house h-5 w-5" aria-hidden="true">
        <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"></path>
        <path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
      </svg>
    ),
  },
  {
    label: "Tổng quan",
    path: "/dashboard",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-layout-dashboard h-5 w-5" aria-hidden="true">
        <rect width="7" height="9" x="3" y="3" rx="1"></rect>
        <rect width="7" height="5" x="14" y="3" rx="1"></rect>
        <rect width="7" height="9" x="14" y="12" rx="1"></rect>
        <rect width="7" height="5" x="3" y="16" rx="1"></rect>
      </svg>
    ),
  },
  {
    label: "Thực hành",
    path: "/topics",
    badge: 2,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-dumbbell h-5 w-5" aria-hidden="true">
        <path d="M17.596 12.768a2 2 0 1 0 2.829-2.829l-1.768-1.767a2 2 0 0 0 2.828-2.829l-2.828-2.828a2 2 0 0 0-2.829 2.828l-1.767-1.768a2 2 0 1 0-2.829 2.829z"></path>
        <path d="m2.5 21.5 1.4-1.4"></path>
        <path d="m20.1 3.9 1.4-1.4"></path>
        <path d="M5.343 21.485a2 2 0 1 0 2.829-2.828l1.767 1.768a2 2 0 1 0 2.829-2.829l-6.364-6.364a2 2 0 1 0-2.829 2.829l1.768 1.767a2 2 0 0 0-2.828 2.829z"></path>
        <path d="m9.6 14.4 4.8-4.8"></path>
      </svg>
    ),
  },
  {
    label: "Bảng xếp hạng",
    path: "/leaderboard",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trophy h-5 w-5" aria-hidden="true">
        <path d="M10 14.66v1.626a2 2 0 0 1-.976 1.696A5 5 0 0 0 7 21.978"></path>
        <path d="M14 14.66v1.626a2 2 0 0 0 .976 1.696A5 5 0 0 1 17 21.978"></path>
        <path d="M18 9h1.5a1 1 0 0 0 0-5H18"></path>
        <path d="M4 22h16"></path>
        <path d="M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"></path>
        <path d="M6 9H4.5a1 1 0 0 1 0-5H6"></path>
      </svg>
    ),
  },
  {
    label: "Cửa hàng",
    path: "/shop",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-store h-5 w-5" aria-hidden="true">
        <path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"></path>
        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
        <path d="M15 22v-6a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v6"></path>
        <path d="M2 7h20"></path>
        <path d="M22 7v3a2 2 0 0 1-4 0V7"></path>
        <path d="M18 7v3a2 2 0 0 1-4 0V7"></path>
        <path d="M14 7v3a2 2 0 0 1-4 0V7"></path>
        <path d="M10 7v3a2 2 0 0 1-4 0V7"></path>
        <path d="M6 7v3a2 2 0 0 1-4 0V7"></path>
      </svg>
    ),
  },
  {
    label: "Hồ sơ",
    path: "/profile",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-user h-5 w-5" aria-hidden="true">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
    ),
  },
];

const AppSidebar = () => {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 hidden h-screen w-64 flex-col border-r border-border bg-card px-4 py-6 lg:flex">
      <div className="mb-10 px-2 flex-shrink-0">
        <BrandMark to="/dashboard" />
      </div>
      
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = isRouteActive(location.pathname, item.path);
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
              {item.icon}
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-red px-1.5 text-xs font-bold text-white">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6">
        <Link to="/shop" className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-promo-from to-promo-to px-4 py-3 text-sm font-extrabold text-white shadow-md transition hover:opacity-90 active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sparkles h-4 w-4" aria-hidden="true">
            <path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"></path>
            <path d="M20 2v4"></path>
            <path d="M22 4h-4"></path>
            <circle cx="4" cy="20" r="2"></circle>
          </svg>
          Upgrade Pro
        </Link>
      </div>
    </aside>
  );
};

export default AppSidebar;
