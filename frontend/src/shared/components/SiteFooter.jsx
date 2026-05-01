import {
  ChartLineUp,
  CheckCircle,
  EnvelopeSimple,
  FacebookLogo,
  GraduationCap,
  ShieldCheck,
  Sparkle,
  TiktokLogo,
  UserSound,
} from "@phosphor-icons/react";

import { useSiteSettings } from "@/shared/hooks/useSiteSettings";

const socialItems = [
  { key: "facebook", label: "Facebook", icon: FacebookLogo },
  { key: "community", label: "Cộng đồng", icon: UserSound },
  { key: "tiktok", label: "TikTok", icon: TiktokLogo },
  { key: "email", label: "Email", icon: EnvelopeSimple },
];

const resourceLinks = [
  { label: "Tính năng", href: "/#features" },
  { label: "Cách học", href: "/#how-it-works" },
  { label: "Chấm phát âm", href: "/#pronunciation" },
  { label: "Gamification", href: "/#gamification" },
];

const appLinks = [
  { label: "Đăng ký", href: "/register", icon: Sparkle },
  { label: "Đăng nhập", href: "/login", icon: CheckCircle },
  { label: "Learn", href: "/learn", icon: GraduationCap },
  { label: "Dashboard", href: "/dashboard", icon: ChartLineUp },
  { label: "Subscription", href: "/subscription", icon: ShieldCheck },
];

const legalLinks = [
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Terms of Service", href: "/terms" },
];

const SiteFooter = ({ className = "" }) => {
  const settings = useSiteSettings();

  return (
    <div className={`p-4 md:p-8 ${className}`}>
      <footer className="mx-auto max-w-7xl rounded-xl border border-solid border-gray-200 bg-[linear-gradient(126deg,rgba(242,245,247,0.78)_20%,rgba(255,254,247,0.78)_97%)] px-6 pb-5 pt-10 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-[30px] md:px-10 lg:rounded-3xl">
        <div className="grid grid-cols-1 gap-8 pb-[30px] md:grid-cols-2 lg:grid-cols-5">
          <div>
            <a href="/" className="flex items-center gap-3" aria-label="Buddy Talk home">
              <img src={settings.logoUrl} alt={settings.brandName} className="h-[54px] w-[54px] rounded-2xl object-cover shadow-sm" />
              <div>
                {settings.brandName.toLowerCase().replace(/\s+/g, "") === "buddytalk" ? (
                  <p className="flex items-center text-2xl font-black leading-none tracking-tighter">
                    <span className="text-foreground">Buddy</span>
                    <span className="ml-1 text-brand-green">Talk</span>
                  </p>
                ) : (
                  <p className="text-xl font-black text-foreground">{settings.brandName}</p>
                )}
                <p className="text-sm font-semibold text-[#667394]">{settings.tagline}</p>
              </div>
            </a>
          </div>

          <div>
            <h3 className="mb-6 text-lg font-semibold text-[#121212]">Liên hệ với chúng tôi</h3>
            <div className="flex flex-wrap items-center gap-3">
              {socialItems.map((item) => {
                const Icon = item.icon;
                const href = settings.socialLinks[item.key] || "#";
                return (
                  <a key={item.label} href={href} aria-label={item.label} className="flex items-center">
                    <span className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] shadow">
                      <Icon size={19} weight="fill" className="text-white" />
                    </span>
                  </a>
                );
              })}
            </div>
            <p className="mt-5 max-w-xs text-sm font-medium leading-6 text-[#667394]">
              {settings.contactNote}
            </p>
          </div>

          <div>
            <h3 className="mb-6 text-lg font-semibold text-[#121212]">Tài nguyên</h3>
            <ul className="flex flex-col gap-3">
              {resourceLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm font-medium text-[#667394] hover:text-brand-blue">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-6 text-lg font-semibold text-[#121212]">Ứng dụng</h3>
            <ul className="flex flex-col gap-3">
              {appLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <li key={link.href}>
                    <a href={link.href} className="inline-flex items-center gap-2 text-sm font-medium text-[#667394] hover:text-brand-blue">
                      <Icon size={16} weight="duotone" />
                      {link.label}
                    </a>
                  </li>
                );
              })}
            </ul>
          </div>

          <div>
            <h3 className="mb-6 text-lg font-semibold text-[#121212]">Pháp lý</h3>
            <ul className="flex flex-col gap-3">
              {legalLinks.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm font-medium text-[#667394] hover:text-brand-blue">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t border-[#D7D7D7] py-5 md:flex-row md:items-center md:justify-between">
          <p className="text-xs font-medium text-[#667394]">Copyright © 2026 {settings.brandName}</p>
          <p className="text-xs font-medium text-[#667394]">Luyện nói tiếng Anh với AI tutor, feedback tức thì, tiến bộ mỗi ngày.</p>
        </div>
      </footer>
    </div>
  );
};

export default SiteFooter;
