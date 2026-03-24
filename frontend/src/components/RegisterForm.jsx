import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    display_name: "",
    native_language: "vi",
    target_language: "en",
    level: "beginner"
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    
    try {
      await register(formData);
      navigate("/topics");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="w-full lg:w-2/5 flex flex-col bg-white relative">
      <div className="lg:hidden p-8">
        <span className="text-2xl font-black tracking-tighter text-primary font-display">LingoFlow</span>
      </div>

      <div className="flex-1 flex flex-col justify-center px-8 md:px-16 lg:px-20 py-12">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full mx-auto space-y-8"
        >
          <div className="space-y-3">
            <h2 className="text-4xl font-black text-zinc-950 tracking-tight font-display">Create Account</h2>
            <p className="text-zinc-500 font-bold text-xs uppercase tracking-widest">Join LingoFlow to practice speaking.</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-sm font-bold border border-red-100">
                {error}
              </div>
            )}
            
            <div className="space-y-2">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="display_name">Display Name</label>
              <input 
                className="w-full px-5 py-3 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="display_name" name="display_name" placeholder="John Doe" required type="text"
                value={formData.display_name} onChange={handleChange}
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="email">Email Address</label>
              <input 
                className="w-full px-5 py-3 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="email" name="email" placeholder="name@company.com" required type="email"
                value={formData.email} onChange={handleChange}
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="password">Password</label>
              <input 
                className="w-full px-5 py-3 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="password" name="password" placeholder="••••••••" required type="password"
                value={formData.password} onChange={handleChange}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="native_language">Native Language</label>
                <select 
                  className="w-full px-5 py-3 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm"
                  id="native_language" name="native_language" value={formData.native_language} onChange={handleChange}
                >
                  <option value="vi">Vietnamese</option>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="zh">Chinese</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="level">Skill Level</label>
                <select 
                  className="w-full px-5 py-3 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm"
                  id="level" name="level" value={formData.level} onChange={handleChange}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
              className={`w-full bg-primary text-white font-black py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all btn-spring text-sm uppercase tracking-widest mt-4 ${isLoading ? "opacity-70 cursor-not-allowed" : ""}`}
              type="submit"
            >
              {isLoading ? "Creating..." : "Sign Up"}
            </motion.button>
          </form>

          <p className="text-center text-xs font-bold text-zinc-400">
            Already have an account? 
            <Link className="text-primary font-black ml-2 hover:underline" to="/login">Sign in</Link>
          </p>
        </motion.div>
      </div>
    </section>
  );
};

export default RegisterForm;
