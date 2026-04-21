import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Camera,
  CaretDown,
  Check,
  ChatsCircle,
  Fire,
  MicrophoneStage,
  Moon,
  Palette,
  PencilSimple,
  SuitcaseSimple,
  UserCircle,
} from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/features/auth/context/AuthContext";
import { useTheme } from "@/shared/context/ThemeContext";

const MAX_BIO_LENGTH = 150;

const TOPIC_OPTIONS = [
  { value: "Daily Life", label: "Daily Life", icon: ChatsCircle },
  { value: "Business", label: "Business", icon: SuitcaseSimple },
  { value: "Travel", label: "Travel", icon: MicrophoneStage },
  { value: "IELTS Prep", label: "IELTS Prep", icon: PencilSimple },
  { value: "Dining Out", label: "Dining Out", icon: ChatsCircle },
  { value: "Pop Culture", label: "Pop Culture", icon: Fire },
];

const LANGUAGE_OPTIONS = [
  { value: "en", label: "English", flag: "🇬🇧" },
  { value: "de", label: "German", flag: "🇩🇪" },
  { value: "es", label: "Spanish", flag: "🇪🇸" },
  { value: "fr", label: "French", flag: "🇫🇷" },
  { value: "vi", label: "Vietnamese", flag: "🇻🇳" },
  { value: "zh", label: "Chinese", flag: "🇨🇳" },
];

const PROFILE_THEME_OPTIONS = [
  { value: "green", swatch: "bg-[#58CC02]", ring: "ring-[#58CC02]" },
  { value: "blue", swatch: "bg-sky-400", ring: "ring-sky-400" },
  { value: "purple", swatch: "bg-violet-400", ring: "ring-violet-400" },
  { value: "orange", swatch: "bg-orange-400", ring: "ring-orange-400" },
];

const PROFILE_THEME_STYLES = {
  green: {
    text: "text-[#58CC02]",
    softText: "text-[#7a7a7a]",
    solid: "bg-[#58CC02] hover:bg-[#52bb02]",
    soft: "bg-[#58CC02]/10",
    border: "border-[#58CC02]",
    shadow: "shadow-[0_4px_0_0_#46a302]",
    pill: "bg-[#fff4e8] text-[#ff9500]",
  },
  blue: {
    text: "text-sky-500",
    softText: "text-[#7a7a7a]",
    solid: "bg-sky-500 hover:bg-sky-600",
    soft: "bg-sky-500/10",
    border: "border-sky-500",
    shadow: "shadow-[0_4px_0_0_#0284c7]",
    pill: "bg-sky-100 text-sky-600",
  },
  purple: {
    text: "text-violet-500",
    softText: "text-[#7a7a7a]",
    solid: "bg-violet-500 hover:bg-violet-600",
    soft: "bg-violet-500/10",
    border: "border-violet-500",
    shadow: "shadow-[0_4px_0_0_#7c3aed]",
    pill: "bg-violet-100 text-violet-600",
  },
  orange: {
    text: "text-orange-500",
    softText: "text-[#7a7a7a]",
    solid: "bg-orange-500 hover:bg-orange-600",
    soft: "bg-orange-500/10",
    border: "border-orange-500",
    shadow: "shadow-[0_4px_0_0_#ea580c]",
    pill: "bg-orange-100 text-orange-600",
  },
};

const normalizeTopics = (value) => {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }

  if (typeof value === "string" && value.trim()) {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
};

const createHandleFromUser = (user) => {
  const savedHandle = user?.preferences?.handle;

  if (typeof savedHandle === "string" && savedHandle.trim()) {
    return savedHandle.trim().replace(/^@/, "");
  }

  const source = user?.display_name || user?.email?.split("@")[0] || "learner";
  return source
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 24);
};

const createFormState = (user, theme) => ({
  displayName: user?.display_name ?? "",
  avatar: user?.avatar ?? "",
  bio: user?.preferences?.bio ?? "",
  handle: createHandleFromUser(user),
  favoriteTopics: normalizeTopics(user?.favorite_topics),
  dailyGoal: Number(user?.daily_goal ?? 20),
  targetLanguage: user?.target_language ?? "de",
  darkMode: (user?.preferences?.theme_preference ?? theme) === "dark",
  profileTheme: user?.preferences?.profile_theme ?? "green",
});

