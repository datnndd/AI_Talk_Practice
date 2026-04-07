import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import GoalProgress from "@/features/profile/components/GoalProgress";
import PreferencesSection from "@/features/profile/components/PreferencesSection";
import ProfileEditorCard from "@/features/profile/components/ProfileEditorCard";
import ProfileHeader from "@/features/profile/components/ProfileHeader";
import SettingsList from "@/features/profile/components/SettingsList";
import SubscriptionCard from "@/features/profile/components/SubscriptionCard";

const ProfileSettings = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!notice) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setNotice("");
    }, 3200);

    return () => window.clearTimeout(timer);
  }, [notice]);

  return (
    <>
      <div className="mx-auto w-full max-w-[1320px]">
        <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="app-text-subtle text-[10px] font-black uppercase tracking-[0.24em]">
                Settings Studio
              </p>
              <h1 className="mt-4 font-display text-4xl font-black tracking-tight text-[var(--page-fg)] md:text-5xl">
                Shape how LingoAI coaches you
              </h1>
            </div>
            <p className="app-text-muted max-w-xl text-sm leading-7">
              Manage your identity, learning path, and account preferences in one centralized workspace. Your data shapes your coaching experience.
            </p>
          </div>
        </motion.section>

        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          className="grid grid-cols-1 gap-6 md:grid-cols-12 items-start"
        >
          <div className="md:col-span-12">
            <ProfileHeader
              isEditing={isEditing}
              onEditProfile={() => setIsEditing((prev) => !prev)}
            />
          </div>
          
          <div className="md:col-span-7 flex flex-col gap-6">
            <PreferencesSection />
            <SettingsList />
          </div>
          
          <div className="md:col-span-5 flex flex-col gap-6">
            <GoalProgress />
            <SubscriptionCard />
          </div>
        </motion.div>

        <footer className="mt-16 flex flex-col items-center justify-between border-t border-[var(--panel-border)] py-10 md:flex-row">
          <p className="app-text-subtle text-[10px] font-bold uppercase tracking-[0.2em]">
            © 2024 LingoAI. High-intensity Language Practice.
          </p>
          <div className="mt-6 flex gap-10 md:mt-0">
            {["Help Center", "Terms", "Privacy"].map((item) => (
              <a
                key={item}
                className="app-text-subtle text-[10px] font-bold uppercase tracking-[0.2em] transition-colors hover:text-primary"
                href="#"
              >
                {item}
              </a>
            ))}
          </div>
        </footer>
      </div>

      {notice ? (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed left-1/2 top-28 z-[60] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 rounded-3xl border border-emerald-400/20 bg-[var(--panel-bg)] px-5 py-4 shadow-2xl backdrop-blur"
        >
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--success-text)]">
            Update successful
          </p>
          <p className="mt-1 text-sm font-bold text-[var(--page-fg)]">{notice}</p>
        </motion.div>
      ) : null}

      {isEditing ? (
        <ProfileEditorCard
          onClose={() => setIsEditing(false)}
          onSuccess={(message) => {
            setIsEditing(false);
            setNotice(message);
          }}
        />
      ) : null}
    </>
  );
};

export default ProfileSettings;
