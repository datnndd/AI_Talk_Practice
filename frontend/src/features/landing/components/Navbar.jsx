import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BrandMark, publicNavItems } from "@/shared/components/navigation";

const Navbar = () => {
  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.1 }}
      className="fixed inset-x-0 top-0 z-50"
    >
      <div className="mx-auto max-w-7xl px-4 pt-4 md:px-6">
        <div className="liquid-glass refraction flex h-[76px] items-center justify-between rounded-[30px] px-4 md:px-5">
          <BrandMark eyebrow="Speak With Confidence" />

          <div className="hidden md:flex items-center gap-3 text-sm font-semibold text-zinc-500">
          {publicNavItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 transition hover:bg-white/70 hover:text-primary"
            >
              {item.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Link 
            to="/login" 
            className="rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] text-zinc-600 transition hover:bg-white/70 hover:text-primary"
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
              className="relative overflow-hidden rounded-2xl bg-primary px-6 py-3 text-xs font-black uppercase tracking-[0.18em] text-white shadow-lg shadow-primary/25 transition-all group"
            >
              <span className="relative z-10">Start Practicing</span>
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:animate-shimmer" />
            </motion.button>
          </Link>
        </div>
      </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
