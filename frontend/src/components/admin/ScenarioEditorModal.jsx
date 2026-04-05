import { useState } from "react";
import { X, Sparkle, ClockCounterClockwise } from "@phosphor-icons/react";
import JsonEditorField from "./JsonEditorField";
import PromptQualityBadge from "./PromptQualityBadge";

const prettyJson = (value, fallback) => JSON.stringify(value ?? fallback, null, 2);

const createInitialState = (scenario) => ({
  title: scenario?.title || "",
  description: scenario?.description || "",
  category: scenario?.category || "travel",
  difficulty: scenario?.difficulty || "medium",
  ai_system_prompt: scenario?.ai_system_prompt || "",
  estimated_duration_minutes: scenario?.estimated_duration_minutes || 10,
  is_pre_generated: scenario?.is_pre_generated ?? true,
  pre_gen_count: scenario?.pre_gen_count || 8,
  mode: scenario?.mode || "conversation",
  is_active: scenario?.is_active ?? true,
  change_note: "",
  learning_objectives: prettyJson(scenario?.learning_objectives, []),
  target_skills: prettyJson(scenario?.target_skills, []),
  tags: prettyJson(scenario?.tags, []),
  metadata: prettyJson(scenario?.metadata, {}),
});

const ScenarioEditorModal = ({
  scenario,
  promptHistory = [],
  onClose,
  onSubmit,
  onSuggestSkills,
  isSaving,
}) => {
  const [form, setForm] = useState(() => createInitialState(scenario));
  const [jsonError, setJsonError] = useState("");

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const payload = {
        ...form,
        estimated_duration_minutes: Number(form.estimated_duration_minutes),
        pre_gen_count: Number(form.pre_gen_count),
        learning_objectives: JSON.parse(form.learning_objectives || "[]"),
        target_skills: JSON.parse(form.target_skills || "[]"),
        tags: JSON.parse(form.tags || "[]"),
        metadata: JSON.parse(form.metadata || "{}"),
      };
      setJsonError("");
      await onSubmit(payload);
    } catch (error) {
      setJsonError(error.message || "JSON fields must be valid before saving.");
    }
  };

  const handleSkillSuggestion = async () => {
    const suggested = await onSuggestSkills({
      description: form.description,
      category: form.category,
    });
    updateField("target_skills", prettyJson(suggested, []));
  };

  return (
    <div className="fixed inset-0 z-[120] bg-zinc-950/60 p-3 backdrop-blur md:p-6">
      <div className="mx-auto flex h-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">
              {scenario ? "Edit Scenario" : "Create Scenario"}
            </p>
            <h2 className="mt-1 font-display text-2xl font-black tracking-tight">
              {scenario ? scenario.title : "New Scenario"}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-2xl border border-zinc-200 p-2 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="grid min-h-0 flex-1 gap-0 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="min-h-0 overflow-y-auto p-5 md:p-6">
            <div className="grid gap-5 xl:grid-cols-2">
              <label className="block space-y-2 xl:col-span-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Title
                </span>
                <input
                  required
                  value={form.title}
                  onChange={(event) => updateField("title", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                />
              </label>

              <label className="block space-y-2 xl:col-span-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Scenario Brief
                </span>
                <textarea
                  required
                  value={form.description}
                  onChange={(event) => updateField("description", event.target.value)}
                  rows={4}
                  className="w-full rounded-[24px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                  placeholder="Describe the learner context, who they are speaking with, and the outcome they should reach."
                />
              </label>

              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Category
                </span>
                <input
                  value={form.category}
                  onChange={(event) => updateField("category", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                />
              </label>

              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Difficulty
                </span>
                <select
                  value={form.difficulty}
                  onChange={(event) => updateField("difficulty", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </label>

              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Mode
                </span>
                <select
                  value={form.mode}
                  onChange={(event) => updateField("mode", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                >
                  {["conversation", "roleplay", "debate", "interview", "presentation"].map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Duration (minutes)
                </span>
                <input
                  type="number"
                  min="1"
                  max="180"
                  value={form.estimated_duration_minutes}
                  onChange={(event) => updateField("estimated_duration_minutes", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                />
              </label>

              <div className="grid gap-4 xl:col-span-2 md:grid-cols-3">
                <label className="flex items-center gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(event) => updateField("is_active", event.target.checked)}
                  />
                  <span className="text-sm font-semibold">Active</span>
                </label>
                <label className="flex items-center gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                  <input
                    type="checkbox"
                    checked={form.is_pre_generated}
                    onChange={(event) => updateField("is_pre_generated", event.target.checked)}
                  />
                  <span className="text-sm font-semibold">Pre-generate variations</span>
                </label>
                <label className="block space-y-2 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                  <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                    Target pre-gen count
                  </span>
                  <input
                    type="number"
                    min="0"
                    max="30"
                    value={form.pre_gen_count}
                    onChange={(event) => updateField("pre_gen_count", event.target.value)}
                    className="w-full rounded-2xl border border-zinc-200 bg-white px-3 py-2 text-sm font-medium outline-none dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </label>
              </div>

              <div className="xl:col-span-2">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                    AI System Prompt
                  </span>
                  <button
                    type="button"
                    onClick={handleSkillSuggestion}
                    className="inline-flex items-center gap-2 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <Sparkle size={14} />
                    Suggest skills
                  </button>
                </div>
                <textarea
                  required
                  value={form.ai_system_prompt}
                  onChange={(event) => updateField("ai_system_prompt", event.target.value)}
                  rows={12}
                  className="w-full rounded-[28px] border border-zinc-200 bg-zinc-950 px-4 py-4 font-mono text-sm text-emerald-200 outline-none transition focus:border-primary dark:border-zinc-700"
                  placeholder="You are a patient but realistic conversation partner..."
                />
              </div>

              <JsonEditorField
                label="Learning Objectives"
                value={form.learning_objectives}
                onChange={(value) => updateField("learning_objectives", value)}
                helperText="Array of teacher-facing objectives."
              />
              <JsonEditorField
                label="Target Skills"
                value={form.target_skills}
                onChange={(value) => updateField("target_skills", value)}
                helperText="Array of skills such as pronunciation, fluency, grammar."
              />
              <JsonEditorField
                label="Tags"
                value={form.tags}
                onChange={(value) => updateField("tags", value)}
                helperText="Array used for filtering and discovery."
              />
              <JsonEditorField
                label="Metadata"
                value={form.metadata}
                onChange={(value) => updateField("metadata", value)}
                placeholder="{}"
                helperText="Flexible extension bag for personas, vocabulary, or extra routing hints."
              />

              <label className="block space-y-2 xl:col-span-2">
                <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                  Change Note
                </span>
                <input
                  value={form.change_note}
                  onChange={(event) => updateField("change_note", event.target.value)}
                  className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                  placeholder="Why did this prompt or scenario change?"
                />
              </label>
            </div>
          </div>

          <aside className="min-h-0 overflow-y-auto border-t border-zinc-200 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 lg:border-l lg:border-t-0">
            <PromptQualityBadge quality={scenario?.latest_prompt_quality} />

            {jsonError && (
              <div className="mt-4 rounded-[24px] bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                {jsonError}
              </div>
            )}

            <div className="mt-5 rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <div className="flex items-center gap-2">
                <ClockCounterClockwise size={16} className="text-zinc-500" />
                <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                  Prompt History
                </p>
              </div>
              <div className="mt-4 space-y-3">
                {promptHistory.length === 0 && (
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">No prompt revisions yet.</p>
                )}
                {promptHistory.map((entry) => (
                  <div key={entry.id} className="rounded-[22px] border border-zinc-200 p-3 dark:border-zinc-800">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">{entry.change_note || "Prompt update"}</p>
                      <span className="rounded-full bg-zinc-100 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                        {entry.quality_score ?? "NA"}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                Admin Notes
              </p>
              <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
                <li>Keep scenarios reusable across many learners.</li>
                <li>Put skill-specific guidance in the prompt, not only the description.</li>
                <li>Use metadata for persona and vocabulary hints instead of prompt clutter.</li>
              </ul>
            </div>
          </aside>

          <div className="flex items-center justify-between gap-3 border-t border-zinc-200 px-5 py-4 dark:border-zinc-800 lg:col-span-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-2xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? "Saving..." : scenario ? "Save Scenario" : "Create Scenario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScenarioEditorModal;
