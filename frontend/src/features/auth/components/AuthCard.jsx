import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useGoogleLogin } from "@react-oauth/google";
import { motion } from "framer-motion";
import { Eye, EyeSlash } from "@phosphor-icons/react";

const AuthCard = ({ mode = "register" }) => {
  const isLogin = mode === "login";
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, register, googleLogin, refreshUser } = useAuth();
  const navigate = useNavigate();

  const resolvePostLoginPath = (user) => {
    if (user?.is_admin) return "/admin/scenarios";
    return user?.is_onboarding_completed ? "/dashboard" : "/onboarding";
  };

  const handleGoogleSuccess = async (tokenResponse) => {
    setIsLoading(true);
    setError("");
    try {
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

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData);
      }
      const user = await refreshUser();
      navigate(resolvePostLoginPath(user), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || (isLogin ? "Invalid email or password" : "Registration failed"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full flex justify-center py-24 px-4 bg-white min-h-screen">
      <div className="w-full max-w-[420px] bg-white rounded-[20px] p-8 flex flex-col items-center border-2 border-brand-gray shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
        <h1 className="font-display text-[#3c3c3c] mb-8 text-[32px] font-black tracking-tight">
          {isLogin ? "Sign in" : "Create your profile"}
        </h1>

        <form onSubmit={handleSubmit} className="w-full space-y-3">
          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 bg-rose-50 text-rose-600 rounded-xl text-xs font-bold border border-rose-100 uppercase tracking-wider text-center"
            >
              {error}
            </motion.div>
          )}

          {!isLogin && (
            <div className="relative">
              <input 
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-4 rounded-xl bg-[#f7f7f7] border-2 border-brand-gray font-semibold text-brand-text placeholder-brand-muted focus:outline-none focus:border-brand-blue focus:bg-white transition-all" 
                placeholder="Name (optional)" 
                type="text"
              />
            </div>
          )}

          <div className="relative">
            <input 
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-4 rounded-xl bg-[#f7f7f7] border-2 border-brand-gray font-semibold text-brand-text placeholder-brand-muted focus:outline-none focus:border-brand-blue focus:bg-white transition-all" 
              placeholder="Email" 
              type="email"
            />
          </div>

          <div className="relative">
            <input 
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-4 rounded-xl bg-[#f7f7f7] border-2 border-brand-gray font-semibold text-brand-text placeholder-brand-muted focus:outline-none focus:border-brand-blue focus:bg-white transition-all" 
              placeholder="Password" 
              type={showPassword ? "text" : "password"}
            />
            <button 
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-brand-blue hover:text-brand-blue-dark transition-colors"
            >
              {showPassword ? <EyeSlash size={24} weight="bold" /> : <Eye size={24} weight="bold" />}
            </button>
          </div>

          <div className="pt-2">
            <button 
              disabled={isLoading}
              className={`bg-brand-blue hover:bg-[#1899d6] w-full py-4 rounded-xl text-white font-display font-black text-sm tracking-widest uppercase shadow-[0_4px_0_0_#1899d6] active:shadow-none active:translate-y-[4px] transition-all ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
              type="submit"
            >
              {isLoading ? (isLogin ? "Signing in..." : "Creating...") : (isLogin ? "Sign In" : "Create Account")}
            </button>
          </div>
        </form>

        <div className="w-full flex items-center my-8">
          <div className="flex-grow h-[2px] bg-brand-gray"></div>
          <span className="px-4 text-brand-muted font-black text-sm tracking-widest">OR</span>
          <div className="flex-grow h-[2px] bg-brand-gray"></div>
        </div>

        <div className="w-full flex gap-4 mb-8">
          <button 
            type="button"
            onClick={() => signInWithGoogle()}
            className="flex-1 flex items-center justify-center gap-3 py-3 border-2 border-brand-gray rounded-xl font-bold text-brand-text text-xs uppercase tracking-wider shadow-[0_2px_0_0_#e5e5e5] active:shadow-none active:translate-y-[2px] transition-all hover:bg-gray-50"
          >
            <img alt="Google" className="w-5 h-5" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBzHlwsf4boccvAWE3xeOv75XLy9eHnaVM6TgW_KvidApYRKsHrhcyTpxUEzoazwVvK9nZgMDo6SbKe0deJ9716nErkJZwbe4H_zWkAk6orbeyaX4m6bEdB3qUWrFg_hwPLbYZIM4Jr-Mw9IIaiITn6IGwJTpJF-CAVi9Czv3PWzGWdc6vSbw3NKXXmEYdRmgC3MYmpWzNSMxW7Zj8rNV3tkuJCAmb5C-OOM7QLfo3RXZ6entNMNfEjkZlCA1KNhenlaFbkUmTudrFZ"/>
            Google
          </button>
          <button 
            type="button"
            className="flex-1 flex items-center justify-center gap-3 py-3 border-2 border-brand-gray rounded-xl font-bold text-brand-text text-xs uppercase tracking-wider shadow-[0_2px_0_0_#e5e5e5] active:shadow-none active:translate-y-[2px] transition-all hover:bg-gray-50"
          >
            <img alt="Facebook" className="w-5 h-5" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBcP858G6fXy_qSzjrwUnq51ItaGkn0SbxrOF-XUSdZ6UNnqNPoFbdpmx4Ti9Kof1SEnLjFsAuQ5X0F0uqGRFcUrWAbeWZNrM9cdJGrENtegeshBlXcxhs2cimzZkqZ-gInyit3CrIG_ZGY0qZvXVn0CGtdlT_46Ly4alEstNsiDtOJGi8ZMAfhiZOp75QG5fdwYgposoiirXSfl8X0D4XAGvDdaO_S3Aq4r0__W6JRDC3XgzXv2DvBmbQCM0C6o1YhiUK6JWuqL3dj"/>
            Facebook
          </button>
        </div>

        <footer className="text-center text-[12px] leading-relaxed text-brand-muted font-bold">
          <p className="mb-4 px-2">
            By signing {isLogin ? "in" : "up"} to SpeakEasy AI, you agree to our 
            <a className="text-brand-blue hover:underline mx-1" href="#">Terms</a> and 
            <a className="text-brand-blue hover:underline mx-1" href="#">Privacy Policy</a>.
          </p>
          <p>
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <Link 
              className="text-brand-blue hover:underline ml-2 uppercase tracking-wider" 
              to={isLogin ? "/register" : "/login"}
            >
              {isLogin ? "Create account" : "Sign in"}
            </Link>
          </p>
        </footer>
      </div>
    </div>
  );
};

export default AuthCard;
