import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowsCounterClockwise, FloppyDiskBack, LockKey, Sparkle, X } from "@phosphor-icons/react";

import { useAuth } from "@/features/auth/context/AuthContext";

const LANGUAGE_OPTIONS = [
  { value: "vi", label: "Vietnamese" },
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "zh", label: "Chinese" },
  { value: "fr", label: "French" },
];

const LEVEL_OPTIONS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "A1", label: "A1" },
  { value: "A2", label: "A2" },
  { value: "B1", label: "B1" },
  { value: "B2", label: "B2" },
  { value: "C1", label: "C1" },
  { value: "C2", label: "C2" },
];

const toCommaSeparated = (value) => {
  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "string") {
    return value;
  }

  return "";
};

const toFormState = (user) => ({
  display_name: user?.display_name ?? "",
  age: user?.age ?? "",
  native_language: user?.native_language ?? "vi",
  target_language: user?.target_language ?? "en",
  level: user?.level ?? "intermediate",
  daily_goal: user?.daily_goal ?? 15,
  learning_purpose: toCommaSeparated(user?.learning_purpose),
  favorite_topics: toCommaSeparated(user?.favorite_topics),
  main_challenge: user?.main_challenge ?? "",
  voice_feedback: user?.preferences?.voice_feedback ?? true,
  current_password: "",
  new_password: "",
  confirm_new_password: "",
});

const parseCommaSeparated = (value) => {
  const entries = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return entries.length ? entries : null;
};

const buildProfilePayload = (formData, user) => ({
  display_name: formData.display_name.trim() || null,
  age: formData.age === "" ? null : Number(formData.age),
  native_language: formData.native_language || null,
  target_language: formData.target_language || null,
  level: formData.level || null,
  daily_goal: formData.daily_goal === "" ? null : Number(formData.daily_goal),
  learning_purpose: parseCommaSeparated(formData.learning_purpose),
  favorite_topics: parseCommaSeparated(formData.favorite_topics),
  main_challenge: formData.main_challenge.trim() || null,
  preferences: {
    ...(user?.preferences ?? {}),
    voice_feedback: formData.voice_feedback,
  },
});

const FieldLabel = ({ children }) => (
  <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
    {children}
  </label>
);

