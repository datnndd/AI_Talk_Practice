import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

const LandingHero = () => {
  const navigate = useNavigate();

  return (
    <main className="max-w-7xl mx-auto px-6 lg:px-12 pt-12 pb-24 flex flex-col md:flex-row items-center justify-center gap-12 lg:gap-24">
      {/* Hero Illustration Column */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="flex-1 flex justify-center items-center"
      >
        <img 
          alt="SpeakEasy AI Robot and Students Illustration" 
          className="w-full max-w-lg object-contain drop-shadow-2xl" 
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuCpiUf0AyLa-PMnRkPUBWhO1TdAp2zeF1odcsgzLVQpvyFQCGJVwkLMSfImNdDMPLdFWLz5_sD1-Ios9rAOAjADOfdqahdJ8KAaiQaqgCcLRRlFOQ2UWevIAY556EUpLH1_fIhDhByhFepp-pFsgjpSaqncufhIzEalB3Y-R7rpL5KF_Omkyr3x022nAlIwBcJHyOjiJ37w1hp3d2kAtdsltuFFQ5MhgAqurHtMP02kbOcj-2Kub4gBW5qfyY-HBzcyuP_9-hZhQplc"
        />
      </motion.div>

      {/* Hero Text and CTA Column */}
      <div className="flex-1 text-center md:text-left flex flex-col items-center md:items-start text-balance">
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-4xl lg:text-5xl font-bold text-duo-text leading-tight mb-10 max-w-md font-display"
        >
          The free, fun, and effective way to practice speaking!
        </motion.h1>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="w-full max-w-sm space-y-4"
        >
          {/* Primary Call to Action */}
          <button 
            onClick={() => navigate("/register")}
            className="w-full bg-duo-green hover:bg-[#61da04] text-white font-bold py-4 rounded-xl shadow-[0_4px_0_#2ba300] active:shadow-none active:translate-y-[2px] transition-all uppercase tracking-wide text-sm font-sans"
          >
            Get Started
          </button>

          {/* Secondary Call to Action */}
          <button 
            onClick={() => navigate("/login")}
            className="w-full bg-white hover:bg-gray-50 text-duo-text border-2 border-duo-gray font-bold py-4 rounded-xl shadow-[0_4px_0_#e5e5e5] active:shadow-none active:translate-y-[2px] transition-all uppercase tracking-wide text-sm font-sans"
          >
            I already have an account
          </button>
        </motion.div>
      </div>
    </main>
  );
};

export default LandingHero;
