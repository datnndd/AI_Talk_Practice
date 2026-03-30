import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ArrowRight, ArrowArcLeft, Question, X } from "@phosphor-icons/react";

import GoalStep from "../components/onboarding/GoalStep";
import LevelStep from "../components/onboarding/LevelStep";
import InterestsStep from "../components/onboarding/InterestsStep";
import FinalStep from "../components/onboarding/FinalStep";

const OnboardingPage = () => {
  const { onboard } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    display_name: "",
    native_language: "vi",
    avatar: "user1",
    age: "",
    level: "intermediate", // Default to recommended
    learning_purpose: "",
    main_challenge: "",
    favorite_topics: "",
    daily_goal: 15,
  });

  const updateData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = async () => {
    if (step < 3) {
      setStep(prev => prev + 1);
    } else {
      await finishOnboarding();
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(prev => prev - 1);
  };

  const finishOnboarding = async () => {
    setIsSubmitting(true);
    try {
      await onboard(formData);
      navigate("/topics");
    } catch (err) {
      console.error(err);
      setIsSubmitting(false);
      alert("Something went wrong during onboarding. Please try again.");
    }
  };

  const isNextDisabled = () => {
    switch (step) {
      case 0: return !formData.learning_purpose;
      case 1: return !formData.level;
      case 2: return formData.favorite_topics.length === 0;
      case 3: 
        return !formData.display_name.trim() || !formData.age || !formData.main_challenge.trim();
      default: return false;
    }
  };

  // Liquid Swipe Transition
  const pageVariants = {
    initial: { opacity: 0, x: 50, filter: "blur(4px)" },
    animate: { 
      opacity: 1, 
      x: 0, 
      filter: "blur(0px)",
      transition: { type: "spring", stiffness: 100, damping: 20 }
    },
    exit: { 
      opacity: 0, 
      x: -50, 
      filter: "blur(4px)",
      transition: { type: "spring", stiffness: 100, damping: 20 }
    }
  };

  return (
    <div className="min-h-screen bg-background font-body text-on-background selection:bg-primary-fixed selection:text-on-primary-fixed overflow-x-hidden flex flex-col">
      {/* Navbar */}
      <header className="bg-[#f9f9fc]/90 dark:bg-slate-950/90 backdrop-blur-md fixed top-0 left-0 w-full z-40 transition-colors duration-300">
        <nav className="flex justify-between items-center w-full px-6 py-4 max-w-7xl mx-auto">
          <div className="text-xl font-extrabold text-primary dark:text-blue-400 tracking-tighter font-display">
            LingoFlow
          </div>
          <div className="flex gap-4">
            <button className="text-slate-500 dark:text-slate-400 hover:text-primary transition-colors btn-spring">
              <Question size={24} weight="regular" />
            </button>
            <button className="text-slate-500 dark:text-slate-400 hover:text-primary transition-colors btn-spring">
              <X size={24} weight="regular" />
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-grow pt-24 pb-32 flex flex-col items-center w-full relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full flex justify-center"
          >
            {step === 0 && <GoalStep formData={formData} updateData={updateData} />}
            {step === 1 && <LevelStep formData={formData} updateData={updateData} />}
            {step === 2 && <InterestsStep formData={formData} updateData={updateData} />}
            {step === 3 && <FinalStep formData={formData} updateData={updateData} />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer / Navigation */}
      <footer className="fixed bottom-0 left-0 w-full z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-[0_-10px_30px_rgba(0,0,0,0.03)] flex justify-between items-center px-8 py-6 mb-safe">
        <button 
          onClick={handleBack}
          disabled={step === 0}
          className={`px-6 py-3 font-body font-medium text-sm hover:opacity-90 transition-opacity flex items-center gap-2 btn-spring ${step === 0 ? 'opacity-0 pointer-events-none' : 'text-slate-500 dark:text-slate-400'}`}
        >
          <ArrowArcLeft size={18} />
          Back
        </button>
        <button 
          onClick={handleNext}
          disabled={isNextDisabled() || isSubmitting}
          className="bg-tertiary-fixed border border-transparent hover:border-[#a16900]/20 text-tertiary disabled:opacity-50 disabled:cursor-not-allowed rounded-xl px-10 py-4 font-bold font-body text-sm shadow-diffusion hover:shadow-lg transition-all btn-spring flex items-center gap-3"
        >
          {isSubmitting ? "Processing..." : step === 3 ? "Complete" : "Continue"}
          {!isSubmitting && <ArrowRight size={20} weight="bold" />}
        </button>
      </footer>
    </div>
  );
};

export default OnboardingPage;
