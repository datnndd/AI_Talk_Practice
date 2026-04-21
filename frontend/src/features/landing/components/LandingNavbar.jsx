import { CaretDown } from "@phosphor-icons/react";
import BrandMark from "@/shared/components/navigation/BrandMark";

const LandingNavbar = () => {
  return (
    <header className="max-w-7xl mx-auto px-6 lg:px-12 py-6 flex justify-between items-center bg-transparent">
      <BrandMark />
      
      {/* Language Selector */}
      <div className="hidden md:flex items-center space-x-1 text-sm font-bold text-duo-header-text uppercase tracking-wider cursor-pointer hover:text-duo-text transition-colors">
        <span>Site Language: English</span>
        <CaretDown weight="bold" className="w-4 h-4" />
      </div>
    </header>
  );
};

export default LandingNavbar;
