import { useState } from "react";
import { Plus, Sparkle, X } from "@phosphor-icons/react";
import JsonEditorField from "./JsonEditorField";

const initialVariationForm = (scenarioId, variation) => ({
  scenario_id: scenarioId,
  variation_name: variation?.variation_name || "",
  parameters: JSON.stringify(variation?.parameters ?? {}, null, 2),
  sample_prompt: variation?.sample_prompt || "",
  sample_conversation: JSON.stringify(variation?.sample_conversation ?? [], null, 2),
  system_prompt_override: variation?.system_prompt_override || "",
  is_active: variation?.is_active ?? true,
  is_pregenerated: variation?.is_pregenerated ?? false,
  is_approved: variation?.is_approved ?? false,
});

const VariationEditorModal = ({ scenarioId, variation, onClose, onSubmit, isSaving }) => {
  const [form, setForm] = useState(initialVariationForm(scenarioId, variation));
  const [error, setError] = useState("");

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const payload = {
        ...form,
        parameters: JSON.parse(form.parameters || "{}"),
        sample_conversation: JSON.parse(form.sample_conversation || "[]"),
      };
      setError("");
      await onSubmit(payload);
    } catch (submitError) {
      setError(submitError.message || "Variation JSON is invalid.");
    }
  };

  return (
    <div className="fixed inset-0 z-[130] bg-zinc-950/60 p-4 backdrop-blur">
      <div className="mx-auto max-w-4xl rounded-[32px] border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">
              {variation ? "Edit Variation" : "Create Variation"}
            </p>
            <h3 className="mt-1 font-display text-2xl font-black tracking-tight">
              {variation?.variation_name || "New variation"}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-2xl border border-zinc-200 p-2 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-5">
          <label className="block space-y-2">
            <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
              Variation Name
            </span>
            <input
              required
              value={form.variation_name}
              onChange={(event) => updateField("variation_name", event.target.value)}
              className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>

          <div className="grid gap-5 lg:grid-cols-2">
            <JsonEditorField
              label="Parameters"
              value={form.parameters}
              onChange={(value) => updateField("parameters", value)}
              placeholder="{}"
              helperText="The structured attributes that differentiate this variation."
            />
            <JsonEditorField
              label="Sample Conversation"
              value={form.sample_conversation}
              onChange={(value) => updateField("sample_conversation", value)}
              helperText="Preview transcript shown to teachers before approval."
            />
          </div>

          <label className="block space-y-2">
            <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
              Sample Prompt
            </span>
            <textarea
              value={form.sample_prompt}
              onChange={(event) => updateField("sample_prompt", event.target.value)}
              rows={3}
              className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>

          <label className="block space-y-2">
            <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
              System Prompt Override
            </span>
            <textarea
              value={form.system_prompt_override}
              onChange={(event) => updateField("system_prompt_override", event.target.value)}
              rows={5}
              className="w-full rounded-[22px] border border-zinc-200 bg-zinc-950 px-4 py-3 font-mono text-sm text-emerald-200 outline-none transition focus:border-primary dark:border-zinc-700"
            />
          </label>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["is_active", "Active"],
              ["is_pregenerated", "Pre-generated"],
              ["is_approved", "Approved"],
            ].map(([field, label]) => (
              <label
                key={field}
                className="flex items-center gap-3 rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold dark:border-zinc-800 dark:bg-zinc-900"
              >
                <input
                  type="checkbox"
                  checked={form[field]}
                  onChange={(event) => updateField(field, event.target.checked)}
                />
                {label}
              </label>
            ))}
          </div>

          {error && (
            <div className="rounded-[22px] bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3">
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
              {isSaving ? "Saving..." : variation ? "Save Variation" : "Create Variation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const VariationPanel = ({
  scenario,
  variations,
  search,
  onSearchChange,
  onCreateVariation,
  onUpdateVariation,
  onDeleteVariation,
  onGenerateVariations,
  generationTask,
  isLoading,
}) => {
  const [editingVariation, setEditingVariation] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [previewVariation, setPreviewVariation] = useState(null);

  if (!scenario) {
    return (
      <div className="rounded-[28px] border border-dashed border-zinc-300 bg-white/70 p-8 text-center text-sm text-zinc-500 shadow-sm dark:border-zinc-700 dark:bg-zinc-900/60 dark:text-zinc-400">
        Select a scenario to review its prompt history and variation set.
      </div>
    );
  }

  const openCreateModal = () => {
    setEditingVariation(null);
    setIsModalOpen(true);
  };

  const openEditModal = (variation) => {
    setEditingVariation(variation);
    setIsModalOpen(true);
  };

  const handleSaveVariation = async (payload) => {
    setIsSaving(true);
    try {
      if (editingVariation) {
        await onUpdateVariation(editingVariation.id, payload);
      } else {
        await onCreateVariation(payload);
      }
      setIsModalOpen(false);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900" id="generation-queue">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Variation Library</p>
            <h3 className="mt-1 font-display text-2xl font-black tracking-tight">{scenario.title}</h3>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
              Manage pre-generated and dynamic variations for this teaching scenario.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onGenerateVariations(scenario.id)}
              className="inline-flex items-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5"
            >
              <Sparkle size={16} />
              Generate Variations
            </button>
            <button
              type="button"
              onClick={openCreateModal}
              className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            >
              <Plus size={16} />
              New Variation
            </button>
          </div>
        </div>

        {generationTask && (
          <div className="mt-4 rounded-[24px] bg-zinc-100 px-4 py-3 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
            <div className="flex items-center justify-between gap-3">
              <span className="font-semibold">Task {generationTask.task_id.slice(0, 8)}</span>
              <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-700 dark:bg-zinc-950 dark:text-zinc-200">
                {generationTask.status}
              </span>
            </div>
            <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
              Created {generationTask.created_count} • Skipped {generationTask.skipped_count}
            </p>
          </div>
        )}

        <div className="mt-5">
          <input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search by variation name, prompt, or parameters..."
            className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>

        <div className="mt-5 overflow-hidden rounded-[24px] border border-zinc-200 dark:border-zinc-800">
          <div className="grid grid-cols-[minmax(0,1.2fr)_130px_130px_110px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
            <span>Variation</span>
            <span>Type</span>
            <span>Usage</span>
            <span className="text-right">Actions</span>
          </div>

          <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {isLoading && (
              <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading variations...</div>
            )}

            {!isLoading && variations.length === 0 && (
              <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">No variations found for this scenario.</div>
            )}

            {!isLoading &&
              variations.map((variation) => (
                <div
                  key={variation.id}
                  className="grid grid-cols-[minmax(0,1.2fr)_130px_130px_110px] gap-3 px-4 py-4 text-sm"
                >
                  <div className="min-w-0">
                    <button
                      type="button"
                      onClick={() => setPreviewVariation(variation)}
                      className="truncate text-left font-semibold text-zinc-900 transition hover:text-primary dark:text-zinc-100"
                    >
                      {variation.variation_name}
                    </button>
                    <p className="mt-1 truncate text-xs text-zinc-500 dark:text-zinc-400">
                      {variation.sample_prompt || "No sample prompt"}
                    </p>
                  </div>
                  <div>
                    <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                      {variation.is_pregenerated ? "Pre-gen" : "Dynamic"}
                    </span>
                  </div>
                  <div className="text-zinc-600 dark:text-zinc-300">{variation.usage_count} uses</div>
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => openEditModal(variation)}
                      className="text-xs font-bold text-primary"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteVariation(variation.id)}
                      className="text-xs font-bold text-rose-600 dark:text-rose-300"
                    >
                      Disable
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      <aside className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Sample Preview</p>
        <h3 className="mt-1 font-display text-2xl font-black tracking-tight">
          {previewVariation?.variation_name || "Select a variation"}
        </h3>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          {previewVariation?.sample_prompt || "Open a variation to inspect its prompt and conversation sample."}
        </p>

        <div className="mt-5 space-y-3">
          {(previewVariation?.sample_conversation || []).map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`rounded-[22px] px-4 py-3 text-sm ${
                message.role === "assistant"
                  ? "bg-primary/10 text-zinc-800 dark:text-zinc-100"
                  : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              }`}
            >
              <p className="mb-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                {message.role}
              </p>
              <p>{message.content}</p>
            </div>
          ))}
        </div>

        {previewVariation?.parameters && (
          <div className="mt-5 rounded-[24px] border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
              Parameters
            </p>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-zinc-700 dark:text-zinc-200">
              {JSON.stringify(previewVariation.parameters, null, 2)}
            </pre>
          </div>
        )}
      </aside>

      {isModalOpen && (
        <VariationEditorModal
          key={editingVariation?.id || `new-${scenario.id}`}
          scenarioId={scenario.id}
          variation={editingVariation}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleSaveVariation}
          isSaving={isSaving}
        />
      )}
    </section>
  );
};

export default VariationPanel;
