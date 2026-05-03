import { MobileNav, AppSidebar, TopBar } from "@/shared/components/navigation";
import SiteFooter from "@/shared/components/SiteFooter";

const AppLayout = ({ children, showMobileNav = true }) => {
  return (
    <div className="app-page-shell min-h-[100dvh] font-sans antialiased text-[var(--page-fg)]">
      {/* Sidebar - Desktop only */}
      <AppSidebar />
      
      {/* Content Area */}
      <div className="flex min-h-[100dvh] flex-col lg:pl-[256px]">
        <TopBar />
        
        <div className="app-layout-container flex flex-1 flex-col">
          {/* Main Content */}
          <main className="app-page-content min-w-0 flex-1">
            {children}
          </main>
          <SiteFooter className="mt-8" />
        </div>
      </div>
      
      {showMobileNav ? <MobileNav /> : null}
    </div>
  );
};

export default AppLayout;
