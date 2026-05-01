import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ChartLineUp,
  CheckCircle,
  Coins,
  Crown,
  GraduationCap,
  MicrophoneStage,
  Sparkle,
  SpeakerHigh,
  Star,
  Target,
  Trophy,
  UserSound,
  X,
} from "@phosphor-icons/react";

import AuthCard from "@/features/auth/components/AuthCard";
import PronunciationAssessmentWidget from "@/features/landing/components/PronunciationAssessmentWidget";
import SiteFooter from "@/shared/components/SiteFooter";
import { useSiteSettings } from "@/shared/hooks/useSiteSettings";
import landingCosmicBg from "@/assets/landing-cosmic-bg.png";

const navItems = [
  { label: "Tính năng", href: "#features" },
  { label: "Cách học", href: "#how-it-works" },
  { label: "Phát âm", href: "#pronunciation" },
  { label: "Gamification", href: "#gamification" },
];

const stats = [
  { value: "15 phút", label: "luyện nói mỗi ngày" },
  { value: "AI", label: "feedback tức thì" },
  { value: "24/7", label: "sẵn sàng luyện tập" },
];

const features = [
  {
    icon: UserSound,
    title: "AI Conversation",
    description: "Luyện hội thoại realtime với tutor AI theo chủ đề, mục tiêu và trình độ của bạn.",
  },
  {
    icon: SpeakerHigh,
    title: "Pronunciation Assessment",
    description: "Chấm phát âm theo từ/câu, phát hiện lỗi sai, thiếu từ và thừa từ rõ ràng.",
  },
  {
    icon: GraduationCap,
    title: "Curriculum",
    description: "Học theo unit, bài luyện nghe-nói, từ vựng và bài tập phát âm có cấu trúc.",
  },
  {
    icon: Trophy,
    title: "Leaderboard",
    description: "Theo dõi thứ hạng, điểm luyện tập và động lực cạnh tranh lành mạnh mỗi tuần.",
  },
  {
    icon: Coins,
    title: "Shop",
    description: "Biến tiến bộ thành phần thưởng trong app để giữ nhịp học vui hơn.",
  },
  {
    icon: ChartLineUp,
    title: "Profile Progress",
    description: "Xem tiến độ, lịch sử buổi học và chỉ số cải thiện sau mỗi phiên luyện nói.",
  },
];

const steps = [
  {
    title: "Chọn mục tiêu",
    description: "Onboarding giúp xác định trình độ, sở thích và mục tiêu học phù hợp.",
  },
  {
    title: "Luyện với AI",
    description: "Vào tình huống roleplay, trả lời bằng giọng nói và nhận phản hồi tự nhiên.",
  },
  {
    title: "Nhận feedback",
    description: "AI tóm tắt điểm mạnh, lỗi phát âm, độ trôi chảy và gợi ý câu tốt hơn.",
  },
  {
    title: "Theo dõi tiến bộ",
    description: "Dashboard, leaderboard và hồ sơ giúp bạn thấy nỗ lực tích lũy từng ngày.",
  },
];

const pronunciationScores = [
  { label: "Phát âm", score: 88, color: "bg-brand-green" },
  { label: "Chính xác", score: 82, color: "bg-brand-blue" },
  { label: "Trôi chảy", score: 76, color: "bg-brand-orange" },
];

const fadeIn = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const SectionHeading = ({ eyebrow, title, description }) => (
  <div className="mx-auto mb-12 max-w-3xl text-center">
    <p className="mb-3 text-sm font-black uppercase tracking-[0.28em] text-brand-blue">{eyebrow}</p>
    <h2 className="text-3xl font-black tracking-tight text-zinc-950 md:text-5xl">{title}</h2>
    <p className="mt-5 text-lg font-medium leading-8 text-zinc-600">{description}</p>
  </div>
);

