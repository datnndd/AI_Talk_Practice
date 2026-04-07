import { Translate } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

const BrandMark = ({ to = "/", eyebrow, compact = false }) => {
  return (
    <Link to={to} className="group inline-flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20 transition duration-300 group-hover:-translate-y-0.5 group-hover:scale-[1.03]">
        <Translate weight="fill" size={compact ? 18 : 20} />
      </div>
      <div className="min-w-0">
        {eyebrow ? (
          <p className="text-[10px] font-black uppercase tracking-[0.24em] text-primary/80">{eyebrow}</p>
        ) : null}
        <p className="font-display text-lg font-black tracking-tight text-[var(--nav-text)]">
          Lingo<span className="text-primary">AI</span>
        </p>
      </div>
    </Link>
  );
};

export default BrandMark;
