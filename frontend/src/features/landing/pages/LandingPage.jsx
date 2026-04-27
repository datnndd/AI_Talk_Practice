import LandingNavbar from "@/features/landing/components/LandingNavbar";
import LandingHero from "@/features/landing/components/LandingHero";
import FutureVoicePreview from "@/features/landing/components/FutureVoicePreview";
import LandingLanguageFooter from "@/features/landing/components/LandingLanguageFooter";

const LandingPage = () => {
  return (
    <div className="min-h-screen flex flex-col bg-white overflow-x-hidden selection:bg-brand-green/10 selection:text-brand-green-dark">
      <LandingNavbar />
      <div className="flex-grow flex flex-col justify-center">
        <LandingHero />
      </div>
      <FutureVoicePreview />
      <LandingLanguageFooter />
    </div>
  );
};

export default LandingPage;
