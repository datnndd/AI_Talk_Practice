import { Link } from "react-router-dom";
import { useSiteSettings } from "@/shared/hooks/useSiteSettings";

const BrandMark = ({ to = "/", compact = false, eyebrow = null, className = "" }) => {
  const settings = useSiteSettings();
  const brandWords = (settings.brandName || "Buddy Talk").trim().split(/\s+/);
  const firstWord = brandWords[0] || "Buddy";
  const restWords = brandWords.slice(1).join(" ") || "Talk";

  return (
    <Link to={to} className={`group inline-flex items-center gap-3 ${className}`}>
      <div className="flex items-center transition duration-300 group-hover:scale-[1.03]">
        <div className={`${compact ? "h-10 w-10" : "h-12 w-12"} flex shrink-0 items-center justify-center rounded-2xl border border-border bg-card p-1.5 shadow-sm`}>
          <img
            src={settings.logoUrl}
            alt={`${settings.brandName || "Buddy Talk"} Logo`}
            className="max-h-10 max-w-10 object-contain"
          />
        </div>
        
        {!compact && (
          <div className="ml-2 flex flex-col justify-center">
            {eyebrow && (
              <p className="mb-0.5 text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/60 transition-colors">
                {eyebrow}
              </p>
            )}
            <div className="flex items-center text-2xl font-black tracking-tighter leading-none">
              <p className="text-foreground transition-colors">
                {firstWord}
              </p>
              <p className="ml-1 text-brand-green transition-colors">
                {restWords}
              </p>
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default BrandMark;
