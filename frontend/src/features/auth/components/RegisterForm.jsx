import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { EnvelopeSimple, LockSimple, ArrowRight, GoogleLogo, Sparkle } from "@phosphor-icons/react";
import { useGoogleLogin } from "@react-oauth/google";
import { BrandMark } from "@/shared/components/navigation";

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { register, googleLogin } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (tokenResponse) => {
    setIsLoading(true);
    setError("");
    try {
      const userData = await googleLogin(tokenResponse.access_token);
      if (userData.is_onboarding_completed) {
        navigate("/dashboard");
      } else {
        navigate("/onboarding");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Google registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError("Google registration failed"),
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    
    try {
      const userData = await register(formData);
      if (userData.is_onboarding_completed) {
        navigate("/dashboard");
      } else {
        navigate("/onboarding");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="w-full lg:w-5/12 bg-white flex flex-col justify-center px-8 sm:px-12 lg:px-24 py-12 min-h-[100dvh] overflow-y-auto">
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
        className="max-w-md w-full mx-auto"
      >
        <div className="mb-12 lg:hidden">
          <BrandMark />
        </div>

        <header className="mb-10 text-left">
          <h2 className="text-4xl font-black text-zinc-950 mb-3 tracking-tighter leading-none font-display">
            Create your account
          </h2>
          <p className="text-zinc-500 font-medium text-sm">Join the flow and start your journey today.</p>
        </header>

        {/* Social Auth */}
        <motion.button 
          whileHover={{ scale: 1.01, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => signInWithGoogle()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 px-6 py-4 border border-zinc-200 rounded-2xl text-zinc-950 font-black text-xs uppercase tracking-widest hover:bg-zinc-50 hover:border-zinc-300 transition-all shadow-sm"
        >
          <GoogleLogo weight="bold" size={20} className="text-red-500" />
          {isLoading ? "Connecting..." : "Continue with Google"}
        </motion.button>

        <div className="relative my-10">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-100"></div>
          </div>
          <div className="relative flex justify-center text-[10px]">
            <span className="px-6 bg-white text-zinc-400 font-black uppercase tracking-[0.2em]">Register with Email</span>
          </div>
        </div>

        {/* Registration Form */}
        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 bg-rose-50 text-rose-600 rounded-2xl text-xs font-black border border-rose-100 uppercase tracking-widest"
            >
              {error}
            </motion.div>
          )}

          <div className="space-y-2">
            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1">Email Address</label>
            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-indigo-500 transition-colors">
                <EnvelopeSimple weight="bold" size={18} />
              </div>
              <input 
                className="w-full pl-14 pr-6 py-4 bg-zinc-50 border border-transparent rounded-[1.5rem] focus:bg-white focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="email" name="email" placeholder="jane@example.com" required type="email"
                value={formData.email} onChange={handleChange}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1">Password</label>
            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-indigo-500 transition-colors">
                <LockSimple weight="bold" size={18} />
              </div>
              <input 
                className="w-full pl-14 pr-6 py-4 bg-zinc-50 border border-transparent rounded-[1.5rem] focus:bg-white focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="password" name="password" placeholder="••••••••" required type="password"
                value={formData.password} onChange={handleChange}
              />
            </div>
            {formData.password && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mt-3 px-1"
              >
                <div className="flex gap-1.5 h-1">
                  <div className="flex-1 bg-indigo-500 rounded-full"></div>
                  <div className="flex-1 bg-indigo-500 rounded-full"></div>
                  <div className={`flex-1 ${formData.password.length > 8 ? "bg-indigo-500" : "bg-zinc-100"} rounded-full`}></div>
                  <div className={`flex-1 ${formData.password.length > 12 ? "bg-indigo-500" : "bg-zinc-100"} rounded-full`}></div>
                </div>
                <p className="mt-2 text-[10px] text-zinc-400 font-bold uppercase tracking-widest">
                  Strength: <span className="text-indigo-600">Dynamic</span>
                </p>
              </motion.div>
            )}
          </div>

          <div className="pt-4">
            <motion.button
              whileHover={{ scale: 1.01, y: -2 }}
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
              className={`w-full bg-indigo-600 text-white font-black py-5 rounded-[1.5rem] shadow-xl shadow-indigo-500/20 transition-all flex items-center justify-center gap-3 text-xs uppercase tracking-[0.2em] group ${isLoading ? "opacity-70 cursor-not-allowed" : ""}`}
              type="submit"
            >
              {isLoading ? "Creating..." : (
                <>
                  Create Account
                  <ArrowRight weight="bold" size={16} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </motion.button>
          </div>
        </form>

        <footer className="mt-12 text-center space-y-10">
          <p className="text-zinc-500 font-bold text-xs uppercase tracking-widest">
            Already have an account? 
            <Link className="text-indigo-600 font-black ml-2 hover:underline underline-offset-4" to="/login">Sign in</Link>
          </p>
          
          <div className="flex justify-center gap-8 border-t border-zinc-100 pt-10">
            <a className="text-[9px] font-black text-zinc-400 uppercase tracking-widest hover:text-indigo-600 transition-colors" href="#">Privacy Policy</a>
            <a className="text-[9px] font-black text-zinc-400 uppercase tracking-widest hover:text-indigo-600 transition-colors" href="#">Terms of Service</a>
          </div>
        </footer>
      </motion.div>

      {/* Floating Offer Toast */}
      <motion.div 
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 1, type: "spring", stiffness: 100, damping: 20 }}
        className="fixed bottom-8 right-8 hidden md:flex items-center gap-4 bg-white/80 backdrop-blur-xl px-6 py-4 rounded-[2rem] shadow-2xl border border-zinc-100/50 cursor-pointer hover:scale-105 transition-transform"
      >
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-600">
          <Sparkle weight="fill" size={20} />
        </div>
        <div>
          <p className="text-[10px] font-black text-zinc-950 uppercase tracking-widest">Get 1 week free</p>
          <p className="text-[9px] text-zinc-500 font-bold tracking-tight">Claim your starter bonus</p>
        </div>
      </motion.div>
    </section>
  );
};

export default RegisterForm;
