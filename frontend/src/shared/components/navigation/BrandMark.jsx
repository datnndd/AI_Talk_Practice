import { Link } from "react-router-dom";
import logo from "@/assets/buddy_talk_logo.jpg";

const BrandMark = ({ to = "/", compact = false, eyebrow = null, className = "" }) => {
  return (
    <Link to={to} className={`group inline-flex items-center gap-3 ${className}`}>
      <div className={`flex items-center transition duration-300 group-hover:scale-[1.03] ${compact ? 'scale-75 origin-left' : ''}`}>
        <img 
          src={logo} 
          alt="Buddy Talk Logo" 
          className="h-9 w-auto object-contain" 
        />
        
        {!compact && (
          <div className="ml-2 flex flex-col justify-center">
            {eyebrow && (
              <p className="mb-0.5 text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/60 transition-colors">
                {eyebrow}
              </p>
            )}
            <div className="flex items-center text-2xl font-black tracking-tighter leading-none">
              <p className="text-foreground transition-colors">
                Buddy
              </p>
              <p className="ml-1 text-brand-green transition-colors">
                Talk
              </p>
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default BrandMark;
