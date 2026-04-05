import Navbar from "@/features/landing/components/Navbar";
import Hero from "@/features/landing/components/Hero";
import BentoGrid from "@/features/landing/components/BentoGrid";
import Testimonials from "@/features/landing/components/Testimonials";
import CTA from "@/features/landing/components/CTA";
import Footer from "@/features/landing/components/Footer";

const LandingPage = () => {
  return (
    <div className="min-h-[100dvh] bg-[#f9fafb]">
      <Navbar />
      <Hero />
      <BentoGrid />
      <Testimonials />
      <CTA />
      <Footer />
    </div>
  );
};

export default LandingPage;
