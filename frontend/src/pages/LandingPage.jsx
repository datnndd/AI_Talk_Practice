import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import BentoGrid from "../components/BentoGrid";
import Testimonials from "../components/Testimonials";
import CTA from "../components/CTA";
import Footer from "../components/Footer";

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
