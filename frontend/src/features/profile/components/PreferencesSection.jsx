import { motion } from "framer-motion";
import { ChatCircleDots, Lightning, ListChecks, Waveform } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const PreferencesSection = () => {
  const { user } = useAuth();
  const favoriteTopics = Array.isArray(user?.favorite_topics)
    ? user.favorite_topics
    : user?.favorite_topics
      ? [user.favorite_topics]
      : [];
  const learningPurpose = Array.isArray(user?.learning_purpose)
    ? user.learning_purpose
    : user?.learning_purpose
      ? [user.learning_purpose]
      : [];
  const voiceFeedback = user?.preferences?.voice_feedback ?? true;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="app-panel rounded-[2rem] p-8"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.22em]">Learning Preferences</p>
          <h3 className="mt-2 text-2xl font-black text-[var(--page-fg)]">Personalization Signals</h3>
        </div>
        <p className="app-text-muted max-w-xl text-sm leading-6">
          These are the inputs the product uses to shape coaching style, recommendation quality, and speaking prompts.
        </p>
      </div>

      <div className="mt-8 grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="grid gap-4">
          <div className="app-panel-soft rounded-[1.5rem] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-500">
                <Waveform size={20} weight="bold" />
              </div>
              <div>
                <p className="text-sm font-black text-[var(--page-fg)]">Voice Feedback</p>
                <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.18em]">
                  Real-time correction loop
                </p>
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between rounded-[1.25rem] bg-white/55 px-4 py-3">
              <span className="app-text-muted text-sm font-bold">
                {voiceFeedback ? "Enabled for live coaching" : "Disabled for quieter practice"}
              </span>
              <span
                className={`rounded-full px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] ${
                  voiceFeedback ? "bg-emerald-500/12 text-emerald-600" : "bg-zinc-500/12 text-zinc-500"
                }`}
              >
                {voiceFeedback ? "On" : "Off"}
              </span>
            </div>
          </div>

          <div className="app-panel-soft rounded-[1.5rem] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-500/12 text-amber-500">
                <Lightning size={20} weight="bold" />
              </div>
              <div>
                <p className="text-sm font-black text-[var(--page-fg)]">Main Challenge</p>
                <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.18em]">
                  Highest-friction speaking area
                </p>
              </div>
            </div>

            <p className="app-text-muted mt-5 text-sm leading-7">
              {user?.main_challenge || "Describe your biggest speaking challenge to shape better prompts and corrections."}
            </p>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="app-panel-soft rounded-[1.5rem] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <ChatCircleDots size={20} weight="bold" />
              </div>
              <div>
                <p className="text-sm font-black text-[var(--page-fg)]">Learning Purpose</p>
                <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.18em]">
                  Why you are practicing
                </p>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {learningPurpose.length ? (
                learningPurpose.map((item) => (
                  <span key={item} className="app-chip rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.16em]">
                    {item}
                  </span>
                ))
              ) : (
                <span className="app-text-muted text-sm">
                  Add your purpose in the editor to improve recommendations.
                </span>
              )}
            </div>
          </div>

          <div className="app-panel-soft rounded-[1.5rem] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-500/12 text-sky-500">
                <ListChecks size={20} weight="bold" />
              </div>
              <div>
                <p className="text-sm font-black text-[var(--page-fg)]">Favorite Topics</p>
                <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.18em]">
                  Relevance anchors for practice
                </p>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {favoriteTopics.length ? (
                favoriteTopics.map((item) => (
                  <span key={item} className="app-chip-neutral rounded-full px-3 py-2 text-[10px] font-black uppercase tracking-[0.16em]">
                    {item}
                  </span>
                ))
              ) : (
                <span className="app-text-muted text-sm">No favorite topics saved yet.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.section>
  );
};

export default PreferencesSection;
