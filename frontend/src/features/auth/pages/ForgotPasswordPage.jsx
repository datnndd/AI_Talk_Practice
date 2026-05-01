import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EnvelopeSimple } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { forgotPassword } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    setError("");
    setIsLoading(true);
    try {
      await forgotPassword(normalizedEmail);
      navigate(`/reset-password?email=${encodeURIComponent(normalizedEmail)}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Không thể gửi OTP. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fafafa] px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-[28px] border border-zinc-200 bg-white p-8 shadow-xl">
        <h1 className="text-2xl font-black text-[#20314a]">Quên mật khẩu</h1>
        <p className="mt-2 text-sm font-medium text-[#667394]">Nhập email để nhận mã OTP đặt lại mật khẩu.</p>
        {error ? <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600">{error}</div> : null}
        <label className="relative mt-6 block">
          <EnvelopeSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a8c4]" size={22} />
          <input
            autoFocus
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            className="h-12 w-full rounded-xl border border-[#d9dde8] bg-white py-3 pl-12 pr-4 font-semibold text-[#20314a] focus:border-[#34DBC5] focus:outline-none focus:ring-4 focus:ring-[#34DBC5]/10"
            placeholder="Email"
          />
        </label>
        <button disabled={isLoading} className="mt-5 h-12 w-full rounded-xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] font-bold text-white disabled:opacity-70" type="submit">
          {isLoading ? "Đang gửi..." : "Gửi mã OTP"}
        </button>
        <Link className="mt-5 block text-center text-sm font-black text-indigo-600 hover:underline" to="/login">Quay lại đăng nhập</Link>
      </form>
    </div>
  );
};

export default ForgotPasswordPage;
