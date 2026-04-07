import { MobileNav, TopBar } from "@/shared/components/navigation";

const AppLayout = ({ children, showMobileNav = true }) => {
  return (
    <div className="app-page-shell min-h-[100dvh] font-sans antialiased text-[var(--page-fg)]">
      <TopBar />
      <div className="mx-auto w-full max-w-[1600px] px-4 md:px-6">
        <main className="min-w-0 pb-28 pt-[104px] md:pb-14">
          {children}
        </main>
      </div>
      {showMobileNav ? <MobileNav /> : null}
    </div>
  );
};

export default AppLayout;
