import { MobileNav, DuolingoSidebar } from "@/shared/components/navigation";

const AppLayout = ({ children, showMobileNav = true }) => {
  return (
    <div className="app-page-shell min-h-[100dvh] font-sans antialiased text-[var(--page-fg)]">
      {/* Sidebar - Desktop only */}
      <DuolingoSidebar />
      
      {/* Content Area */}
      <div className="flex flex-col lg:pl-[256px]">
        <div className="mx-auto w-full max-w-[1056px] px-4 md:px-6">
          <main className="min-w-0 pb-28 pt-8 md:pb-14">
            {children}
          </main>
        </div>
      </div>
      
      {showMobileNav ? <MobileNav /> : null}
    </div>
  );
};

export default AppLayout;
