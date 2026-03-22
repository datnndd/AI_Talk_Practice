import { motion } from "framer-motion";
import { Robot, User, Sparkle } from "@phosphor-icons/react";
import CameraOverlay from "./CameraOverlay";

const Message = ({ char, content, isAI }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95, y: 10 }}
    whileInView={{ opacity: 1, scale: 1, y: 0 }}
    viewport={{ once: true }}
    className={`flex items-start gap-4 max-w-[85%] ${isAI ? "" : "flex-row-reverse ml-auto"}`}
  >
    <div className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center border ${
      isAI ? "bg-zinc-100 border-zinc-200 text-zinc-500" : "bg-primary/10 border-primary text-primary shadow-sm"
    }`}>
      {isAI ? <Robot size={22} /> : <User size={22} />}
    </div>
    
    <div className={`p-5 rounded-3xl shadow-sm border ${
      isAI 
        ? "bg-white/60 border-white/40 rounded-tl-none text-zinc-900" 
        : "bg-white border-primary/20 rounded-tr-none text-zinc-950 font-semibold"
    } relative overflow-hidden`}>
      {isAI && <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full -mr-12 -mt-12" />}
      <p className="text-sm leading-relaxed relative z-10">{content}</p>
    </div>
  </motion.div>
);

const ChatWindow = () => {
  const messages = [
    {
      isAI: true,
      content: "Bonjour ! I'm your language companion. Would you like to practice your French conversation skills today? We could discuss cuisine, travel, or literature."
    },
    {
      isAI: false,
      content: "Oui, j'aimerais parler de la cuisine française. Qu'est-ce que vous recommandez comme plat classique ?"
    },
    {
      isAI: true,
      content: "Excellent choice! For a classic dish, you can't go wrong with Boeuf Bourguignon. It's a rich beef stew braised in red wine. Have you ever tried making it?"
    }
  ];

  return (
    <section className="lg:col-span-8 flex flex-col liquid-glass rounded-4xl overflow-hidden h-full relative border border-white/20 shadow-2xl refraction">
      <CameraOverlay />
      
      <header className="px-8 py-5 border-b border-zinc-200/50 flex items-center justify-end">
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs font-bold text-zinc-950">Linguist AI</p>
            <div className="flex items-center justify-end gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Online</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/20 transition-transform hover:scale-105 active:scale-95">
            <Sparkle weight="fill" size={24} />
          </div>
        </div>
      </header>
      
      <div className="flex-1 overflow-y-auto p-10 space-y-8 scroll-hide pt-40">
        {messages.map((m, i) => (
          <Message key={i} {...m} />
        ))}
      </div>
    </section>
  );
};

export default ChatWindow;