const buildPayload = (formState, user) => ({
  display_name: formState.displayName.trim() || null,
  avatar: formState.avatar.trim() || null,
  target_language: formState.targetLanguage || null,
  favorite_topics: formState.favoriteTopics.length ? formState.favoriteTopics : null,
  daily_goal: Number(formState.dailyGoal) || null,
  preferences: {
    ...(user?.preferences ?? {}),
    bio: formState.bio.trim() || null,
    handle: formState.handle.trim().replace(/^@/, "") || null,
    profile_theme: formState.profileTheme,
    theme_preference: formState.darkMode ? "dark" : "light",
  },
});

const getLanguageMeta = (value) =>
  LANGUAGE_OPTIONS.find((language) => language.value === value) ?? LANGUAGE_OPTIONS[0];

const getDailyGoalLabel = (goal) => {
  if (goal >= 45) {
    return "INTENSE";
  }

  if (goal >= 25) {
    return "STRONG";
  }

  return "REGULAR";
};

const isImageAvatar = (avatar) =>
  typeof avatar === "string" &&
  avatar.trim() &&
  (avatar.startsWith("http://") ||
    avatar.startsWith("https://") ||
    avatar.startsWith("data:") ||
    avatar.startsWith("/"));

const SectionTitle = ({ icon: Icon, children, accentText }) => (
  <h2 className={`mb-6 flex items-center gap-2 text-lg font-extrabold uppercase tracking-[0.08em] ${accentText}`}>
    <Icon size={18} weight="fill" />
    {children}
  </h2>
);

