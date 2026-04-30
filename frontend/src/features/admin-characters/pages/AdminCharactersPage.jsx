import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowCounterClockwise, PencilSimple, Plus, Trash, X } from "@phosphor-icons/react";

import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import { adminCharactersApi } from "@/features/admin-characters/api/adminCharactersApi";
import { getApiErrorMessage } from "@/shared/api/httpClient";

const DEFAULT_MODEL_URL = "https://rgpmptospjqospitmcqw.supabase.co/storage/v1/object/public/live2d-models/ai-tutor/pachirisu%20anime%20girl%20-%20top%20half.model3.json";
const DEFAULT_CORE_URL = "https://rgpmptospjqospitmcqw.supabase.co/storage/v1/object/public/live2d-models/live2dcubismcore.min.js";

const createInitialForm = (character) => ({
  name: character?.name || "",
  description: character?.description || "",
  model_url: character?.model_url || DEFAULT_MODEL_URL,
  core_url: character?.core_url || DEFAULT_CORE_URL,
  thumbnail_url: character?.thumbnail_url || "",
  tts_voice: character?.tts_voice || "Cherry",
  tts_language: character?.tts_language || "en",
  sort_order: character?.sort_order ?? 0,
  is_active: character?.is_active ?? true,
});

const StatusBadge = ({ children, tone = "zinc" }) => {
  const tones = {
    emerald: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
    rose: "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
    zinc: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  };
  return (
    <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${tones[tone]}`}>
      {children}
    </span>
  );
};

const CharacterEditorModal = ({ character, onClose, onSubmit, isSaving }) => {
  const [form, setForm] = useState(() => createInitialForm(character));
  const [formError, setFormError] = useState("");
  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await onSubmit({
        name: form.name.trim(),
        description: form.description.trim() || null,
        model_url: form.model_url.trim(),
        core_url: form.core_url.trim(),
        thumbnail_url: form.thumbnail_url.trim() || null,
        tts_voice: form.tts_voice.trim(),
        tts_language: form.tts_language.trim(),
        sort_order: Number(form.sort_order || 0),
        is_active: form.is_active,
        metadata: {},
      });
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Please check the character form."));
    }
  };

  return (
    <div className="fixed inset-0 z-[120] bg-zinc-950/60 p-3 backdrop-blur md:p-6">
      <div className="mx-auto flex h-full max-w-3xl flex-col overflow-hidden rounded-[24px] border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">
              {character ? "Edit Character" : "Create Character"}
            </p>
            <h2 className="mt-1 font-display text-2xl font-black tracking-tight">
              {character ? character.name : "New Character"}
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

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-5 md:p-6">
            {formError ? (
              <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                {formError}
              </div>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Name</span>
                <input
                  required
                  value={form.name}
                  onChange={(event) => updateField("name", event.target.value)}
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                />
              </label>
              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Voice</span>
                <input
                  required
                  value={form.tts_voice}
                  onChange={(event) => updateField("tts_voice", event.target.value)}
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                  placeholder="Cherry"
                />
              </label>
              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">TTS language</span>
                <input
                  required
                  value={form.tts_language}
                  onChange={(event) => updateField("tts_language", event.target.value)}
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                  placeholder="en"
                />
              </label>
              <label className="block space-y-2">
                <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Sort order</span>
                <input
                  type="number"
                  value={form.sort_order}
                  onChange={(event) => updateField("sort_order", event.target.value)}
                  className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                />
              </label>
            </div>

            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Description</span>
              <textarea
                value={form.description}
                onChange={(event) => updateField("description", event.target.value)}
                rows={3}
                className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              />
            </label>

            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Live2D model URL</span>
              <input
                required
                value={form.model_url}
                onChange={(event) => updateField("model_url", event.target.value)}
                className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              />
            </label>

            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Cubism core URL</span>
              <input
                required
                value={form.core_url}
                onChange={(event) => updateField("core_url", event.target.value)}
                className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              />
            </label>

            <label className="block space-y-2">
              <span className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Thumbnail URL</span>
              <input
                value={form.thumbnail_url}
                onChange={(event) => updateField("thumbnail_url", event.target.value)}
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
              {isSaving ? "Saving..." : character ? "Save Character" : "Create Character"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AdminCharactersPage = () => {
  const [characters, setCharacters] = useState([]);
  const [filters, setFilters] = useState({ search: "", include_deleted: false, page: 1, page_size: 50 });
  const [selectedCharacterId, setSelectedCharacterId] = useState(null);
  const [editingCharacter, setEditingCharacter] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedCharacter = useMemo(
    () => characters.find((character) => character.id === selectedCharacterId) || characters[0] || null,
    [characters, selectedCharacterId],
  );

  const loadCharacters = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await adminCharactersApi.listCharacters(filters);
      setCharacters(data.items || []);
      setSelectedCharacterId((current) => {
        if (current && data.items?.some((item) => item.id === current)) {
          return current;
        }
        return data.items?.[0]?.id || null;
      });
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Failed to load characters."));
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadCharacters();
  }, [loadCharacters]);

  const openCreate = () => {
    setEditingCharacter(null);
    setIsEditorOpen(true);
  };

  const openEdit = (character = selectedCharacter) => {
    if (!character) return;
    setEditingCharacter({ ...character });
    setIsEditorOpen(true);
  };

  const handleSave = async (payload) => {
    setIsSaving(true);
    setError("");
    try {
      if (editingCharacter) {
        await adminCharactersApi.updateCharacter(editingCharacter.id, payload);
      } else {
        await adminCharactersApi.createCharacter(payload);
      }
      setNotice(editingCharacter ? "Character updated." : "Character created.");
      setIsEditorOpen(false);
      await loadCharacters();
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Failed to save character."));
      throw saveError;
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (characterId) => {
    try {
      await adminCharactersApi.deleteCharacter(characterId);
      setNotice("Character soft-deleted.");
      await loadCharacters();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Failed to delete character."));
    }
  };

  const handleRestore = async (characterId) => {
    try {
      await adminCharactersApi.restoreCharacter(characterId);
      setNotice("Character restored.");
      await loadCharacters();
    } catch (restoreError) {
      setError(getApiErrorMessage(restoreError, "Failed to restore character."));
    }
  };

  const handleToggle = async (characterId) => {
    try {
      await adminCharactersApi.toggleCharacter(characterId);
      setNotice("Character visibility updated.");
      await loadCharacters();
    } catch (toggleError) {
      setError(getApiErrorMessage(toggleError, "Failed to toggle character."));
    }
  };

  return (
    <AdminShell
      title="Character Admin Panel"
      subtitle="Manage Live2D avatars and the TTS voice assigned to scenarios."
    >
      <div className="space-y-6">
        {(notice || error) && (
          <div className={`rounded-[26px] px-5 py-4 text-sm font-semibold ${
            error
              ? "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
              : "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
          }`}
          >
            {error || notice}
          </div>
        )}

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
          <div className="min-w-0 rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Master List</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Characters</h2>
                <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">{characters.length} loaded</p>
              </div>
              <button
                type="button"
                onClick={openCreate}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5"
              >
                <Plus size={16} />
                New Character
              </button>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
              <input
                value={filters.search}
                onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value, page: 1 }))}
                placeholder="Search name, description, voice..."
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              />
              <label className="flex items-center gap-3 rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold dark:border-zinc-700 dark:bg-zinc-950">
                <input
                  type="checkbox"
                  checked={filters.include_deleted}
                  onChange={(event) => setFilters((current) => ({ ...current, include_deleted: event.target.checked, page: 1 }))}
                />
                Include deleted
              </label>
            </div>

            <div className="mt-5 overflow-hidden rounded-[24px] border border-zinc-200 dark:border-zinc-800">
              <div className="grid grid-cols-[minmax(0,1fr)_120px_100px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <span>Character</span>
                <span>Voice</span>
                <span>Status</span>
              </div>
              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoading ? (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading characters...</div>
                ) : null}
                {!isLoading && characters.length === 0 ? (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">No characters found.</div>
                ) : null}
                {!isLoading && characters.map((character) => {
                  const isSelected = selectedCharacter?.id === character.id;
                  return (
                    <button
                      key={character.id}
                      type="button"
                      onClick={() => setSelectedCharacterId(character.id)}
                      className={`grid w-full grid-cols-[minmax(0,1fr)_120px_100px] gap-3 px-4 py-4 text-left text-sm transition ${
                        isSelected ? "bg-primary/5 dark:bg-primary/10" : "hover:bg-zinc-50 dark:hover:bg-zinc-950/60"
                      }`}
                    >
                      <span className="min-w-0">
                        <span className="block truncate font-semibold text-zinc-900 dark:text-zinc-100">{character.name}</span>
                        <span className="mt-1 block truncate text-xs text-zinc-500 dark:text-zinc-400">{character.description || character.model_url}</span>
                      </span>
                      <span className="flex items-center text-zinc-600 dark:text-zinc-300">{character.tts_voice}</span>
                      <span className="flex flex-col justify-center gap-1">
                        <StatusBadge tone={character.is_active ? "emerald" : "zinc"}>
                          {character.is_active ? "Active" : "Inactive"}
                        </StatusBadge>
                        {character.deleted_at ? <StatusBadge tone="rose">Deleted</StatusBadge> : null}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <aside className="min-w-0 rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 xl:sticky xl:top-28 xl:max-h-[calc(100dvh-8rem)] xl:overflow-y-auto">
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Detail</p>
            {!selectedCharacter ? (
              <div className="mt-6 rounded-[24px] bg-zinc-50 p-5 text-sm text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                Select a character to inspect details and actions.
              </div>
            ) : (
              <div className="mt-2 space-y-5">
                <div>
                  <h3 className="font-display text-3xl font-black tracking-tight">{selectedCharacter.name}</h3>
                  <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                    {selectedCharacter.description || "No description configured."}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge tone={selectedCharacter.is_active ? "emerald" : "zinc"}>
                      {selectedCharacter.is_active ? "Active" : "Inactive"}
                    </StatusBadge>
                    {selectedCharacter.deleted_at ? <StatusBadge tone="rose">Deleted</StatusBadge> : null}
                  </div>
                </div>

                <div className="grid gap-3">
                  {[
                    ["Voice", selectedCharacter.tts_voice],
                    ["Language", selectedCharacter.tts_language],
                    ["Model URL", selectedCharacter.model_url],
                    ["Core URL", selectedCharacter.core_url],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-[20px] bg-zinc-50 px-4 py-3 dark:bg-zinc-950">
                      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">{label}</p>
                      <p className="mt-1 break-all text-sm font-semibold">{value || "Not set"}</p>
                    </div>
                  ))}
                </div>

                <div className="grid gap-2">
                  <button
                    type="button"
                    onClick={() => openEdit(selectedCharacter)}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white transition hover:-translate-y-0.5"
                  >
                    <PencilSimple size={16} />
                    Edit Character
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggle(selectedCharacter.id)}
                    disabled={Boolean(selectedCharacter.deleted_at)}
                    className="inline-flex items-center justify-center rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    {selectedCharacter.is_active ? "Deactivate" : "Activate"}
                  </button>
                  {selectedCharacter.deleted_at ? (
                    <button
                      type="button"
                      onClick={() => handleRestore(selectedCharacter.id)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-emerald-200 px-4 py-3 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 dark:border-emerald-500/30 dark:text-emerald-300 dark:hover:bg-emerald-500/10"
                    >
                      <ArrowCounterClockwise size={16} />
                      Restore
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleDelete(selectedCharacter.id)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-200 px-4 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 dark:border-rose-500/30 dark:text-rose-300 dark:hover:bg-rose-500/10"
                    >
                      <Trash size={16} />
                      Soft-delete
                    </button>
                  )}
                </div>
              </div>
            )}
          </aside>
        </section>
      </div>

      {isEditorOpen ? (
        <CharacterEditorModal
          key={editingCharacter?.id || "new-character"}
          character={editingCharacter}
          onClose={() => setIsEditorOpen(false)}
          onSubmit={handleSave}
          isSaving={isSaving}
        />
      ) : null}
    </AdminShell>
  );
};

export default AdminCharactersPage;
