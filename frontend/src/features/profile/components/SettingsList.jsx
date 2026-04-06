import { motion } from "framer-motion";
import { CaretRight, Lock, ShieldCheck, UserCircleGear } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const AccountRow = ({ icon: Icon, label, value, tone = "neutral", helper }) => {
  const toneClass =
    tone === "good"
      ? "bg-emerald-500/12 text-emerald-600"
      : tone === "warn"
        ? "bg-amber-500/12 text-amber-600"
        : "app-chip-neutral";

  return (
    <div className="app-panel-soft flex items-center justify-between rounded-[1.4rem] p-4">
      <div className="flex items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Icon weight="bold" size={20} />
        </div>
        <div>
          <p className="text-sm font-black text-[var(--page-fg)]">{label}</p>
          <p className="app-text-muted text-xs">{helper}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className={`rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.16em] ${toneClass}`}>{value}</span>
        <CaretRight weight="bold" className="app-text-subtle" />
      </div>
    </div>
  );
};

const SettingsList = () => {
  const { user } = useAuth();
  const isGoogleAccount = user?.auth_provider === "google";

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="app-panel rounded-[2rem] p-8"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">Account Controls</p>
          <h3 className="mt-2 text-2xl font-black text-[var(--page-fg)]">Security & Access Snapshot</h3>
        </div>
        <p className="app-text-muted max-w-xl text-sm leading-6">
          This section gives you a quick operational view of how the account is configured right now.
        </p>
      </div>

      <div className="mt-8 space-y-4">
        <AccountRow
          icon={UserCircleGear}
          label="Sign-in Method"
          value={isGoogleAccount ? "Google" : "Email"}
          helper={isGoogleAccount ? "This account was created through Google sign-in." : "This account uses email and password."}
        />
        <AccountRow
          icon={Lock}
          label="Password Status"
          value={user?.has_password ? "Configured" : "Missing"}
          tone={user?.has_password ? "good" : "warn"}
          helper={
            user?.has_password
              ? "You can change the password from the profile editor."
              : "Set a password in the editor to add a direct sign-in fallback."
          }
        />
        <AccountRow
          icon={ShieldCheck}
          label="Profile Readiness"
          value={user?.is_onboarding_completed ? "Ready" : "Needs setup"}
          tone={user?.is_onboarding_completed ? "good" : "warn"}
          helper={
            user?.is_onboarding_completed
              ? "Your personalization profile is complete."
              : "Complete the profile editor to improve coaching quality."
          }
        />
      </div>
    </motion.section>
  );
};

export default SettingsList;
