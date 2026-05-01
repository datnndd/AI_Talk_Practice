import { MobileNav, AppSidebar, TopBar } from "@/shared/components/navigation";
import SiteFooter from "@/shared/components/SiteFooter";

const AppLayout = ({ children, showMobileNav = true }) => {
  return (
    <div className="app-page-shell min-h-[100dvh] font-sans antialiased text-[var(--page-fg)]">
      {/* Sidebar - Desktop only */}
      <AppSidebar />
      
      {/* Content Area */}
      <div className="flex flex-col lg:pl-[256px]">
        <TopBar />
        
        <div className="flex-1">
          {/* Main Content */}
          <main className="min-w-0 flex-1 pb-28 md:pb-14">
            {children}
          </main>
          <SiteFooter />
        </div>
      </div>
      
      {showMobileNav ? <MobileNav /> : null}
    </div>
  );
};

export default AppLayout;
