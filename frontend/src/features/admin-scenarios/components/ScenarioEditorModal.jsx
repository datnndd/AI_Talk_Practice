import { useCallback, useEffect, useRef, useState } from "react";
import { X, Image as ImageIcon, UploadSimple } from "@phosphor-icons/react";
import ListEditorField from "./ListEditorField";
import { getApiBaseUrl, getApiErrorMessage } from "@/shared/api/httpClient";

const prettyList = (value) => (Array.isArray(value) ? value.join("\n") : "");
const parseListInput = (value = "") =>
  value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

const getFullImageUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  const host = getApiBaseUrl().replace(/\/api\/?$/, "");
  return `${host}${url}`;
};

const createInitialState = (scenario) => ({
  title: scenario?.title || "",
  description: scenario?.description || "",
  category: scenario?.category || "travel",
  difficulty: scenario?.difficulty || "medium",
  ai_role: scenario?.ai_role || "",
  user_role: scenario?.user_role || "",
  tasks: prettyList(scenario?.tasks),
  tags: prettyList(scenario?.tags),
  time_limit_minutes: scenario?.time_limit_minutes || 10,
  character_id: scenario?.character_id || scenario?.character?.id || "",
  is_active: scenario?.is_active ?? true,
  is_pro: scenario?.is_pro ?? false,
  image_url: scenario?.image_url || "",
});

const ScenarioEditorModal = ({
  scenario,
  onClose,
  onSubmit,
  characters = [],
  isSaving,
}) => {
  const [form, setForm] = useState(() => createInitialState(scenario));
  const [formError, setFormError] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState("");
  const imagePreviewUrlRef = useRef("");

  const clearImagePreview = useCallback(() => {
    if (imagePreviewUrlRef.current) {
      URL.revokeObjectURL(imagePreviewUrlRef.current);
      imagePreviewUrlRef.current = "";
    }
    setImagePreviewUrl("");
  }, []);

  useEffect(() => clearImagePreview, [clearImagePreview]);

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleImageSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    clearImagePreview();
    const nextPreviewUrl = URL.createObjectURL(file);
    imagePreviewUrlRef.current = nextPreviewUrl;
    setImageFile(file);
    setImagePreviewUrl(nextPreviewUrl);
    setFormError("");
    event.target.value = "";
  };

  const coverImageUrl = imagePreviewUrl || getFullImageUrl(form.image_url);

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
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
        tags: parseListInput(form.tags),
        time_limit_minutes: Number(form.time_limit_minutes),
        character_id: form.character_id ? Number(form.character_id) : null,
        is_active: form.is_active,
        is_pro: form.is_pro,
        image_url: form.image_url || null,
      };

      setFormError("");
      await onSubmit(payload, imageFile);
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Please check the form before saving."));
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
                      {coverImageUrl && (
                        <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg border border-zinc-200">
                          <img src={coverImageUrl} alt="Scenario Cover" className="h-full w-full object-cover" />
                        </div>
                      )}
                      <div className="relative flex-1">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          disabled={isSaving}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                        />
                        <div className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 bg-zinc-50 px-4 py-3 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-900/50 dark:text-zinc-400">
                          <UploadSimple size={18} />
                          {imageFile ? "Image selected. Uploads when saved." : "Click to choose an image"}
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

              <section className="grid gap-4 md:grid-cols-2">
                <ListEditorField
                  label="Tags"
                  value={form.tags}
                  onChange={(value) => updateField("tags", value)}
                  helperText="Dùng cho tìm kiếm và lọc."
                  placeholder={"travel\\nhotel\\nA1"}
                  rows={3}
                />

                <div className="space-y-4">
                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Max time</span>
                    <input
                      type="number"
                      min="1"
                      max="180"
                      value={form.time_limit_minutes}
                      onChange={(event) => updateField("time_limit_minutes", event.target.value)}
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
