import { motion } from "framer-motion";
import { Crown, PencilSimple, Sparkle, Target } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";
import { getSubscriptionLabel } from "@/features/auth/utils/subscription";

const isImageAvatar = (avatar) =>
  typeof avatar === "string" &&
  (avatar.startsWith("http://") || avatar.startsWith("https://") || avatar.startsWith("data:") || avatar.startsWith("/"));

const ProfileHeader = ({ isEditing = false, onEditProfile }) => {
  const { user, isSubscribed } = useAuth();
  const displayName = user?.display_name || user?.email?.split("@")[0] || "Learner";
  const subtitle = [
    user?.level?.toUpperCase?.(),
    user?.native_language?.toUpperCase?.(),
    user?.target_language?.toUpperCase?.(),
  ]
    .filter(Boolean)
    .join(" | ");
  const authLabel = user?.auth_provider === "google" ? "Google Sign-in" : "Email Sign-in";
  const passwordLabel = user?.has_password ? "Password ready" : "Password not set";

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="app-panel relative overflow-hidden rounded-[2rem] p-8"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-[linear-gradient(135deg,rgba(0,90,182,0.18),rgba(14,165,233,0.08)_55%,transparent)]" />

      <div className="relative flex flex-col gap-8 xl:flex-row xl:items-end">
        <div className="flex flex-1 flex-col gap-6">
          <div className="flex flex-col gap-5 md:flex-row md:items-center">
            <div className="relative">
              <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-[2rem] bg-primary/10 text-4xl font-black text-primary shadow-[0_20px_40px_-24px_rgba(0,90,182,0.55)] ring-1 ring-white/60">
                {isImageAvatar(user?.avatar) ? (
                  <img src={user.avatar} alt={displayName} className="h-full w-full object-cover" />
                ) : (
                  displayName.charAt(0).toUpperCase()
                )}
              </div>
              <div className="app-chip absolute -bottom-2 left-1/2 inline-flex -translate-x-1/2 items-center gap-2 rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.18em]">
                <Sparkle weight="fill" size={12} />
                {getSubscriptionLabel(user?.subscription)}
              </div>
            </div>

            <div className="flex-1">
              <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.24em]">
                Profile Command Center
              </p>
              <h2 className="mt-3 font-display text-4xl font-black tracking-tight text-[var(--page-fg)]">
                {displayName}
              </h2>
              <div className="app-text-muted mt-3 flex flex-wrap items-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em]">
                <Target size={14} weight="bold" className="text-primary" />
                <span>{subtitle || "Complete your profile to personalize practice."}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <span className="app-chip rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em]">
              {authLabel}
            </span>
            <span className="app-chip-neutral rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em]">
              {passwordLabel}
            </span>
            <span
              className={`rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] ${
                isSubscribed ? "bg-emerald-500/12 text-emerald-600" : "bg-amber-500/12 text-amber-600"
              }`}
            >
              {isSubscribed ? "Subscription active" : "Free plan"}
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="app-panel-soft rounded-[1.5rem] p-4">
              <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.2em]">
                Practice Identity
              </p>
              <p className="mt-2 text-lg font-black text-[var(--page-fg)]">
                {user?.target_language?.toUpperCase?.() || "EN"} speaking track
              </p>
              <p className="app-text-muted mt-2 text-sm leading-6">
                Your settings shape tone, topic selection, and live coaching feedback across sessions.
              </p>
            </div>

            <div className="app-panel-soft rounded-[1.5rem] p-4">
              <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.2em]">Contact</p>
              <p className="mt-2 break-all text-lg font-black text-[var(--page-fg)]">{user?.email}</p>
              <p className="app-text-muted mt-2 text-sm leading-6">
                Keep this account current before changing voice, goals, and security options.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 xl:min-w-[220px]">
          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={onEditProfile}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-6 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20"
          >
            <PencilSimple weight="bold" size={16} />
            {isEditing ? "Close Editor" : "Edit Profile"}
          </motion.button>

          <div className="app-panel-soft rounded-[1.5rem] p-4">
            <div className="flex items-center gap-2 text-[var(--page-fg)]">
              <Crown weight="fill" size={18} className="text-primary" />
              <span className="text-sm font-black">Membership</span>
            </div>
            <p className="app-text-muted mt-2 text-sm leading-6">
              {isSubscribed
                ? "Your current plan keeps premium speaking sessions and advanced practice unlocked."
                : "Upgrade to unlock premium speaking sessions and deeper coaching controls."}
            </p>
          </div>
        </div>
      </div>
    </motion.section>
  );
};

export default ProfileHeader;
