import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { forgotPassword, resetPassword } = useAuth();
  const navigate = useNavigate();

  const resendOtp = async () => {
    const normalizedEmail = email.trim().toLowerCase();
    setError("");
    setMessage("");
    setIsLoading(true);
    try {
      await forgotPassword(normalizedEmail);
      setMessage("Đã gửi lại mã OTP nếu email hợp lệ.");
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể gửi OTP.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Mật khẩu nhập lại không khớp.");
      return;
    }
    setError("");
    setMessage("");
    setIsLoading(true);
    try {
      await resetPassword({ email: email.trim().toLowerCase(), otp, new_password: newPassword });
      setMessage("Đã cập nhật mật khẩu. Đang chuyển về đăng nhập...");
      window.setTimeout(() => navigate("/login", { replace: true }), 900);
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể đặt lại mật khẩu.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fafafa] px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-[28px] border border-zinc-200 bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-black text-[#20314a]">Đặt lại mật khẩu</h1>
        <p className="mt-2 text-sm font-medium text-[#667394]">Nhập OTP đã gửi qua email và mật khẩu mới.</p>
        {error ? <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600">{error}</div> : null}
        {message ? <div className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">{message}</div> : null}
        <div className="mt-6 space-y-4">
          <input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" className="h-12 w-full rounded-xl border border-[#d9dde8] px-4 font-semibold" placeholder="Email" />
          <input value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))} required minLength={6} maxLength={6} inputMode="numeric" className="h-12 w-full rounded-xl border border-[#d9dde8] px-4 text-center font-semibold tracking-[0.35em]" placeholder="OTP" />
          <input value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required minLength={6} type="password" className="h-12 w-full rounded-xl border border-[#d9dde8] px-4 font-semibold" placeholder="Mật khẩu mới" />
          <input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={6} type="password" className="h-12 w-full rounded-xl border border-[#d9dde8] px-4 font-semibold" placeholder="Nhập lại mật khẩu mới" />
        </div>
        <button disabled={isLoading} className="mt-5 h-12 w-full rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] font-bold text-white disabled:opacity-70" type="submit">
          {isLoading ? "Đang cập nhật..." : "Cập nhật mật khẩu"}
        </button>
        <button disabled={isLoading || !email} onClick={resendOtp} className="mt-3 h-11 w-full rounded-xl border border-zinc-200 font-bold text-[#20314a] disabled:opacity-70" type="button">
          Gửi lại OTP
        </button>
        <Link className="mt-5 block text-center text-sm font-black text-indigo-600 hover:underline" to="/login">Quay lại đăng nhập</Link>
      </form>
    </div>
  );
};

export default ResetPasswordPage;
