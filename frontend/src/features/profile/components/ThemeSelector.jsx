import { motion } from "framer-motion";
import { Moon, Sun } from "@phosphor-icons/react";

import { useTheme } from "@/shared/context/ThemeContext";

const ThemeOption = ({ icon: Icon, title, description, value, theme, onSelect }) => {
  const isActive = theme === value;

  return (
    <motion.button
      whileHover={{ scale: 1.01, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(value)}
      className={`rounded-[1.5rem] border p-4 text-left transition-all ${
        isActive
          ? "border-primary bg-primary/8 shadow-[0_20px_40px_-28px_rgba(0,90,182,0.42)]"
          : "border-[var(--panel-border)] bg-white/30 hover:bg-white/45"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-black text-[var(--page-fg)]">{title}</p>
          <p className="app-text-muted mt-1 text-sm leading-6">{description}</p>
        </div>
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-2xl ${
            isActive ? "bg-primary text-white" : "bg-[var(--chip-neutral-bg)] text-[var(--chip-neutral-text)]"
          }`}
        >
          <Icon size={18} weight={isActive ? "fill" : "bold"} />
        </div>
      </div>
    </motion.button>
  );
};

const ThemeSelector = () => {
  const { theme, setTheme, isDark } = useTheme();

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="app-panel rounded-[2rem] p-7"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">Appearance</p>
          <h3 className="mt-2 text-2xl font-black text-[var(--page-fg)]">Theme Mode</h3>
        </div>
        <div className="app-chip-neutral rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em]">
          {isDark ? "Dark active" : "Light active"}
        </div>
      </div>

      <div className="mt-6 rounded-[1.6rem] border border-[var(--panel-border)] bg-[linear-gradient(145deg,rgba(255,255,255,0.48),rgba(148,163,184,0.06))] p-4">
        <div className="grid gap-4">
          <ThemeOption
            icon={Sun}
            title="Light"
            description="Bright workspace with crisp cards and high daytime readability."
            value="light"
            theme={theme}
            onSelect={setTheme}
          />
          <ThemeOption
            icon={Moon}
            title="Dark"
            description="Low-glare evening mode with deeper panels and softer contrast."
            value="dark"
            theme={theme}
            onSelect={setTheme}
          />
        </div>
      </div>
    </motion.section>
  );
};

export default ThemeSelector;
