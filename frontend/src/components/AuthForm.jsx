import { useState } from "react";
import { motion } from "framer-motion";
import { GoogleLogo } from "@phosphor-icons/react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const AuthForm = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await login(email, password);
      // Wait a moment for auth state to update before navigation
      navigate("/topics");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="w-full lg:w-2/5 flex flex-col bg-white relative">
      {/* Mobile Header */}
      <div className="lg:hidden p-8">
        <span className="text-2xl font-black tracking-tighter text-primary font-display">LingoFlow</span>
      </div>

      <div className="flex-1 flex flex-col justify-center px-8 md:px-16 lg:px-20 py-12">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full mx-auto space-y-10"
        >
          <div className="space-y-3">
            <h2 className="text-4xl font-black text-zinc-950 tracking-tight font-display">Welcome back</h2>
            <p className="text-zinc-500 font-bold text-xs uppercase tracking-widest">Please enter your details to sign in.</p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full flex items-center justify-center space-x-3 px-6 py-4 border border-zinc-200 rounded-2xl hover:bg-zinc-50 active:bg-zinc-100 transition-all duration-200 group shadow-sm font-bold text-sm text-zinc-700"
          >
            <GoogleLogo size={22} weight="bold" className="text-zinc-900" />
            <span>Continue with Google</span>
          </motion.button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-100"></div>
            </div>
            <div className="relative flex justify-center text-[10px] uppercase font-black tracking-[0.3em]">
              <span className="bg-white px-6 text-zinc-300">or email</span>
            </div>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-sm font-bold border border-red-100">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="email">Email Address</label>
              <input 
                className="w-full px-6 py-4 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="email" 
                name="email" 
                placeholder="name@company.com" 
                required 
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block" htmlFor="password">Password</label>
                <a className="text-[10px] font-black text-primary uppercase tracking-widest hover:underline" href="#">Forgot password?</a>
              </div>
              <input 
                className="w-full px-6 py-4 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="password" 
                name="password" 
                placeholder="••••••••" 
                required 
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            
            <motion.button
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
              className={`w-full bg-primary text-white font-black py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all btn-spring text-sm uppercase tracking-widest ${isLoading ? "opacity-70 cursor-not-allowed" : ""}`}
              type="submit"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </motion.button>
          </form>

          <p className="text-center text-xs font-bold text-zinc-400">
            Don't have an account? 
            <Link className="text-primary font-black ml-2 hover:underline" to="/register">Create account</Link>
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default AuthForm;
