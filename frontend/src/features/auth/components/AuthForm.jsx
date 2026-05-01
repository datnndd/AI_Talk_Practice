import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { EnvelopeSimple, LockSimple, ArrowRight, GoogleLogo } from "@phosphor-icons/react";
import { useGoogleLogin } from "@react-oauth/google";
import { BrandMark } from "@/shared/components/navigation";

const resolvePostLoginPath = (user) => {
  if (user?.is_admin) {
    return "/admin/scenarios";
  }

  return user?.is_onboarding_completed ? "/dashboard" : "/onboarding";
};

const AuthForm = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, googleLogin, refreshUser } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (tokenResponse) => {
    setIsLoading(true);
    setError("");
    try {
      // The tokenResponse contains an access_token that we can exchange or use.
      // But usually we want the id_token if we used the implicit flow or code if we use the auth code flow.
      // @react-oauth/google's useGoogleLogin by default returns an access_token.
      // However, our backend /auth/google expects an id_token or similar.
      // For simplicity and standard practice with @react-oauth/google, we can use the credential from GoogleLogin component 
      // OR use fetch to get user info if only access_token is provided.
      // Let's assume we want to use the standard GoogleLogin component or useGoogleLogin with the right flow.
      
      // If using useGoogleLogin (implicit flow), we get an access_token.
      // We'll send it to the backend which will verify it with Google's tokeninfo API.
      await googleLogin(tokenResponse.access_token);
      const user = await refreshUser();
      navigate(resolvePostLoginPath(user), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Google authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError("Google login failed"),
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await login(email, password);
      const user = await refreshUser();
      navigate(resolvePostLoginPath(user), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password");
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
            Welcome back
          </h2>
          <p className="text-zinc-500 font-medium text-sm">Please enter your details to sign in.</p>
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
            <span className="px-6 bg-white text-zinc-400 font-black uppercase tracking-[0.2em]">or sign in with email</span>
          </div>
        </div>

        {/* Login Form */}
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
            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="email">Email Address</label>
            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-indigo-500 transition-colors">
                <EnvelopeSimple weight="bold" size={18} />
              </div>
              <input 
                className="w-full pl-14 pr-6 py-4 bg-zinc-50 border border-transparent rounded-[1.5rem] focus:bg-white focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="email" 
                name="email" 
                placeholder="jane@example.com" 
                required 
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center ml-1">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block" htmlFor="password">Password</label>
              <a className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline underline-offset-2" href="#">Forgot?</a>
            </div>
            <div className="relative group">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-indigo-500 transition-colors">
                <LockSimple weight="bold" size={18} />
              </div>
              <input 
                className="w-full pl-14 pr-6 py-4 bg-zinc-50 border border-transparent rounded-[1.5rem] focus:bg-white focus:ring-2 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="password" 
                name="password" 
                placeholder="••••••••" 
                required 
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="pt-4">
            <motion.button
              whileHover={{ scale: 1.01, y: -2 }}
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
              className={`w-full bg-indigo-600 text-white font-black py-5 rounded-[1.5rem] shadow-xl shadow-indigo-500/20 transition-all flex items-center justify-center gap-3 text-xs uppercase tracking-[0.2em] group ${isLoading ? "opacity-70 cursor-not-allowed" : ""}`}
              type="submit"
            >
              {isLoading ? "Signing in..." : (
                <>
                  Sign In
                  <ArrowRight weight="bold" size={16} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </motion.button>
          </div>
        </form>

        <footer className="mt-12 text-center space-y-10">
          <p className="text-zinc-500 font-bold text-xs uppercase tracking-widest">
            Don't have an account? 
            <Link className="text-indigo-600 font-black ml-2 hover:underline underline-offset-4" to="/register">Create account</Link>
          </p>
          
          <div className="flex justify-center gap-8 border-t border-zinc-100 pt-10">
            <a className="text-[9px] font-black text-zinc-400 uppercase tracking-widest hover:text-indigo-600 transition-colors" href="/privacy">Privacy Policy</a>
            <a className="text-[9px] font-black text-zinc-400 uppercase tracking-widest hover:text-indigo-600 transition-colors" href="/terms">Terms of Service</a>
          </div>
        </footer>
      </motion.div>
    </section>
  );
};

export default AuthForm;