const LandingPage = () => {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("features");
  const siteSettings = useSiteSettings();

  const openAuth = () => setIsAuthOpen(true);
  const closeAuth = () => setIsAuthOpen(false);

  useEffect(() => {
    const observedSections = navItems
      .map((item) => document.getElementById(item.href.replace("#", "")))
      .filter(Boolean);

    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visibleEntry?.target?.id) {
          setActiveSection(visibleEntry.target.id);
        }
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0.1, 0.25, 0.5] },
    );

    observedSections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#f8fbff] text-[#24324a]">
      <div
        className="fixed inset-0 -z-20 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${landingCosmicBg})` }}
      />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[linear-gradient(180deg,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0.50)_34%,rgba(244,253,255,0.64)_68%,rgba(255,253,244,0.80)_100%),radial-gradient(circle_at_18%_18%,rgba(255,253,244,0.78),transparent_34%),radial-gradient(circle_at_88%_18%,rgba(210,228,248,0.70),transparent_34%),radial-gradient(circle_at_12%_88%,rgba(136,223,70,0.16),transparent_36%)]" />

      <header className="fixed left-0 right-0 top-0 z-50 border-b border-white/70 bg-white/55 backdrop-blur-[24px]">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <a href="/" className="flex items-center gap-3" aria-label="Buddy Talk home">
            <img src={siteSettings.logoUrl} alt={siteSettings.brandName} className="h-11 w-11 rounded-2xl object-cover shadow-sm" />
            {siteSettings.brandName.toLowerCase().replace(/\s+/g, "") === "buddytalk" ? (
              <span className="flex items-center font-display text-2xl font-black leading-none tracking-tighter">
                <span className="text-foreground">Buddy</span>
                <span className="ml-1 text-brand-green">Talk</span>
              </span>
            ) : (
              <span className="font-display text-xl font-black tracking-tight text-foreground">{siteSettings.brandName}</span>
            )}
          </a>

          <div className="hidden items-center gap-8 rounded-full border border-white/80 bg-white/45 px-6 py-3 text-sm font-bold text-[#667394] shadow-sm shadow-sky-100/60 lg:flex">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`rounded-full px-3 py-1.5 transition ${
                  activeSection === item.href.replace("#", "")
                    ? "bg-gradient-to-r from-[#88DF46]/20 to-[#34DBC5]/20 text-[#1f8f83] shadow-sm"
                    : "hover:bg-white/60 hover:text-[#34DBC5]"
                }`}
              >
                {item.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button type="button" onClick={() => openAuth("login")} className="hidden rounded-full px-5 py-3 text-sm font-black text-[#667394] hover:bg-white/70 hover:text-[#34DBC5] sm:inline-flex">
              Đăng nhập
            </button>
            <button
              type="button"
              onClick={() => openAuth("register")}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-5 py-3 text-sm font-black text-white shadow-[0_10px_24px_rgba(52,219,197,0.24)] hover:shadow-[0_14px_30px_rgba(52,219,197,0.32)]"
            >
              Bắt đầu <ArrowRight weight="bold" />
            </button>
          </div>
        </nav>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-32 lg:grid-cols-[1.02fr_0.98fr] lg:px-8 lg:pb-28 lg:pt-40">
        <motion.div initial="hidden" animate="visible" variants={fadeIn} transition={{ duration: 0.65 }} className="max-w-3xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-green/20 bg-brand-green/10 px-4 py-2 text-sm font-black text-brand-green-dark">
            <Sparkle weight="fill" /> AI tutor luyện nói 24/7
          </div>
          <h1 className="text-5xl font-black leading-[1.02] tracking-[-0.055em] text-[#20314a] md:text-7xl">
            Luyện nói tiếng Anh mỗi ngày với AI tutor.
          </h1>
          <p className="mt-6 max-w-2xl text-lg font-medium leading-8 text-[#667394] md:text-xl">
            Buddy Talk giúp bạn nói nhiều hơn, sửa phát âm rõ hơn và giữ động lực bằng lộ trình học, điểm thưởng, leaderboard và phản hồi sau mỗi buổi luyện.
          </p>

          <div className="mt-9 flex flex-col gap-4 sm:flex-row">
            <button
              type="button"
              onClick={() => openAuth("register")}
              className="inline-flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-7 py-4 text-base font-black text-white shadow-2xl shadow-cyan-200/50 hover:-translate-y-0.5"
            >
              Tạo tài khoản miễn phí <ArrowRight weight="bold" />
            </button>
            <a
              href="#pronunciation"
              className="inline-flex items-center justify-center gap-3 rounded-2xl border border-white/80 bg-white/60 px-7 py-4 text-base font-black text-[#2f496b] shadow-sm backdrop-blur hover:-translate-y-0.5 hover:border-[#34DBC5]/50"
            >
              Xem chấm phát âm <MicrophoneStage weight="bold" />
            </a>
          </div>

          <div className="mt-10 grid max-w-2xl grid-cols-3 gap-3">
            {stats.map((stat) => (
              <div key={stat.label} className="rounded-3xl border border-white/80 bg-white/58 p-4 shadow-sm shadow-sky-100/50 backdrop-blur">
                <p className="text-2xl font-black text-[#20314a]">{stat.value}</p>
                <p className="mt-1 text-xs font-bold uppercase tracking-wide text-zinc-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 32 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.75, delay: 0.1 }}
          className="relative"
        >
          <div className="absolute -left-8 top-10 h-32 w-32 rounded-full bg-brand-green/25 blur-3xl" />
          <div className="absolute -right-10 bottom-12 h-40 w-40 rounded-full bg-brand-blue/25 blur-3xl" />
          <div className="relative rounded-[2.5rem] border border-white/85 bg-white/62 p-4 shadow-[0_30px_80px_rgba(52,219,197,0.16)] backdrop-blur-[18px]">
            <div className="rounded-[2rem] border border-white/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(210,228,248,0.58))] p-5 text-[#20314a]">
              <div className="mb-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] text-xl font-black text-white">AI</div>
                  <div>
                    <p className="font-black">Speaking Session</p>
                    <p className="text-sm font-semibold text-[#667394]">Travel roleplay · A2-B1</p>
                  </div>
                </div>
                <div className="rounded-full bg-[#88DF46]/20 px-3 py-1 text-sm font-black text-[#46a302]">Live</div>
              </div>

              <div className="space-y-3">
                <div className="max-w-[86%] rounded-3xl rounded-tl-md border border-white/70 bg-white/70 p-4 shadow-sm">
                  <p className="text-sm font-semibold text-[#667394]">AI Tutor</p>
                  <p className="mt-1 font-medium">Tell me about your last weekend trip. Try using past tense.</p>
                </div>
                <div className="ml-auto max-w-[86%] rounded-3xl rounded-tr-md bg-gradient-to-r from-[#34DBC5] to-[#8bdcff] p-4 text-white shadow-lg shadow-cyan-100">
                  <p className="text-sm font-semibold text-white/80">Bạn</p>
                  <p className="mt-1 font-medium">I went to Da Lat and tried new coffee with my friends.</p>
                </div>
                <div className="rounded-3xl border border-[#88DF46]/25 bg-[#88DF46]/12 p-4">
                  <div className="mb-2 flex items-center gap-2 text-[#46a302]">
                    <CheckCircle weight="fill" />
                    <span className="text-sm font-black uppercase tracking-wider">Feedback</span>
                  </div>
                  <p className="text-sm font-medium text-[#4f6280]">Great sentence. Practice ending sound in “friends” and add one detail about the place.</p>
                </div>
              </div>
            </div>

            <div className="-mt-6 ml-auto mr-4 max-w-sm rounded-[1.75rem] border border-white/80 bg-white/82 p-5 shadow-xl shadow-sky-100/60 backdrop-blur">
              <div className="mb-4 flex items-center justify-between">
                <p className="font-black">Session result</p>
                <div className="flex items-center gap-1 rounded-full bg-brand-gold/20 px-3 py-1 text-sm font-black text-amber-600">
                  <Star weight="fill" /> +120 XP
                </div>
              </div>
              <div className="space-y-3">
                {pronunciationScores.map((item) => (
                  <div key={item.label}>
                    <div className="mb-1 flex justify-between text-sm font-bold text-zinc-600">
                      <span>{item.label}</span>
                      <span>{item.score}</span>
                    </div>
                    <div className="h-2 rounded-full bg-zinc-100">
                      <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section id="features" className="py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <SectionHeading
            eyebrow="Tính năng"
            title="Một nơi đủ cho luyện nói, phát âm và động lực học."
            description="Landing chỉ giới thiệu chức năng đã có trong app: luyện hội thoại, học theo bài, chấm phát âm, leaderboard, shop và hồ sơ tiến bộ."
          />

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, margin: "-80px" }}
                  variants={fadeIn}
                  transition={{ duration: 0.45, delay: index * 0.04 }}
                  className="group rounded-[2rem] border border-white/80 bg-white/62 p-7 shadow-sm shadow-sky-100/40 backdrop-blur hover:-translate-y-1 hover:shadow-xl hover:shadow-sky-100"
                >
                  <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-blue/10 text-brand-blue group-hover:bg-brand-green/15 group-hover:text-brand-green-dark">
                    <Icon size={28} weight="duotone" />
                  </div>
                  <h3 className="text-xl font-black text-zinc-950">{feature.title}</h3>
                  <p className="mt-3 font-medium leading-7 text-zinc-600">{feature.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <SectionHeading
            eyebrow="Cách học"
            title="Từ mục tiêu đến tiến bộ, mỗi bước đều rõ ràng."
            description="Buddy Talk biến luyện nói thành vòng lặp ngắn: nói thật, nhận góp ý, sửa lỗi và quay lại luyện tiếp."
          />

          <div className="grid gap-5 lg:grid-cols-4">
            {steps.map((step, index) => (
              <div key={step.title} className="relative rounded-[2rem] border border-white/80 bg-white/58 p-7 shadow-sm shadow-sky-100/40 backdrop-blur">
                <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] text-lg font-black text-white">
                  {index + 1}
                </div>
                <h3 className="text-xl font-black">{step.title}</h3>
                <p className="mt-3 font-medium leading-7 text-zinc-600">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="pronunciation" className="py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div id="pronunciation-demo" className="mx-auto mb-10 max-w-3xl scroll-mt-28 text-center">
            <p className="mb-3 text-sm font-black uppercase tracking-[0.28em] text-brand-blue">Phát âm</p>
            <h2 className="text-3xl font-black tracking-tight text-[#20314a] md:text-5xl">Thử chấm phát âm ngay trên landing page.</h2>
            <p className="mt-5 text-lg font-medium leading-8 text-[#667394]">
              Đọc câu mẫu, gửi bản ghi âm để hệ thống chấm và xem lỗi được highlight trực tiếp trên câu gốc.
            </p>
          </div>
          <PronunciationAssessmentWidget />
        </div>
      </section>

      <section id="gamification" className="py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="grid items-center gap-10 rounded-[2.5rem] border border-white/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.76),rgba(210,228,248,0.56),rgba(255,253,244,0.72))] p-8 text-[#20314a] shadow-2xl shadow-sky-100/80 backdrop-blur-[18px] lg:grid-cols-[0.9fr_1.1fr] lg:p-12">
            <div>
              <p className="mb-3 text-sm font-black uppercase tracking-[0.28em] text-brand-green">Gamification</p>
              <h2 className="text-3xl font-black tracking-tight md:text-5xl">Học đều hơn bằng điểm, hạng và phần thưởng.</h2>
              <p className="mt-5 text-lg font-medium leading-8 text-[#667394]">
                Leaderboard và shop tạo động lực nhẹ nhàng để bạn quay lại luyện mỗi ngày, không biến học nói thành áp lực.
              </p>
              <button type="button" onClick={() => openAuth("register")} className="mt-8 inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-7 py-4 font-black text-white shadow-lg shadow-cyan-100 hover:shadow-xl hover:shadow-cyan-100">
                Bắt đầu tích XP <ArrowRight weight="bold" />
              </button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { icon: Crown, title: "Top tuần", value: "#8", text: "Tăng hạng khi hoàn thành session." },
                { icon: Star, title: "XP hôm nay", value: "+120", text: "Điểm thưởng sau luyện nói." },
                { icon: Coins, title: "Coin", value: "2,450", text: "Dùng trong shop của app." },
                { icon: Target, title: "Streak", value: "7 ngày", text: "Giữ nhịp luyện đều." },
              ].map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.title} className="rounded-[1.75rem] border border-white/80 bg-white/62 p-6 shadow-sm shadow-sky-100/50 backdrop-blur">
                    <Icon className="text-brand-green" size={30} weight="duotone" />
                    <p className="mt-5 text-sm font-black uppercase tracking-wider text-[#667394]">{card.title}</p>
                    <p className="mt-1 text-3xl font-black">{card.value}</p>
                    <p className="mt-2 text-sm font-semibold leading-6 text-[#667394]">{card.text}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="py-24">
        <div className="mx-auto max-w-5xl px-5 text-center lg:px-8">
          <h2 className="text-4xl font-black tracking-tight text-[#20314a] md:text-6xl">Sẵn sàng nói tiếng Anh nhiều hơn hôm nay?</h2>
          <p className="mx-auto mt-5 max-w-2xl text-lg font-medium leading-8 text-zinc-600">
            Tạo tài khoản, chọn mục tiêu và bắt đầu phiên luyện nói đầu tiên với Buddy Talk.
          </p>
          <div className="mt-9 flex flex-col justify-center gap-4 sm:flex-row">
            <button type="button" onClick={() => openAuth("register")} className="inline-flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-8 py-4 font-black text-white shadow-xl shadow-cyan-100 hover:shadow-2xl hover:shadow-cyan-100">
              Đăng ký ngay <ArrowRight weight="bold" />
            </button>
            <button type="button" onClick={() => openAuth("login")} className="inline-flex items-center justify-center rounded-2xl border border-white/80 bg-white/58 px-8 py-4 font-black text-[#2f496b] shadow-sm backdrop-blur hover:border-[#34DBC5]/50">
              Tôi đã có tài khoản
            </button>
          </div>
        </div>
      </section>

      <SiteFooter className="bg-transparent" />

      {isAuthOpen ? (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-zinc-950/55 px-4 py-6 backdrop-blur-md" role="dialog" aria-modal="true">
          <button type="button" aria-label="Đóng form đăng nhập" className="absolute inset-0 cursor-default" onClick={closeAuth} />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 20 }}
            transition={{ duration: 0.18 }}
            className="relative z-10 w-full max-w-[900px]"
          >
            <button
              type="button"
              onClick={closeAuth}
              aria-label="Đóng form đăng nhập"
              className="absolute -right-3 -top-3 z-20 flex size-10 items-center justify-center rounded-full bg-white text-zinc-600 shadow-lg shadow-zinc-950/20 hover:bg-zinc-100"
            >
              <X size={20} weight="bold" />
            </button>
            <AuthCard embedded />
          </motion.div>
        </div>
      ) : null}
    </main>
  );
};

export default LandingPage;