const ProfileEditorCard = ({ onClose, onSuccess }) => {
  const { user, updateProfile, changePassword } = useAuth();
  const [formData, setFormData] = useState(() => toFormState(user));
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const requiresCurrentPassword = Boolean(user?.has_password);

  const baselineForm = useMemo(() => toFormState(user), [user]);
  const profilePayload = useMemo(() => buildProfilePayload(formData, user), [formData, user]);
  const baselinePayload = useMemo(() => buildProfilePayload(baselineForm, user), [baselineForm, user]);

  useEffect(() => {
    setFormData(toFormState(user));
  }, [user]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleEscape = (event) => {
      if (event.key === "Escape" && !isSaving) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isSaving, onClose]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError("");
  };

  const handleReset = () => {
    setFormData(toFormState(user));
    setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setError("");

    const hasPasswordInput =
      Boolean(formData.new_password) ||
      Boolean(formData.confirm_new_password) ||
      (requiresCurrentPassword && Boolean(formData.current_password));
    const hasProfileChanges = JSON.stringify(profilePayload) !== JSON.stringify(baselinePayload);

    if (!hasPasswordInput && !hasProfileChanges) {
      setError("Please update at least one field before saving.");
      setIsSaving(false);
      return;
    }

    if (hasPasswordInput) {
      if (!formData.new_password || !formData.confirm_new_password) {
        setError("Please fill in the new password fields.");
        setIsSaving(false);
        return;
      }

      if (requiresCurrentPassword && !formData.current_password) {
        setError("Please enter your current password.");
        setIsSaving(false);
        return;
      }

      if (formData.new_password !== formData.confirm_new_password) {
        setError("New password confirmation does not match.");
        setIsSaving(false);
        return;
      }
    }

    try {
      if (hasPasswordInput) {
        await changePassword({
          ...(requiresCurrentPassword ? { current_password: formData.current_password } : {}),
          new_password: formData.new_password,
        });
      }

      if (hasProfileChanges) {
        await updateProfile(profilePayload);
      }

      const successMessage =
        hasPasswordInput && hasProfileChanges
          ? "Profile and password updated successfully."
          : hasPasswordInput
            ? requiresCurrentPassword
              ? "Password updated successfully."
              : "Password set successfully."
            : "Profile updated successfully.";

      onSuccess?.(successMessage);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save your changes right now.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/45 p-4 backdrop-blur-sm sm:p-6"
      onClick={() => {
        if (!isSaving) {
          onClose();
        }
      }}
    >
      <motion.section
        role="dialog"
        aria-modal="true"
        aria-label="Edit profile"
        initial={{ opacity: 0, y: 24, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        onClick={(event) => event.stopPropagation()}
        className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-[2rem] border border-white/70 bg-white p-6 shadow-2xl shadow-zinc-950/15 sm:p-8"
      >
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-primary">
              <Sparkle weight="fill" size={12} />
              Profile Editor
            </div>
            <h3 className="text-2xl font-black tracking-tight text-zinc-950 font-display">
              Update your learning profile
            </h3>
            <p className="mt-2 max-w-2xl text-sm text-zinc-500">
              Edit your profile details, then optionally {requiresCurrentPassword ? "change" : "set"} your password before saving everything in one step.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center gap-2 self-start rounded-2xl bg-zinc-100 px-4 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 transition-colors hover:bg-zinc-200"
          >
            <X weight="bold" size={14} />
            Close
          </button>
        </div>

        <form className="mt-8 space-y-8" onSubmit={handleSubmit}>
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-xs font-bold text-rose-600">
              {error}
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <FieldLabel>Display Name</FieldLabel>
              <input
                type="text"
                value={formData.display_name}
                onChange={(event) => handleChange("display_name", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
                placeholder="How should we call you?"
              />
            </div>

            <div>
              <FieldLabel>Age</FieldLabel>
              <input
                type="number"
                min="1"
                max="120"
                value={formData.age}
                onChange={(event) => handleChange("age", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
                placeholder="Optional"
              />
            </div>

            <div>
              <FieldLabel>Native Language</FieldLabel>
              <select
                value={formData.native_language}
                onChange={(event) => handleChange("native_language", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
              >
                {LANGUAGE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Target Language</FieldLabel>
              <select
                value={formData.target_language}
                onChange={(event) => handleChange("target_language", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
              >
                {LANGUAGE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Current Level</FieldLabel>
              <select
                value={formData.level}
                onChange={(event) => handleChange("level", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
              >
                {LEVEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Daily Goal (Minutes)</FieldLabel>
              <input
                type="number"
                min="1"
                max="1440"
                value={formData.daily_goal}
                onChange={(event) => handleChange("daily_goal", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <FieldLabel>Learning Purpose</FieldLabel>
              <input
                type="text"
                value={formData.learning_purpose}
                onChange={(event) => handleChange("learning_purpose", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
                placeholder="Career growth, travel, IELTS, interviews..."
              />
            </div>

            <div>
              <FieldLabel>Favorite Topics</FieldLabel>
              <input
                type="text"
                value={formData.favorite_topics}
                onChange={(event) => handleChange("favorite_topics", event.target.value)}
                className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
                placeholder="Music, travel, business, technology"
              />
            </div>
          </div>

          <div>
            <FieldLabel>Main Challenge</FieldLabel>
            <textarea
              rows="4"
              value={formData.main_challenge}
              onChange={(event) => handleChange("main_challenge", event.target.value)}
              className="w-full rounded-[1.5rem] border border-zinc-200 bg-zinc-50 px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
              placeholder="Describe the hardest part of your speaking practice right now."
            />
          </div>

          <div className="flex items-center justify-between rounded-[1.75rem] border border-zinc-200 bg-zinc-50 px-5 py-4">
            <div>
              <p className="text-sm font-bold text-zinc-950">Voice Feedback</p>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
                Real-time speaking corrections
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleChange("voice_feedback", !formData.voice_feedback)}
              className={`relative h-7 w-14 rounded-full p-1 transition-colors ${
                formData.voice_feedback ? "bg-emerald-500" : "bg-zinc-300"
              }`}
            >
              <motion.span
                animate={{ x: formData.voice_feedback ? 28 : 0 }}
                className="block h-5 w-5 rounded-full bg-white shadow-sm"
              />
            </button>
          </div>

          <div className="rounded-[1.75rem] border border-zinc-200 bg-zinc-50/70 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <LockKey size={20} weight="bold" />
              </div>
              <div>
                <p className="text-sm font-black text-zinc-950">
                  {requiresCurrentPassword ? "Change Password" : "Set Password"}
                </p>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
                  {requiresCurrentPassword ? "Optional security update" : "Add a password to this account"}
                </p>
              </div>
            </div>

            <div className={`mt-5 grid grid-cols-1 gap-4 ${requiresCurrentPassword ? "lg:grid-cols-3" : "lg:grid-cols-2"}`}>
              {requiresCurrentPassword ? (
                <div>
                  <FieldLabel>Current Password</FieldLabel>
                  <input
                    type="password"
                    value={formData.current_password}
                    onChange={(event) => handleChange("current_password", event.target.value)}
                    className="w-full rounded-[1.5rem] border border-zinc-200 bg-white px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/10"
                    placeholder="Enter current password"
                  />
                </div>
              ) : null}

              <div>
                <FieldLabel>New Password</FieldLabel>
                <input
                  type="password"
                  value={formData.new_password}
                  onChange={(event) => handleChange("new_password", event.target.value)}
                  className="w-full rounded-[1.5rem] border border-zinc-200 bg-white px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/10"
                  placeholder={requiresCurrentPassword ? "Enter new password" : "Create a password"}
                />
              </div>

              <div>
                <FieldLabel>Confirm New Password</FieldLabel>
                <input
                  type="password"
                  value={formData.confirm_new_password}
                  onChange={(event) => handleChange("confirm_new_password", event.target.value)}
                  className="w-full rounded-[1.5rem] border border-zinc-200 bg-white px-5 py-4 text-sm font-bold text-zinc-950 outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/10"
                  placeholder="Repeat new password"
                />
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 border-t border-zinc-100 pt-6 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-zinc-100 px-5 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-600 transition-colors hover:bg-zinc-200"
            >
              <ArrowsCounterClockwise weight="bold" size={14} />
              Reset
            </button>

            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-6 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20 transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <FloppyDiskBack weight="bold" size={14} />
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </motion.section>
    </div>
  );
};

export default ProfileEditorCard;
