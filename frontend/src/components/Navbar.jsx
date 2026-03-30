import { motion } from "framer-motion";
import { Translate } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.1 }}
      className="fixed top-0 w-full z-50 liquid-glass backdrop-blur-xl border-b border-white/20"
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/20 transition-all duration-500 group-hover:rotate-12 group-hover:scale-110">
            <Translate weight="bold" size={22} />
          </div>
          <span className="text-2xl font-black tracking-tighter font-display text-zinc-900">
            Lingo<span className="text-primary">AI</span>
          </span>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-10 text-sm font-semibold text-zinc-500">
          {["Methodology", "Features", "Pricing"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="hover:text-primary transition-all duration-300 relative group py-2"
            >
              {item}
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full rounded-full" />
            </a>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-6">
          <Link 
            to="/login" 
            className="text-sm font-bold text-zinc-600 hover:text-primary transition-colors px-4 py-2 rounded-lg hover:bg-zinc-100/50"
          >
            Log In
          </Link>
          <Link to="/dashboard">
            <motion.button
              whileHover={{ 
                scale: 1.02,
                y: -1,
                boxShadow: "0 20px 40px -15px rgba(0, 90, 182, 0.3)"
              }}
              whileTap={{ scale: 0.98 }}
              className="bg-primary text-white px-7 py-3 rounded-2xl font-bold text-sm tracking-tight shadow-diffusion transition-all relative overflow-hidden group"
            >
              <span className="relative z-10">Get Started</span>
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:animate-shimmer" />
            </motion.button>
          </Link>
        </div>
      </div>
      {/* Refraction Line */}
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/10" />
    </motion.nav>
  );
};

export default Navbar;
