import { motion } from "framer-motion";
import { Sun, Moon } from "@phosphor-icons/react";
import { useState } from "react";

const ThemeSelector = () => {
  const [theme, setTheme] = useState("light");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="md:col-span-6 bg-white border border-zinc-200 rounded-[2.5rem] p-8 shadow-sm flex flex-col justify-between hover:shadow-xl transition-all duration-300"
    >
      <div>
        <h3 className="font-bold text-lg text-zinc-950 font-display mb-2">Appearance</h3>
        <p className="text-xs text-zinc-400 font-bold uppercase tracking-widest">Choose your theme</p>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mt-8">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setTheme("light")}
          className={`flex items-center justify-center gap-3 p-5 rounded-3xl border-2 transition-all ${
            theme === "light" 
              ? "border-primary bg-primary/5 text-primary" 
              : "border-transparent bg-zinc-50 text-zinc-400 hover:bg-zinc-100"
          }`}
        >
          <Sun weight={theme === "light" ? "fill" : "bold"} size={24} />
          <span className="font-black text-xs uppercase tracking-widest">Light</span>
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setTheme("dark")}
          className={`flex items-center justify-center gap-3 p-5 rounded-3xl border-2 transition-all ${
            theme === "dark" 
              ? "border-primary bg-primary/5 text-primary" 
              : "border-transparent bg-zinc-50 text-zinc-400 hover:bg-zinc-100"
          }`}
        >
          <Moon weight={theme === "dark" ? "fill" : "bold"} size={24} />
          <span className="font-black text-xs uppercase tracking-widest">Dark</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default ThemeSelector;
