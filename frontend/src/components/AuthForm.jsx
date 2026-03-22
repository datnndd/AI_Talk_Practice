import { motion } from "framer-motion";
import { GoogleLogo } from "@phosphor-icons/react";

const AuthForm = () => {
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

          <form className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest block ml-1" htmlFor="email">Email Address</label>
              <input 
                className="w-full px-6 py-4 bg-zinc-50 border-none rounded-2xl focus:ring-2 focus:ring-primary/20 transition-all outline-none text-zinc-950 font-bold text-sm placeholder:text-zinc-300" 
                id="email" 
                name="email" 
                placeholder="name@company.com" 
                required 
                type="email"
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
              />
            </div>
            
            <motion.button
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="w-full bg-primary text-white font-black py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all btn-spring text-sm uppercase tracking-widest"
              type="submit"
            >
              Sign in to Account
            </motion.button>
          </form>

          <p className="text-center text-xs font-bold text-zinc-400">
            Don't have an account? 
            <a className="text-primary font-black ml-2 hover:underline" href="#">Start free trial</a>
          </p>
        </motion.div>
      </div>

      <footer className="p-10 border-t border-zinc-50">
        <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-[10px] font-black text-zinc-300 uppercase tracking-widest">
          <a className="hover:text-zinc-500 transition-colors" href="#">Privacy</a>
          <a className="hover:text-zinc-500 transition-colors" href="#">Terms</a>
          <a className="hover:text-zinc-500 transition-colors" href="#">Help</a>
          <span className="text-zinc-200">© 2024 LingoFlow</span>
        </div>
      </footer>
    </section>
  );
};

export default AuthForm;
