import { Link } from "react-router-dom";

import BrandMark from "./BrandMark";

const AuthHeader = ({ mode = "login" }) => {
  const isLogin = mode === "login";

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 pt-4 md:px-6">
        <div className="flex h-[72px] items-center justify-between rounded-[28px] border border-[var(--panel-border)] bg-[var(--nav-bg)] px-4 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.2)] backdrop-blur-xl md:px-5">
          <BrandMark eyebrow="Account Access" />

          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] text-[var(--nav-muted)] transition hover:bg-[var(--chip-neutral-bg)] hover:text-[var(--nav-text)]"
            >
              Home
            </Link>
            <Link
              to={isLogin ? "/register" : "/login"}
              className="rounded-2xl bg-primary px-4 py-3 text-[11px] font-black uppercase tracking-[0.18em] text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5"
            >
              {isLogin ? "Create Account" : "Sign In"}
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AuthHeader;
