import { useState } from "react";
import { Sparkle, X, Image as ImageIcon, UploadSimple } from "@phosphor-icons/react";
import { adminApi } from "../api/adminScenariosApi";

import ListEditorField from "./ListEditorField";
import { getApiErrorMessage } from "@/shared/api/httpClient";

const prettyList = (value) => (Array.isArray(value) ? value.join("\n") : "");
const parseListInput = (value = "") =>
  value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

const createInitialState = (scenario) => ({
  title: scenario?.title || "",
  description: scenario?.description || "",
  category: scenario?.category || "travel",
  difficulty: scenario?.difficulty || "medium",
  ai_role: scenario?.ai_role || "",
  user_role: scenario?.user_role || "",
  tasks: prettyList(scenario?.tasks),
  ai_system_prompt: scenario?.ai_system_prompt || "",
  tags: prettyList(scenario?.tags),
  estimated_duration_minutes: scenario?.estimated_duration_minutes || 10,
  character_id: scenario?.character_id || scenario?.character?.id || "",
  is_active: scenario?.is_active ?? true,
  is_pro: scenario?.is_pro ?? false,
  image_url: scenario?.image_url || "",
});

const ScenarioEditorModal = ({
  scenario,
  onClose,
  onSubmit,
  onGeneratePrompt,
  characters = [],
  isSaving,
}) => {
  const [form, setForm] = useState(() => createInitialState(scenario));
  const [formError, setFormError] = useState("");
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      const data = await adminApi.uploadImage(file);
      if (data.url) {
        updateField("image_url", data.url);
      }
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Failed to upload image."));
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      if (!form.ai_system_prompt.trim()) {
        setFormError("Generate or enter a system prompt before saving.");
        return;
      }
      if (form.is_active && !form.character_id) {
        setFormError("Select a character before activating this scenario.");
        return;
      }

      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category.trim(),
        difficulty: form.difficulty,
        ai_role: form.ai_role.trim(),
        user_role: form.user_role.trim(),
        tasks: parseListInput(form.tasks),
        ai_system_prompt: form.ai_system_prompt.trim(),
        tags: parseListInput(form.tags),
        estimated_duration_minutes: Number(form.estimated_duration_minutes),
        character_id: form.character_id ? Number(form.character_id) : null,
        is_active: form.is_active,
        is_pro: form.is_pro,
        image_url: form.image_url || null,
      };

      setFormError("");
      await onSubmit(payload);
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Please check the form before saving."));
    }
  };

  const handleGeneratePrompt = async () => {
    try {
      setIsGeneratingPrompt(true);
      const generated = await onGeneratePrompt({
        title: form.title,
        description: form.description,
        ai_role: form.ai_role.trim(),
        user_role: form.user_role.trim(),
        tasks: parseListInput(form.tasks),
      });
      updateField("ai_system_prompt", generated.prompt || "");
      setFormError("");
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Failed to generate default prompt."));
    } finally {
      setIsGeneratingPrompt(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[120] bg-zinc-950/60 p-3 backdrop-blur md:p-6">
      <div className="mx-auto flex h-full max-w-5xl flex-col overflow-hidden rounded-[24px] border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
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
            className="rounded-xl border border-zinc-200 p-2 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="grid min-h-0 flex-1">
          <div className="min-h-0 overflow-y-auto p-5 md:p-6">
            <div className="space-y-5">
              {formError ? (
                <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                  {formError}
                </div>
              ) : null}

              <section className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 md:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Title</span>
                    <input
                      required
                      value={form.title}
                      onChange={(event) => updateField("title", event.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Hotel check-in problem"
                    />
                  </label>

                  <label className="block space-y-2 md:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Scenario brief</span>
                    <textarea
                      required
                      value={form.description}
                      onChange={(event) => updateField("description", event.target.value)}
                      rows={4}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Describe the situation the learner will face."
                    />
                  </label>

                  <label className="block space-y-2 md:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                      <ImageIcon size={16} /> Cover Image
                    </span>
                    <div className="flex items-center gap-4">
                      {form.image_url && (
                        <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg border border-zinc-200">
                          <img src={form.image_url.startsWith('http') ? form.image_url : `http://localhost:8000${form.image_url}`} alt="Scenario Cover" className="h-full w-full object-cover" />
                        </div>
                      )}
                      <div className="relative flex-1">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          disabled={isUploading}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                        />
                        <div className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 bg-zinc-50 px-4 py-3 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900/50 dark:text-zinc-400">
                          <UploadSimple size={18} />
                          {isUploading ? "Uploading..." : "Click to upload an image"}
                        </div>
                      </div>
                    </div>
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Category</span>
                    <input
                      value={form.category}
                      onChange={(event) => updateField("category", event.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="travel"
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Difficulty</span>
                    <select
                      value={form.difficulty}
                      onChange={(event) => updateField("difficulty", event.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </label>

                  <label className="block space-y-2 md:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Character</span>
                    <select
                      value={form.character_id}
                      onChange={(event) => updateField("character_id", event.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    >
                      <option value="">No character selected</option>
                      {characters.map((character) => (
                        <option key={character.id} value={character.id}>
                          {character.name} · {character.tts_voice}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </section>

              <section className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2">
                  <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">AI role</span>
                  <input
                    value={form.ai_role}
                    onChange={(event) => updateField("ai_role", event.target.value)}
                    className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    placeholder="Hotel front desk agent"
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Learner role</span>
                  <input
                    value={form.user_role}
                    onChange={(event) => updateField("user_role", event.target.value)}
                    className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    placeholder="Traveler checking in"
                  />
                </label>
              </section>

              <section>
                <ListEditorField
                  label="Nhiệm vụ người học cần hoàn thành"
                  value={form.tasks}
                  onChange={(value) => updateField("tasks", value)}
                  helperText="Mỗi dòng là một nhiệm vụ. Hội thoại chỉ nên kết thúc khi người học đã hoàn thành các nhiệm vụ này."
                  placeholder={"Nói tên của bạn\nNói tuổi của bạn\nNói quê quán của bạn"}
                  rows={6}
                />
              </section>

              <section className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">System prompt</p>
                    <p className="mt-1 text-sm text-zinc-500">Prompt mà AI sẽ dùng trong kịch bản này.</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleGeneratePrompt}
                    disabled={isGeneratingPrompt}
                    className="inline-flex items-center gap-2 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-bold text-zinc-700 transition hover:bg-zinc-100 disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <Sparkle size={14} />
                    {isGeneratingPrompt ? "Generating..." : "Generate"}
                  </button>
                </div>
                <textarea
                  value={form.ai_system_prompt}
                  onChange={(event) => updateField("ai_system_prompt", event.target.value)}
                  rows={9}
                  className="w-full rounded-xl border border-zinc-200 bg-zinc-950 px-4 py-4 font-mono text-sm text-emerald-200 outline-none transition focus:border-primary dark:border-zinc-700"
                  placeholder="Generate or write the system prompt before saving."
                />
              </section>

              <section className="grid gap-4 md:grid-cols-2">
                <ListEditorField
                  label="Tags"
                  value={form.tags}
                  onChange={(value) => updateField("tags", value)}
                  helperText="Dùng cho tìm kiếm và lọc."
                  placeholder={"travel\nhotel\nbeginner"}
                  rows={3}
                />

                <div className="space-y-4">
                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Max time</span>
                    <input
                      type="number"
                      min="1"
                      max="180"
                      value={form.estimated_duration_minutes}
                      onChange={(event) => updateField("estimated_duration_minutes", event.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    />
                  </label>

                  <label className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(event) => updateField("is_active", event.target.checked)}
                    />
                    <span className="text-sm font-semibold">Active</span>
                  </label>

                  <label className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                    <input
                      type="checkbox"
                      checked={form.is_pro}
                      onChange={(event) => updateField("is_pro", event.target.checked)}
                    />
                    <span className="text-sm font-semibold">VIP only</span>
                  </label>
                </div>
              </section>

            </div>
          </div>

          <div className="flex items-center justify-between gap-3 border-t border-zinc-200 px-5 py-4 dark:border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
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
