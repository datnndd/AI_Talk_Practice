import LandingNavbar from "@/features/landing/components/LandingNavbar";
import LandingHero from "@/features/landing/components/LandingHero";
import LandingLanguageFooter from "@/features/landing/components/LandingLanguageFooter";

const LandingPage = () => {
  return (
    <div className="min-h-screen flex flex-col bg-white overflow-x-hidden selection:bg-duo-green/10 selection:text-duo-green-dark">
      <LandingNavbar />
      <div className="flex-grow flex flex-col justify-center">
        <LandingHero />
      </div>
      <LandingLanguageFooter />
    </div>
  );
};

export default LandingPage;
