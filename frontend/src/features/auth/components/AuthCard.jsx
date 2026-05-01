import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useGoogleLogin } from "@react-oauth/google";
import {
  ArrowRight,
  EnvelopeSimple,
  Eye,
  EyeSlash,
  GoogleLogo,
  LockSimple,
  MicrophoneStage,
  Sparkle,
  UserCircle,
} from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const copy = {
  login: {
    eyebrow: "Chào mừng trở lại",
    title: "Tiếp tục luyện nói cùng Buddy Talk",
    description: "Đăng nhập để quay lại dashboard, lịch sử luyện tập và mục tiêu hôm nay.",
    submit: "Đăng nhập",
    loading: "Đang đăng nhập...",
    switchPrompt: "Chưa có tài khoản?",
    switchAction: "Tạo tài khoản",
  },
  register: {
    eyebrow: "Bắt đầu miễn phí",
    title: "Tạo hồ sơ luyện nói của bạn",
    description: "Tạo tài khoản để nhận lộ trình, feedback phát âm và theo dõi tiến bộ mỗi ngày.",
    submit: "Tạo tài khoản",
    loading: "Đang tạo...",
    switchPrompt: "Đã có tài khoản?",
    switchAction: "Đăng nhập",
  },
};

const resolvePostLoginPath = (user) => {
  if (user?.is_admin) {
    return "/admin/scenarios";
  }

  return user?.is_onboarding_completed ? "/dashboard" : "/onboarding";
};

