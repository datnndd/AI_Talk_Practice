import { motion } from "framer-motion";
import { Translate, TwitterLogo, InstagramLogo, LinkedinLogo } from "@phosphor-icons/react";

const Footer = () => {
  return (
    <footer className="bg-white border-t border-zinc-100 pt-32 pb-16">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-start gap-16 mb-24">
          <div className="max-w-sm space-y-6">
            <div className="flex items-center gap-3 group cursor-pointer w-fit">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white transition-transform group-hover:scale-110 group-hover:rotate-6">
                <Translate weight="bold" size={18} />
              </div>
              <span className="text-2xl font-black font-display tracking-tighter text-zinc-900">LingoAI</span>
            </div>
            <p className="text-zinc-500 text-sm font-medium leading-relaxed">
              The world's most advanced AI speaking companion. Mastering new languages through natural, unscripted immersion.
            </p>
            <div className="flex gap-4 pt-2">
              {[TwitterLogo, InstagramLogo, LinkedinLogo].map((Icon, i) => (
                <motion.a
                  key={i}
                  href="#"
                  whileHover={{ y: -3, color: "var(--color-primary)" }}
                  className="text-zinc-400 transition-colors"
                >
                  <Icon weight="bold" size={20} />
                </motion.a>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-16 md:gap-24">
            <div className="space-y-6">
              <h5 className="font-black text-zinc-900 uppercase text-[10px] tracking-[0.2em]">Product</h5>
              <ul className="space-y-4 text-zinc-500 text-sm font-bold">
                {["Methodology", "Features", "Pricing", "Demo"].map((item) => (
                  <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
                ))}
              </ul>
            </div>

            <div className="space-y-6">
              <h5 className="font-black text-zinc-900 uppercase text-[10px] tracking-[0.2em]">Company</h5>
              <ul className="space-y-4 text-zinc-500 text-sm font-bold">
                {["About", "Blog", "Careers", "Contact"].map((item) => (
                  <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
                ))}
              </ul>
            </div>

            <div className="space-y-6">
              <h5 className="font-black text-zinc-900 uppercase text-[10px] tracking-[0.2em]">Legal</h5>
              <ul className="space-y-4 text-zinc-500 text-sm font-bold">
                {["Privacy", "Terms", "Policies"].map((item) => (
                  <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-zinc-100 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-zinc-400 text-[11px] font-black uppercase tracking-widest">
            © {new Date().getFullYear()} LingoAI Inc. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-zinc-400 text-[11px] font-black uppercase tracking-widest">
            <a href="#" className="hover:text-zinc-600 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-zinc-600 transition-colors">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