const TopicChip = ({ icon: Icon, label, selected, accent }) => (
  <span
    className={`inline-flex items-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-bold transition-all ${
      selected
        ? `${accent.soft} ${accent.border} ${accent.text} shadow-[0_3px_0_0_#d9d9d9]`
        : "border-gray-100 bg-white text-gray-500"
    }`}
  >
    <Icon size={18} weight={selected ? "fill" : "regular"} />
    {label}
  </span>
);

const ProfileSettingsPage = () => {
  const navigate = useNavigate();
  const { user, updateProfile } = useAuth();
  const { theme, setTheme } = useTheme();

  const [formState, setFormState] = useState(() => createFormState(user, theme));
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingHandle, setIsEditingHandle] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    setFormState(createFormState(user, theme));
  }, [theme, user]);

  useEffect(() => {
    if (!notice) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setNotice("");
    }, 3200);

    return () => window.clearTimeout(timer);
  }, [notice]);

  const accent = PROFILE_THEME_STYLES[formState.profileTheme] ?? PROFILE_THEME_STYLES.green;
  const language = getLanguageMeta(formState.targetLanguage);
  const baselinePayload = useMemo(() => buildPayload(createFormState(user, theme), user), [theme, user]);
  const currentPayload = useMemo(() => buildPayload(formState, user), [formState, user]);
  const hasChanges = JSON.stringify(baselinePayload) !== JSON.stringify(currentPayload);
  const bioLength = formState.bio.length;
  const displayName = formState.displayName.trim() || user?.email?.split("@")[0] || "Learner";
  const streakDays = Number(user?.preferences?.streak_days ?? 0);
  const streakLabel = streakDays > 0 ? `${streakDays} DAY STREAK` : "READY TO PRACTICE";

  const updateField = (field, value) => {
    setFormState((current) => ({ ...current, [field]: value }));
    setError("");
  };

  const toggleTopic = (topic) => {
    setFormState((current) => {
      const exists = current.favoriteTopics.includes(topic);

      return {
        ...current,
        favoriteTopics: exists
          ? current.favoriteTopics.filter((item) => item !== topic)
          : [...current.favoriteTopics, topic],
      };
    });
    setError("");
  };

  const handleAvatarUpload = () => {
    const nextAvatar = window.prompt("Paste an image URL for your profile photo", formState.avatar);

    if (nextAvatar === null) {
      return;
    }

    updateField("avatar", nextAvatar.trim());
  };

  const handleAvatarCustomize = () => {
    updateField("avatar", "");
  };

  const handleCancel = () => {
    navigate("/dashboard");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (bioLength > MAX_BIO_LENGTH) {
      setError(`Bio must stay within ${MAX_BIO_LENGTH} characters.`);
      return;
    }

    if (!hasChanges) {
      setError("Update at least one field before saving.");
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      await updateProfile(currentPayload);
      setTheme(formState.darkMode ? "dark" : "light");
      setNotice("Profile updated successfully.");
      setIsEditingHandle(false);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to save your profile right now.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-[#f6f7f5] text-[#1f2937]">
      <header className="sticky top-0 z-40 border-b-2 border-gray-100 bg-white">
        <div className="mx-auto flex h-[78px] w-full max-w-6xl items-center justify-between gap-4 px-4 md:px-6">
          <div className={`flex items-center gap-2 text-lg font-black tracking-tight md:text-2xl ${accent.text}`}>
            <ChatsCircle size={28} weight="fill" />
            <span>Emerald Quest</span>
          </div>

          <h1 className="hidden text-xl font-bold text-[#1f2937] md:block">Edit Profile</h1>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCancel}
              className="hidden px-4 py-2 text-sm font-bold text-gray-500 transition-colors hover:text-[#1f2937] sm:inline-flex"
            >
              Cancel
            </button>
            <button
              type="submit"
              form="edit-profile-form"
              disabled={isSaving || !hasChanges}
              className={`rounded-2xl px-5 py-2.5 text-sm font-bold text-white transition-all ${accent.solid} ${accent.shadow} disabled:translate-y-0 disabled:cursor-not-allowed disabled:shadow-none disabled:opacity-50`}
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-8 md:px-6 md:py-10">
        {notice ? (
          <div className="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">
            {notice}
          </div>
        ) : null}

        {error ? (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">
            {error}
          </div>
        ) : null}

        <form id="edit-profile-form" onSubmit={handleSubmit}>
          <motion.section
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative mb-8 overflow-hidden rounded-[28px] border-2 border-gray-100 bg-white p-6 shadow-sm md:p-8"
          >
            <div className="flex flex-col gap-8 md:flex-row md:items-center">
              <div className="relative mx-auto md:mx-0">
                <div
                  className={`flex h-36 w-36 items-center justify-center overflow-hidden rounded-full border-4 border-gray-100 text-4xl font-black shadow-inner md:h-40 md:w-40 ${
                    isImageAvatar(formState.avatar)
                      ? "bg-white"
                      : `${accent.soft} ${accent.text}`
                  }`}
                >
                  {isImageAvatar(formState.avatar) ? (
                    <img src={formState.avatar} alt={displayName} className="h-full w-full object-cover" />
                  ) : (
                    displayName
                      .split(" ")
                      .map((item) => item[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleAvatarCustomize}
                  className="absolute bottom-1 right-1 rounded-full border-2 border-gray-100 bg-white p-3 text-[#58CC02] shadow-lg transition-transform hover:scale-105"
                  aria-label="Customize avatar"
                >
                  <PencilSimple size={18} weight="bold" />
                </button>
              </div>

              <div className="flex-1 text-center md:text-left">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
                  <h2 className="text-3xl font-extrabold tracking-tight text-[#1f2937] md:text-4xl">
                    {displayName}
                  </h2>
                  <div className={`inline-flex items-center justify-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${accent.pill}`}>
                    <Fire size={14} weight="fill" />
                    {streakLabel}
                  </div>
                </div>

                <div className="mt-2 flex flex-col items-center justify-center gap-2 md:flex-row md:justify-start">
                  {isEditingHandle ? (
                    <input
                      value={formState.handle}
                      onChange={(event) => updateField("handle", event.target.value)}
                      onBlur={() => setIsEditingHandle(false)}
                      className="rounded-xl border-2 border-gray-100 bg-gray-50 px-3 py-2 text-sm font-semibold text-gray-600 outline-none focus:border-[#58CC02]"
                      maxLength={24}
                      autoFocus
                    />
                  ) : (
                    <p className="text-lg font-medium italic text-gray-500">@{formState.handle || "learner"}</p>
                  )}

                  <button
                    type="button"
                    onClick={() => setIsEditingHandle((current) => !current)}
                    className="text-sm font-bold uppercase tracking-[0.08em] text-orange-500 transition-colors hover:underline"
                  >
                    Change
                  </button>
                </div>

                <div className="mt-6 flex flex-wrap justify-center gap-3 md:justify-start">
                  <button
                    type="button"
                    onClick={handleAvatarCustomize}
                    className="inline-flex items-center gap-2 rounded-2xl bg-gray-100 px-5 py-3 text-sm font-bold text-[#1f2937] transition-colors hover:bg-gray-200"
                  >
                    <UserCircle size={18} weight="fill" />
                    Customize Avatar
                  </button>
                  <button
                    type="button"
                    onClick={handleAvatarUpload}
                    className="inline-flex items-center gap-2 rounded-2xl border-2 border-gray-100 px-5 py-3 text-sm font-bold text-gray-600 transition-colors hover:border-[#58CC02] hover:text-[#58CC02]"
                  >
                    <Camera size={18} weight="bold" />
                    Upload Photo
                  </button>
                </div>
              </div>
            </div>
          </motion.section>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div className="space-y-8">
              <motion.section
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 }}
                className="rounded-[28px] border-2 border-gray-100 bg-white p-6 shadow-sm md:p-8"
              >
                <SectionTitle icon={UserCircle} accentText={accent.text}>
                  Basic Information
                </SectionTitle>

                <div className="space-y-5">
                  <div>
                    <label htmlFor="full-name" className="mb-2 block px-1 text-sm font-bold text-gray-500">
                      FULL NAME
                    </label>
                    <input
                      id="full-name"
                      value={formState.displayName}
                      onChange={(event) => updateField("displayName", event.target.value)}
                      className="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 p-4 font-semibold text-[#1f2937] outline-none transition-colors focus:border-[#58CC02]"
                      placeholder="Your full name"
                    />
                  </div>

                  <div>
                    <label htmlFor="bio" className="mb-2 block px-1 text-sm font-bold text-gray-500">
                      BIO
                    </label>
                    <textarea
                      id="bio"
                      value={formState.bio}
                      onChange={(event) => updateField("bio", event.target.value.slice(0, MAX_BIO_LENGTH))}
                      className="h-32 w-full resize-none rounded-2xl border-2 border-gray-100 bg-gray-50 p-4 font-medium text-[#1f2937] outline-none transition-colors focus:border-[#58CC02]"
                      placeholder="I practice speaking English 20 minutes every day!"
                    />
                    <p className="mt-2 text-right text-xs font-bold uppercase text-gray-400">
                      {bioLength} / {MAX_BIO_LENGTH}
                    </p>
                  </div>
                </div>
              </motion.section>

              <motion.section
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.16 }}
                className="rounded-[28px] border-2 border-gray-100 bg-white p-6 shadow-sm md:p-8"
              >
                <SectionTitle icon={ChatsCircle} accentText={accent.text}>
                  Learning Goals
                </SectionTitle>

                <div className="space-y-8">
                  <div>
                    <label htmlFor="daily-goal" className="mb-4 block px-1 text-sm font-bold uppercase text-gray-500">
                      Daily Speaking Goal
                    </label>

                    <div className="rounded-2xl bg-gray-50 p-5">
                      <div className="mb-4 flex items-end justify-between">
                        <span className={`text-3xl font-black ${accent.text}`}>
                          {formState.dailyGoal} <span className="text-lg font-bold text-gray-400">min</span>
                        </span>
                        <span className="rounded-lg bg-orange-50 px-2 py-1 text-xs font-bold text-orange-500">
                          {getDailyGoalLabel(formState.dailyGoal)}
                        </span>
                      </div>

                      <input
                        id="daily-goal"
                        type="range"
                        min="5"
                        max="60"
                        step="5"
                        value={formState.dailyGoal}
                        onChange={(event) => updateField("dailyGoal", Number(event.target.value))}
                        className="h-2.5 w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-[#58CC02]"
                      />

                      <div className="mt-3 flex justify-between px-1 text-xs font-bold text-gray-400">
                        <span>5m</span>
                        <span>15m</span>
                        <span>30m</span>
                        <span>45m</span>
                        <span>60m</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label htmlFor="target-language" className="mb-3 block px-1 text-sm font-bold uppercase text-gray-500">
                      Target Language
                    </label>

                    <div className="relative">
                      <select
                        id="target-language"
                        value={formState.targetLanguage}
                        onChange={(event) => updateField("targetLanguage", event.target.value)}
                        className="w-full appearance-none rounded-2xl border-2 border-gray-100 bg-gray-50 p-4 pr-12 font-bold text-[#1f2937] outline-none transition-colors focus:border-[#58CC02]"
                      >
                        {LANGUAGE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.flag} {option.label}
                          </option>
                        ))}
                      </select>

                      <div className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-gray-400">
                        <CaretDown size={18} weight="bold" />
                      </div>
                    </div>
                  </div>
                </div>
              </motion.section>
            </div>

            <div className="space-y-8">
              <motion.section
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.12 }}
                className="rounded-[28px] border-2 border-gray-100 bg-white p-6 shadow-sm md:p-8"
              >
                <SectionTitle icon={MicrophoneStage} accentText={accent.text}>
                  Speaking Topics
                </SectionTitle>

                <p className="mb-6 text-sm font-medium text-gray-500">
                  Select the topics you want to focus on during your AI conversations.
                </p>

                <div className="flex flex-wrap gap-3">
                  {TOPIC_OPTIONS.map((topic) => (
                    <button
                      key={topic.value}
                      type="button"
                      onClick={() => toggleTopic(topic.value)}
                    >
                      <TopicChip
                        icon={topic.icon}
                        label={topic.label}
                        selected={formState.favoriteTopics.includes(topic.value)}
                        accent={accent}
                      />
                    </button>
                  ))}
                </div>
              </motion.section>

              <motion.section
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-[28px] border-2 border-gray-100 bg-white p-6 shadow-sm md:p-8"
              >
                <SectionTitle icon={Palette} accentText={accent.text}>
                  Account & Theme
                </SectionTitle>

                <div className="space-y-6">
                  <div>
                    <label htmlFor="email-address" className="mb-2 block px-1 text-sm font-bold text-gray-500">
                      EMAIL ADDRESS
                    </label>

                    <div className="flex items-center gap-2">
                      <input
                        id="email-address"
                        value={user?.email ?? ""}
                        readOnly
                        className="min-w-0 flex-1 rounded-2xl border-2 border-gray-100 bg-gray-50 p-4 font-semibold text-gray-400 outline-none"
                      />
                      <button type="button" className="px-2 text-sm font-bold text-orange-500">
                        Change
                      </button>
                    </div>
                  </div>

                  <div className="border-t border-gray-100 pt-4">
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-3">
                        <Moon size={20} className="text-gray-400" weight="fill" />
                        <span className="font-bold text-[#1f2937]">Dark Mode</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => updateField("darkMode", !formState.darkMode)}
                        className={`relative h-8 w-14 rounded-full transition-colors ${
                          formState.darkMode ? "bg-[#58CC02]" : "bg-gray-200"
                        }`}
                        aria-pressed={formState.darkMode}
                        aria-label="Toggle dark mode"
                      >
                        <span
                          className={`absolute top-1 h-6 w-6 rounded-full bg-white transition-transform ${
                            formState.darkMode ? "translate-x-7" : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>

                    <div className="flex items-center justify-between py-4">
                      <span className="font-bold text-[#1f2937]">Profile Theme</span>

                      <div className="flex gap-2">
                        {PROFILE_THEME_OPTIONS.map((option) => {
                          const isSelected = option.value === formState.profileTheme;

                          return (
                            <button
                              key={option.value}
                              type="button"
                              onClick={() => updateField("profileTheme", option.value)}
                              aria-label={`Set profile theme to ${option.value}`}
                              className={`h-8 w-8 rounded-full ${option.swatch} ${
                                isSelected ? `ring-2 ring-offset-2 ${option.ring}` : ""
                              }`}
                            >
                              {isSelected ? <span className="sr-only">Selected</span> : null}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl bg-gray-50 p-4">
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 rounded-full p-2 ${accent.soft} ${accent.text}`}>
                        <Check size={16} weight="bold" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[#1f2937]">
                          Current learning setup
                        </p>
                        <p className="mt-1 text-sm text-gray-500">
                          {language.flag} {language.label} • {formState.favoriteTopics.length || 0} selected topics •{" "}
                          {formState.dailyGoal} minutes per day
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.section>
            </div>
          </div>
        </form>
      </main>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t-2 border-gray-100 bg-white p-4 md:hidden">
        <button
          type="submit"
          form="edit-profile-form"
          disabled={isSaving || !hasChanges}
          className={`w-full rounded-2xl px-5 py-4 text-lg font-black text-white transition-all ${accent.solid} ${accent.shadow} disabled:cursor-not-allowed disabled:shadow-none disabled:opacity-50`}
        >
          {isSaving ? "Saving..." : "SAVE CHANGES"}
        </button>
      </div>

      <div className="h-24 md:hidden" />
    </div>
  );
};

export default ProfileSettingsPage;
