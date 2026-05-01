import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useGoogleLogin } from "@react-oauth/google";
import {
  ArrowLeft,
  ArrowRight,
  EnvelopeSimple,
  Eye,
  EyeSlash,
  GoogleLogo,
  LockSimple,
  Sparkle,
} from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import loginRightSide from "@/assets/login_right_side.png";

const resolvePostLoginPath = (user) => {
  if (user?.is_admin) {
    return "/admin/scenarios";
  }

  return user?.is_onboarding_completed ? "/dashboard" : "/onboarding";
};

const normalizeEmail = (value) => value.trim().toLowerCase();

const AuthCard = ({ embedded = false }) => {
  const [step, setStep] = useState("start");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [resendSeconds, setResendSeconds] = useState(0);

  const { checkIdentity, login, register, requestOtp, verifyOtp, googleLogin, refreshUser } = useAuth();
  const navigate = useNavigate();

  const completeAuth = async () => {
    const user = await refreshUser();
    navigate(resolvePostLoginPath(user), { replace: true });
  };

  const handleGoogleSuccess = async (tokenResponse) => {
    setIsLoading(true);
    setError("");
    try {
      await googleLogin(tokenResponse.access_token);
      await completeAuth();
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể tiếp tục với Google.");
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError("Không thể tiếp tục với Google."),
  });

  useEffect(() => {
    if (resendSeconds <= 0) return undefined;
    const timerId = window.setTimeout(() => setResendSeconds((current) => Math.max(0, current - 1)), 1000);
    return () => window.clearTimeout(timerId);
  }, [resendSeconds]);

  const startEmailFlow = () => {
    setError("");
    setStep("email");
  };

  const handleEmailSubmit = async (event) => {
    event.preventDefault();
    const nextEmail = normalizeEmail(email);
    if (!nextEmail) {
      setError("Vui lòng nhập email.");
      return;
    }

    setEmail(nextEmail);
    setError("");
    setIsLoading(true);
    try {
      const identity = await checkIdentity(nextEmail);
      setPassword("");
      setOtp("");
      if (identity.status === "existing") {
        setStep("password-login");
      } else {
        setName(nextEmail.split("@")[0]);
        setStep("name-register");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể kiểm tra email. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNameSubmit = async (event) => {
    event.preventDefault();
    const normalizedEmail = normalizeEmail(email);
    if (!name.trim()) {
      setError("Vui lòng nhập tên.");
      return;
    }
    setError("");
    setIsLoading(true);
    try {
      await requestOtp({ email: normalizedEmail, purpose: "register" });
      setOtp("");
      setResendSeconds(60);
      setStep("otp-register");
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể gửi OTP. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendSeconds > 0 || isLoading) return;
    const normalizedEmail = normalizeEmail(email);
    setError("");
    setIsLoading(true);
    try {
      await requestOtp({ email: normalizedEmail, purpose: "register" });
      setOtp("");
      setResendSeconds(60);
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể gửi lại OTP. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpSubmit = async (event) => {
    event.preventDefault();
    const normalizedEmail = normalizeEmail(email);
    if (otp.length !== 6) {
      setError("Vui lòng nhập mã OTP gồm 6 số.");
      return;
    }
    setError("");
    setIsLoading(true);
    try {
      await verifyOtp({ email: normalizedEmail, purpose: "register", otp });
      setPassword("");
      setStep("password-register");
    } catch (err) {
      setError(err.response?.data?.detail || "Mã OTP chưa đúng hoặc đã hết hạn.");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    const normalizedEmail = normalizeEmail(email);
    if (!password) {
      setError("Vui lòng nhập mật khẩu.");
      return;
    }

    setError("");
    setIsLoading(true);
    try {
      if (step === "password-login") {
        await login(normalizedEmail, password);
      } else {
        await register({ email: normalizedEmail, otp, password, name: name.trim() });
      }
      await completeAuth();
    } catch (err) {
      setError(err.response?.data?.detail || (step === "password-login" ? "Email hoặc mật khẩu chưa đúng." : "Không thể tạo tài khoản."));
    } finally {
      setIsLoading(false);
    }
  };

  const resetToStart = () => {
    setStep("start");
    setError("");
    setPassword("");
    setOtp("");
    setName("");
    setResendSeconds(0);
  };

  const useAnotherEmail = () => {
    setStep("email");
    setError("");
    setPassword("");
    setOtp("");
    setResendSeconds(0);
  };

  const isPasswordStep = step === "password-login" || step === "password-register";
  const passwordTitle = step === "password-login" ? "Nhập mật khẩu để đăng nhập" : "Tạo mật khẩu";
  const passwordButton = step === "password-login" ? "Log in" : "Create account";

  const card = (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
      className="relative grid w-full max-w-[900px] overflow-hidden rounded-[32px] border border-zinc-200 bg-white shadow-[0_24px_70px_rgba(15,23,42,0.12)] lg:grid-cols-[420px_minmax(360px,1fr)]"
    >
      <div className="pointer-events-none absolute -right-16 -top-20 h-48 w-48 rounded-full bg-[#88DF46]/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 -left-16 h-48 w-48 rounded-full bg-[#34DBC5]/20 blur-3xl" />

      <div className="relative px-6 py-8 sm:px-9 lg:px-10 lg:py-10">
        {step !== "start" ? (
          <button
            type="button"
            onClick={step === "email" ? resetToStart : step === "otp-register" || step === "password-register" ? () => setStep("name-register") : useAnotherEmail}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/70 px-4 py-2 text-sm font-black text-[#667394] shadow-sm hover:text-[#1f8f83]"
          >
            <ArrowLeft size={17} weight="bold" />
            {step === "email" ? "Quay lại" : step === "otp-register" ? "Return to previous screen" : step === "password-register" ? "Return to previous screen" : "Dùng email khác"}
          </button>
        ) : null}

        <div className="mb-6 flex justify-start">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#88DF46]/20 bg-[#88DF46]/10 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-[#1f8f83]">
            <Sparkle weight="fill" /> Buddy Talk
          </div>
        </div>

        <header className="mb-6 text-left">
          <h1 className="font-display text-[28px] font-semibold leading-tight tracking-[-0.025em] text-[#20314a] sm:text-[32px]">
            {step === "start"
              ? "Log in or sign up in seconds"
              : step === "email"
                ? "Continue with email"
                : step === "name-register"
                  ? "Create your account"
                  : step === "otp-register"
                    ? "You’re almost signed up"
                    : passwordTitle}
          </h1>
          <p className="mt-3 max-w-sm text-[14px] font-medium leading-6 text-[#667394]">
            {step === "start"
              ? "Use your email or another service to continue with Buddy Talk. It’s free!"
              : step === "email"
                ? "Enter your email. If you already have an account, we’ll ask for your password."
                : step === "name-register"
                  ? `You’re creating a Buddy Talk account with ${email}`
                  : step === "otp-register"
                    ? `Enter the code we sent to ${email} to finish signing up.`
                    : email}
          </p>
        </header>

        {error ? (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-center text-xs font-bold text-rose-600"
          >
            {error}
          </motion.div>
        ) : null}

        {step === "start" ? (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => signInWithGoogle()}
              disabled={isLoading}
              className="relative flex h-12 w-full items-center justify-center rounded-xl border border-[#d9dde8] bg-white px-4 text-sm font-semibold text-[#24324a] shadow-sm transition hover:border-[#34DBC5] hover:bg-[#f8fbff] disabled:cursor-not-allowed disabled:opacity-70"
            >
              <GoogleLogo size={22} weight="bold" className="absolute left-4 text-red-500" />
              Continue with Google
            </button>
            <button
              type="button"
              onClick={startEmailFlow}
              className="relative flex h-12 w-full items-center justify-center rounded-xl border border-[#d9dde8] bg-white px-4 text-sm font-semibold text-[#24324a] shadow-sm transition hover:border-[#34DBC5] hover:bg-[#f8fbff]"
            >
              <EnvelopeSimple size={22} weight="bold" className="absolute left-4 text-[#24324a]" />
              Continue with email
            </button>
          </div>
        ) : null}

        {step === "email" ? (
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <label className="group relative block">
              <EnvelopeSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a8c4] group-focus-within:text-[#34DBC5]" size={22} weight="duotone" />
              <input
                autoFocus
                name="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                className="h-12 w-full rounded-xl border border-[#d9dde8] bg-white py-3 pl-12 pr-4 font-semibold text-[#20314a] placeholder:text-[#94a8c4] shadow-sm focus:border-[#34DBC5] focus:outline-none focus:ring-4 focus:ring-[#34DBC5]/10"
                placeholder="Email"
                type="email"
              />
            </label>
            <button
              disabled={isLoading}
              className="flex h-12 w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-5 text-sm font-bold text-white shadow-lg shadow-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
              type="submit"
            >
              {isLoading ? "Checking..." : "Continue"}
              <ArrowRight size={18} weight="bold" />
            </button>
          </form>
        ) : null}

        {step === "name-register" ? (
          <form onSubmit={handleNameSubmit} className="space-y-4">
            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-widest text-[#667394]">Name</span>
              <input
                autoFocus
                name="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
                autoComplete="name"
                className="h-12 w-full rounded-xl border border-[#d9dde8] bg-white px-4 py-3 font-semibold text-[#20314a] placeholder:text-[#94a8c4] shadow-sm focus:border-[#34DBC5] focus:outline-none focus:ring-4 focus:ring-[#34DBC5]/10"
                placeholder="Julie Smith"
                type="text"
              />
            </label>
            <button
              disabled={isLoading}
              className="flex h-12 w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-5 text-sm font-bold text-white shadow-lg shadow-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
              type="submit"
            >
              {isLoading ? "Sending code..." : "Continue"}
              <ArrowRight size={18} weight="bold" />
            </button>
          </form>
        ) : null}

        {step === "otp-register" ? (
          <form onSubmit={handleOtpSubmit} className="space-y-4">
            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-widest text-[#667394]">Code</span>
              <input
                autoFocus
                name="otp"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                required
                minLength={6}
                maxLength={6}
                autoComplete="one-time-code"
                inputMode="numeric"
                pattern="\d*"
                className="h-12 w-full rounded-xl border border-[#d9dde8] bg-white px-4 py-3 text-center font-semibold tracking-[0.35em] text-[#20314a] placeholder:text-[#94a8c4] shadow-sm focus:border-[#34DBC5] focus:outline-none focus:ring-4 focus:ring-[#34DBC5]/10"
                placeholder="000000"
              />
            </label>
            <div className="text-center text-xs font-bold text-[#667394]">
              Didn’t get the code?{" "}
              <button
                type="button"
                onClick={handleResendOtp}
                disabled={resendSeconds > 0 || isLoading}
                className="font-black text-indigo-600 hover:underline disabled:text-[#94a8c4] disabled:no-underline"
              >
                {resendSeconds > 0 ? `Resend in ${resendSeconds}s` : "Resend OTP"}
              </button>
            </div>
            <button
              disabled={isLoading}
              className="flex h-12 w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-5 text-sm font-bold text-white shadow-lg shadow-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
              type="submit"
            >
              {isLoading ? "Checking code..." : "Continue"}
              <ArrowRight size={18} weight="bold" />
            </button>
            <div className="flex items-center gap-3 py-2 text-xs font-black text-[#94a8c4]"><hr className="flex-1 border-zinc-200" />OR<hr className="flex-1 border-zinc-200" /></div>
            <button
              type="button"
              onClick={() => signInWithGoogle()}
              disabled={isLoading}
              className="relative flex h-12 w-full items-center justify-center rounded-xl border border-[#d9dde8] bg-white px-4 text-sm font-semibold text-[#24324a] shadow-sm transition hover:border-[#34DBC5] hover:bg-[#f8fbff] disabled:cursor-not-allowed disabled:opacity-70"
            >
              <GoogleLogo size={22} weight="bold" className="absolute left-4 text-red-500" />
              Continue with Google
            </button>
          </form>
        ) : null}

        {isPasswordStep ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <label className="group relative block">
              <LockSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a8c4] group-focus-within:text-[#34DBC5]" size={22} weight="duotone" />
              <input
                autoFocus
                name="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={step === "password-register" ? 6 : undefined}
                className="h-12 w-full rounded-xl border border-[#d9dde8] bg-white py-3 pl-12 pr-12 font-semibold text-[#20314a] placeholder:text-[#94a8c4] shadow-sm focus:border-[#34DBC5] focus:outline-none focus:ring-4 focus:ring-[#34DBC5]/10"
                placeholder={step === "password-login" ? "Password" : "Create password"}
                type={showPassword ? "text" : "password"}
              />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#94a8c4] hover:text-[#34DBC5]"
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              >
                {showPassword ? <EyeSlash size={22} weight="bold" /> : <Eye size={22} weight="bold" />}
              </button>
            </label>
            <button
              disabled={isLoading}
              className="flex h-12 w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-5 text-sm font-bold text-white shadow-lg shadow-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
              type="submit"
            >
              {isLoading ? "Please wait..." : passwordButton}
              <ArrowRight size={18} weight="bold" />
            </button>
            {step === "password-login" ? (
              <Link className="block text-center text-xs font-black text-indigo-600 hover:underline" to="/forgot-password">
                Quên mật khẩu?
              </Link>
            ) : null}
          </form>
        ) : null}

        <footer className="mt-7 text-left text-[12px] font-medium leading-relaxed text-[#667394]">
          By continuing, you agree to Buddy Talk’s{" "}
          <Link className="font-semibold text-[#20314a] underline underline-offset-2 hover:text-[#34DBC5]" to="/terms">Terms</Link>
          {" "}and{" "}
          <Link className="font-semibold text-[#20314a] underline underline-offset-2 hover:text-[#34DBC5]" to="/privacy">Privacy Policy</Link>.
        </footer>
      </div>

      <div className="relative hidden min-h-[620px] overflow-hidden bg-zinc-50 lg:block">
        <img
          src={loginRightSide}
          alt="Buddy Talk learning preview"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(52,219,197,0.10))]" />
      </div>
    </motion.div>
  );

  if (embedded) {
    return card;
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-white px-4 py-16 selection:bg-brand-blue/10 selection:text-brand-blue">
      {card}
    </div>
  );
};

export default AuthCard;
