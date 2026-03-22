import { motion } from "framer-motion";
import { Translate, TwitterLogo, InstagramLogo, LinkedinLogo, Heart } from "@phosphor-icons/react";

const Footer = () => {
  return (
    <footer className="bg-zinc-50 border-t border-zinc-200 pt-20 pb-10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-16">
          <div className="col-span-2 lg:col-span-2">
            <div className="flex items-center gap-2 mb-6 group cursor-pointer w-fit">
              <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-white transition-transform group-hover:scale-110">
                <Translate weight="fill" size={20} />
              </div>
              <span className="text-lg font-bold font-display">LingoAI</span>
            </div>
            <p className="text-zinc-500 max-w-xs mb-8 font-medium">
              The world's most advanced AI-powered language immersion platform. Built for the modern learner.
            </p>
            <div className="flex gap-4">
              {[TwitterLogo, InstagramLogo, LinkedinLogo].map((Icon, i) => (
                <motion.a
                  key={i}
                  href="#"
                  whileHover={{ y: -3, color: "var(--color-primary)" }}
                  className="w-10 h-10 rounded-full border border-zinc-200 flex items-center justify-center text-zinc-400 transition-all hover:border-primary"
                >
                  <Icon size={20} />
                </motion.a>
              ))}
            </div>
          </div>

          <div>
            <h5 className="font-bold text-zinc-900 mb-6 uppercase text-[10px] tracking-widest">Product</h5>
            <ul className="space-y-4 text-zinc-500 text-sm font-medium">
              {["Tutor AI", "Curriculum", "Pricing", "Enterprise"].map((item) => (
                <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h5 className="font-bold text-zinc-900 mb-6 uppercase text-[10px] tracking-widest">Company</h5>
            <ul className="space-y-4 text-zinc-500 text-sm font-medium">
              {["About", "Blog", "Careers", "Contact"].map((item) => (
                <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h5 className="font-bold text-zinc-900 mb-6 uppercase text-[10px] tracking-widest">Legal</h5>
            <ul className="space-y-4 text-zinc-500 text-sm font-medium">
              {["Privacy", "Terms", "Cookies"].map((item) => (
                <li key={item}><a className="hover:text-primary transition-colors" href="#">{item}</a></li>
              ))}
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-zinc-200 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-zinc-400 text-sm font-medium">© {new Date().getFullYear()} LingoAI Inc. All rights reserved.</p>
          <p className="text-zinc-400 text-sm flex items-center gap-2 font-medium">
            Made with <Heart weight="fill" className="text-rose-400" /> for global citizens.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
