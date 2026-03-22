import { motion, useScroll, useTransform } from "framer-motion";
import { Translate, List, X } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
      className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-zinc-100"
    >
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center text-white transition-transform group-hover:scale-110">
            <Translate weight="fill" size={24} />
          </div>
          <span className="text-xl font-bold tracking-tight font-display">LingoAI</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-600">
          {["Methodology", "Features", "Pricing"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="hover:text-primary transition-colors relative group"
            >
              {item}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full" />
            </a>
          ))}
        </div>

        <div className="flex items-center gap-8">
            <Link to="/login" className="text-sm font-black text-zinc-500 hover:text-primary transition-colors uppercase tracking-widest">
              Login
            </Link>
            <Link to="/dashboard">
              <motion.button
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className="bg-primary text-white border border-primary px-8 py-3.5 rounded-full font-black text-[10px] uppercase tracking-[0.2em] shadow-xl shadow-primary/20 transition-all btn-spring"
              >
                Get Started
              </motion.button>
            </Link>
          </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
