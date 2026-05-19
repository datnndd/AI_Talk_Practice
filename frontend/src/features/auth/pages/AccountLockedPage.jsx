import { Link } from "react-router-dom";
import { LockKey } from "@phosphor-icons/react";

const SUPPORT_EMAIL = "ddat260904@gmail.com";

const AccountLockedPage = () => (
  <main className="flex min-h-[100dvh] items-center justify-center bg-muted px-4 py-10 text-[var(--page-fg)]">
    <section className="w-full max-w-lg rounded-[32px] border border-border bg-card p-8 text-center shadow-sm">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300">
        <LockKey size={34} weight="duotone" />
      </div>
      <h1 className="mt-6 font-display text-3xl font-black tracking-tight">Tài khoản của bạn bị khóa</h1>
      <p className="mt-3 text-sm font-semibold leading-6 text-[var(--page-muted)]">
        Vui lòng liên hệ <a className="font-black text-primary hover:underline" href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a> để được hỗ trợ.
      </p>
      <Link to="/login" className="mt-8 inline-flex items-center justify-center rounded-2xl bg-primary px-5 py-3 text-sm font-black text-white">
        Quay lại đăng nhập
      </Link>
    </section>
  </main>
);

export default AccountLockedPage;