const AuthCard = ({ mode = "register", embedded = false, onModeChange }) => {
  const isLogin = mode === "login";
  const content = copy[mode] || copy.register;
  const [formData, setFormData] = useState({ email: "", password: "", name: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { login, register, googleLogin, refreshUser } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (tokenResponse) => {
    setIsLoading(true);
    setError("");
    try {
      await googleLogin(tokenResponse.access_token);
      const user = await refreshUser();
      navigate(resolvePostLoginPath(user), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Đăng nhập Google thất bại");
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError("Đăng nhập Google thất bại"),
  });

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData);
      }
      const user = await refreshUser();
      navigate(resolvePostLoginPath(user), { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || (isLogin ? "Email hoặc mật khẩu chưa đúng" : "Tạo tài khoản thất bại"));
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = isLogin ? "register" : "login";
  const switchPath = isLogin ? "/register" : "/login";

  const card = (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
      className="relative w-full max-w-[860px] overflow-hidden rounded-[30px] border border-white/70 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.16)]"
    >
      <div className="pointer-events-none absolute -right-20 -top-24 h-56 w-56 rounded-full bg-brand-green/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-20 h-56 w-56 rounded-full bg-brand-blue/20 blur-3xl" />

      <div className="relative grid lg:grid-cols-[0.92fr_1.08fr]">
        <aside className="hidden min-h-[560px] flex-col justify-between bg-zinc-950 p-8 text-white lg:flex">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-xs font-black uppercase tracking-[0.18em] text-brand-green">
              <Sparkle weight="fill" /> Buddy Talk
            </div>
            <h2 className="mt-8 font-display text-4xl font-black leading-tight tracking-[-0.04em]">
              Nói nhiều hơn, sửa nhanh hơn, tiến bộ rõ hơn.
            </h2>
            <p className="mt-4 text-sm font-semibold leading-7 text-zinc-300">
              Một tài khoản để vào dashboard, bài học, luyện hội thoại AI, chấm phát âm và theo dõi streak mỗi ngày.
            </p>
          </div>

          <div className="space-y-3">
            {[
              "AI tutor phản hồi tức thì",
              "Chấm phát âm theo từng từ",
              "XP, streak và leaderboard",
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/10 p-4 text-sm font-bold text-zinc-100">
                <span className="flex size-8 items-center justify-center rounded-xl bg-brand-green text-white">
                  <ArrowRight size={16} weight="bold" />
                </span>
                {item}
              </div>
            ))}
          </div>
        </aside>

        <div className="p-6 sm:p-8 lg:p-10">
          <div className="mb-7 flex items-center justify-between gap-4 lg:hidden">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand-green/20 bg-brand-green/10 px-3 py-2 text-xs font-black uppercase tracking-[0.18em] text-brand-green-dark">
              <Sparkle weight="fill" /> Buddy Talk
            </div>
            <div className="flex size-12 items-center justify-center rounded-2xl bg-zinc-950 text-white shadow-lg shadow-zinc-950/15">
              <MicrophoneStage size={25} weight="duotone" />
            </div>
          </div>

        <header className="mb-6">
          <p className="mb-2 text-sm font-black uppercase tracking-[0.22em] text-brand-blue">{content.eyebrow}</p>
          <h1 className="font-display text-[30px] font-black leading-[1.05] tracking-[-0.05em] text-zinc-950 sm:text-[36px]">
            {content.title}
          </h1>
          <p className="mt-4 text-sm font-semibold leading-6 text-zinc-500">{content.description}</p>
        </header>

        <button
          type="button"
          onClick={() => signInWithGoogle()}
          disabled={isLoading}
          className="mb-5 flex w-full items-center justify-center gap-3 rounded-2xl border border-zinc-200 bg-white px-5 py-4 text-sm font-black text-zinc-800 shadow-sm hover:-translate-y-0.5 hover:border-brand-blue/40 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <GoogleLogo size={22} weight="bold" className="text-red-500" />
          Tiếp tục với Google
        </button>

        <div className="mb-5 flex items-center gap-4">
          <div className="h-px flex-1 bg-zinc-200" />
          <span className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-400">hoặc email</span>
          <div className="h-px flex-1 bg-zinc-200" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error ? (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-center text-xs font-bold text-rose-600"
            >
              {error}
            </motion.div>
          ) : null}

          {!isLogin ? (
            <label className="group relative block">
              <UserCircle className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-brand-blue" size={22} weight="duotone" />
              <input
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full rounded-2xl border-2 border-zinc-100 bg-zinc-50 py-4 pl-12 pr-4 font-bold text-zinc-800 placeholder:text-zinc-400 focus:border-brand-blue focus:bg-white focus:outline-none"
                placeholder="Tên của bạn (tuỳ chọn)"
                type="text"
              />
            </label>
          ) : null}

          <label className="group relative block">
            <EnvelopeSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-brand-blue" size={22} weight="duotone" />
            <input
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full rounded-2xl border-2 border-zinc-100 bg-zinc-50 py-4 pl-12 pr-4 font-bold text-zinc-800 placeholder:text-zinc-400 focus:border-brand-blue focus:bg-white focus:outline-none"
              placeholder="Email"
              type="email"
            />
          </label>

          <label className="group relative block">
            <LockSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 group-focus-within:text-brand-blue" size={22} weight="duotone" />
            <input
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full rounded-2xl border-2 border-zinc-100 bg-zinc-50 py-4 pl-12 pr-12 font-bold text-zinc-800 placeholder:text-zinc-400 focus:border-brand-blue focus:bg-white focus:outline-none"
              placeholder="Mật khẩu"
              type={showPassword ? "text" : "password"}
            />
            <button
              type="button"
              onClick={() => setShowPassword((current) => !current)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-brand-blue"
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            >
              {showPassword ? <EyeSlash size={22} weight="bold" /> : <Eye size={22} weight="bold" />}
            </button>
          </label>

          <button
            disabled={isLoading}
            className="flex w-full items-center justify-center gap-3 rounded-2xl bg-brand-green px-5 py-4 font-display text-sm font-black uppercase tracking-[0.16em] text-white shadow-[0_5px_0_0_#46a302] transition-all hover:bg-brand-green-dark active:translate-y-[4px] active:shadow-none disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
          >
            {isLoading ? content.loading : content.submit}
            <ArrowRight size={18} weight="bold" />
          </button>
        </form>

        <footer className="mt-7 text-center text-[12px] font-bold leading-relaxed text-zinc-500">
          <p className="mb-4">
            Bằng việc {isLogin ? "đăng nhập" : "đăng ký"}, bạn đồng ý với điều khoản sử dụng Buddy Talk.
          </p>
          <p>
            {content.switchPrompt}
            {onModeChange ? (
              <button type="button" className="ml-2 font-black uppercase tracking-wider text-brand-blue hover:underline" onClick={() => onModeChange(switchMode)}>
                {content.switchAction}
              </button>
            ) : (
              <Link className="ml-2 font-black uppercase tracking-wider text-brand-blue hover:underline" to={switchPath}>
                {content.switchAction}
              </Link>
            )}
          </p>
        </footer>
        </div>
      </div>
    </motion.div>
  );

  if (embedded) {
    return card;
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[radial-gradient(circle_at_15%_20%,rgba(88,204,2,0.16),transparent_32%),radial-gradient(circle_at_85%_18%,rgba(28,176,246,0.18),transparent_28%),#f8fbff] px-4 py-16 selection:bg-brand-blue/10 selection:text-brand-blue">
      {card}
    </div>
  );
};

export default AuthCard;
