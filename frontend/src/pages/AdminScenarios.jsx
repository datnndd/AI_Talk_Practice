import { useEffect, useState } from "react";
import { CheckSquareOffset, FadersHorizontal, PencilSimple, Plus, Trash, ArrowCounterClockwise, Sparkle } from "@phosphor-icons/react";
import AdminShell from "../components/admin/AdminShell";
import PromptQualityBadge from "../components/admin/PromptQualityBadge";
import ScenarioEditorModal from "../components/admin/ScenarioEditorModal";
import VariationPanel from "../components/admin/VariationPanel";
import { adminApi } from "../lib/adminApi";

const DEFAULT_FILTERS = {
  search: "",
  category: "",
  difficulty: "",
  tag: "",
  include_deleted: false,
  page: 1,
  page_size: 12,
};

const AdminScenarios = () => {
  const [theme, setTheme] = useState(() => localStorage.getItem("admin-theme") || "light");
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [scenarios, setScenarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [promptHistory, setPromptHistory] = useState([]);
  const [variations, setVariations] = useState([]);
  const [variationSearch, setVariationSearch] = useState("");
  const [generationTask, setGenerationTask] = useState(null);
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState(null);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isSavingScenario, setIsSavingScenario] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    localStorage.setItem("admin-theme", theme);
  }, [theme]);

  useEffect(() => {
    loadScenarios();
  }, [filters]);

  useEffect(() => {
    if (selectedScenarioId) {
      loadScenarioDetail(selectedScenarioId);
    }
  }, [selectedScenarioId]);

  useEffect(() => {
    if (selectedScenarioId) {
      loadVariations(selectedScenarioId, variationSearch);
    }
  }, [selectedScenarioId, variationSearch]);

  useEffect(() => {
    if (!generationTask || !["queued", "running"].includes(generationTask.status)) {
      return undefined;
    }

    const interval = setInterval(async () => {
      try {
        const latest = await adminApi.getGenerationTask(generationTask.task_id);
        setGenerationTask(latest);
        if (latest.status === "completed") {
          setNotice(`Generated ${latest.created_count} variations.`);
          if (selectedScenarioId) {
            await loadScenarioDetail(selectedScenarioId);
            await loadVariations(selectedScenarioId, variationSearch);
          }
          await loadScenarios();
        }
      } catch (taskError) {
        clearInterval(interval);
        setError(taskError?.response?.data?.detail || "Failed to refresh generation task.");
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [generationTask, selectedScenarioId, variationSearch]);

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === "page" ? value : 1,
    }));
  };

  const loadScenarios = async () => {
    setIsLoadingScenarios(true);
    setError("");
    try {
      const data = await adminApi.listScenarios(filters);
      setScenarios(data.items);
      setTotal(data.total);

      if (data.items.length === 0) {
        setSelectedScenarioId(null);
        setSelectedScenario(null);
        setVariations([]);
        return;
      }

      setSelectedScenarioId((current) => {
        if (current && data.items.some((item) => item.id === current)) {
          return current;
        }
        return data.items[0].id;
      });
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || "Failed to load scenarios.");
    } finally {
      setIsLoadingScenarios(false);
    }
  };

  const loadScenarioDetail = async (scenarioId) => {
    setIsLoadingDetail(true);
    try {
      const [scenario, history] = await Promise.all([
        adminApi.getScenario(scenarioId),
        adminApi.getPromptHistory(scenarioId),
      ]);
      setSelectedScenario(scenario);
      setPromptHistory(history);
    } catch (detailError) {
      setError(detailError?.response?.data?.detail || "Failed to load scenario details.");
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const loadVariations = async (scenarioId, search = "") => {
    try {
      const data = await adminApi.listVariations(scenarioId, search);
      setVariations(data.items);
    } catch (variationError) {
      setError(variationError?.response?.data?.detail || "Failed to load variations.");
    }
  };

  const openCreateScenario = () => {
    setEditingScenario(null);
    setIsScenarioModalOpen(true);
  };

  const openEditScenario = async (scenario = selectedScenario) => {
    if (!scenario) return;
    setSelectedScenarioId(scenario.id);
    // Fetch the fresh detail directly instead of relying on stale selectedScenario state
    try {
      const [freshScenario, history] = await Promise.all([
        adminApi.getScenario(scenario.id),
        adminApi.getPromptHistory(scenario.id),
      ]);
      setSelectedScenario(freshScenario);
      setPromptHistory(history);
      setEditingScenario({ ...freshScenario });
    } catch {
      setEditingScenario({ ...scenario });
    }
    setIsScenarioModalOpen(true);
  };

  const handleSaveScenario = async (payload) => {
    setIsSavingScenario(true);
    setError("");
    try {
      const saved = editingScenario
        ? await adminApi.updateScenario(editingScenario.id, payload)
        : await adminApi.createScenario(payload);
      setNotice(editingScenario ? "Scenario updated." : "Scenario created.");
      setIsScenarioModalOpen(false);
      setSelectedScenarioId(saved.id);
      await loadScenarios();
      await loadScenarioDetail(saved.id);
    } catch (saveError) {
      setError(saveError?.response?.data?.detail || "Failed to save scenario.");
      throw saveError;
    } finally {
      setIsSavingScenario(false);
    }
  };

  const handleSuggestSkills = async (payload) => {
    const data = await adminApi.suggestSkills(payload);
    return data.suggested_skills;
  };

  const handleDeleteScenario = async (scenarioId) => {
    try {
      await adminApi.deleteScenario(scenarioId);
      setNotice("Scenario soft-deleted.");
      await loadScenarios();
    } catch (deleteError) {
      setError(deleteError?.response?.data?.detail || "Failed to delete scenario.");
    }
  };

  const handleRestoreScenario = async (scenarioId) => {
    try {
      await adminApi.restoreScenario(scenarioId);
      setNotice("Scenario restored.");
      await loadScenarios();
      await loadScenarioDetail(scenarioId);
    } catch (restoreError) {
      setError(restoreError?.response?.data?.detail || "Failed to restore scenario.");
    }
  };

  const handleToggleScenario = async (scenarioId) => {
    try {
      await adminApi.toggleScenario(scenarioId);
      setNotice("Scenario visibility updated.");
      await loadScenarios();
      await loadScenarioDetail(scenarioId);
    } catch (toggleError) {
      setError(toggleError?.response?.data?.detail || "Failed to toggle scenario.");
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedIds.length === 0) return;
    try {
      const response = await adminApi.bulkAction({
        scenario_ids: selectedIds,
        action,
        generation_count: action === "generate_variations" ? 8 : undefined,
      });
      if (response.task) {
        setGenerationTask(response.task);
      }
      setNotice(response.message);
      setSelectedIds([]);
      await loadScenarios();
    } catch (bulkError) {
      setError(bulkError?.response?.data?.detail || "Bulk action failed.");
    }
  };

  const handleGenerateVariations = async (scenarioId) => {
    try {
      const task = await adminApi.generateVariations(scenarioId, {
        count: selectedScenario?.pre_gen_count || 8,
        overwrite_existing: false,
        approve_generated: true,
      });
      setGenerationTask(task);
      setNotice("Variation generation started.");
    } catch (generationError) {
      setError(generationError?.response?.data?.detail || "Failed to start generation.");
    }
  };

  const handleCreateVariation = async (payload) => {
    await adminApi.createVariation(payload);
    setNotice("Variation created.");
    await loadVariations(payload.scenario_id, variationSearch);
    await loadScenarioDetail(payload.scenario_id);
  };

  const handleUpdateVariation = async (variationId, payload) => {
    await adminApi.updateVariation(variationId, payload);
    setNotice("Variation updated.");
    await loadVariations(selectedScenarioId, variationSearch);
    await loadScenarioDetail(selectedScenarioId);
  };

  const handleDeleteVariation = async (variationId) => {
    try {
      await adminApi.deleteVariation(variationId);
      setNotice("Variation disabled.");
      await loadVariations(selectedScenarioId, variationSearch);
      await loadScenarioDetail(selectedScenarioId);
    } catch (variationError) {
      setError(variationError?.response?.data?.detail || "Failed to disable variation.");
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / filters.page_size));
  const selectedCount = selectedIds.length;
  const summaryCards = [
    { label: "Scenarios", value: total },
    { label: "Selected", value: selectedCount },
    { label: "Variations", value: selectedScenario?.variation_count || 0 },
    { label: "Usage", value: selectedScenario?.usage_count || 0 },
  ];

  return (
    <AdminShell
      theme={theme}
      onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      title="Scenario Admin Panel"
      subtitle="Manage reusable speaking scenarios, prompt history, and the hybrid pre-generation workflow for teachers and content operators."
    >
      <div className="space-y-6">
        {(notice || error) && (
          <div
            className={`rounded-[26px] px-5 py-4 text-sm font-semibold ${
              error
                ? "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
            }`}
          >
            {error || notice}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {summaryCards.map((card) => (
            <div key={card.label} className="rounded-[28px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                {card.label}
              </p>
              <p className="mt-3 font-display text-4xl font-black tracking-tight">{card.value}</p>
            </div>
          ))}
        </div>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]" id="scenario-library">
          <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Scenario Library</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Scenario Management</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={openCreateScenario}
                  className="inline-flex items-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5"
                >
                  <Plus size={16} />
                  New Scenario
                </button>
                <button
                  type="button"
                  onClick={() => handleBulkAction("generate_variations")}
                  disabled={selectedCount === 0}
                  className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  <Sparkle size={16} />
                  Batch Generate
                </button>
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              <label className="block xl:col-span-2">
                <span className="sr-only">Search</span>
                <input
                  value={filters.search}
                  onChange={(event) => updateFilter("search", event.target.value)}
                  placeholder="Search title, description, tags..."
                  className="w-full rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>
              <input
                value={filters.category}
                onChange={(event) => updateFilter("category", event.target.value)}
                placeholder="Category"
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              />
              <select
                value={filters.difficulty}
                onChange={(event) => updateFilter("difficulty", event.target.value)}
                className="rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              >
                <option value="">All difficulty</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
              <label className="flex items-center gap-3 rounded-[22px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold dark:border-zinc-700 dark:bg-zinc-950">
                <FadersHorizontal size={16} />
                <input
                  type="checkbox"
                  checked={filters.include_deleted}
                  onChange={(event) => updateFilter("include_deleted", event.target.checked)}
                />
                Include deleted
              </label>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {[
                ["activate", "Activate"],
                ["deactivate", "Deactivate"],
                ["soft_delete", "Soft-delete"],
              ].map(([action, label]) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => handleBulkAction(action)}
                  disabled={selectedCount === 0}
                  className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-black uppercase tracking-[0.18em] text-zinc-600 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="mt-5 overflow-hidden rounded-[24px] border border-zinc-200 dark:border-zinc-800">
              <div className="grid grid-cols-[48px_minmax(0,1.5fr)_120px_120px_120px_150px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <button
                  type="button"
                  onClick={() =>
                    setSelectedIds((current) =>
                      current.length === scenarios.length ? [] : scenarios.map((item) => item.id)
                    )
                  }
                  className="text-left"
                >
                  <CheckSquareOffset size={18} />
                </button>
                <span>Scenario</span>
                <span>Difficulty</span>
                <span>Usage</span>
                <span>Status</span>
                <span className="text-right">Actions</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingScenarios && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading scenarios...</div>
                )}

                {!isLoadingScenarios &&
                  scenarios.map((scenario) => {
                    const isSelected = selectedScenarioId === scenario.id;
                    const isChecked = selectedIds.includes(scenario.id);
                    return (
                      <div
                        key={scenario.id}
                        className={`grid grid-cols-[48px_minmax(0,1.5fr)_120px_120px_120px_150px] gap-3 px-4 py-4 text-sm transition ${
                          isSelected ? "bg-primary/5 dark:bg-primary/10" : ""
                        }`}
                      >
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(event) =>
                              setSelectedIds((current) =>
                                event.target.checked
                                  ? [...new Set([...current, scenario.id])]
                                  : current.filter((item) => item !== scenario.id)
                              )
                            }
                          />
                        </label>
                        <button
                          type="button"
                          onClick={() => setSelectedScenarioId(scenario.id)}
                          className="min-w-0 text-left"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate font-semibold text-zinc-900 dark:text-zinc-100">{scenario.title}</p>
                              <p className="mt-1 line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                                {scenario.description}
                              </p>
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {(scenario.tags || []).slice(0, 3).map((tag) => (
                                  <span
                                    key={tag}
                                    className="rounded-full bg-zinc-100 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <PromptQualityBadge quality={scenario.latest_prompt_quality} compact />
                          </div>
                        </button>
                        <div className="flex items-center text-zinc-600 dark:text-zinc-300">{scenario.difficulty}</div>
                        <div className="flex items-center text-zinc-600 dark:text-zinc-300">{scenario.usage_count}</div>
                        <div className="flex flex-col justify-center gap-1">
                          <span
                            className={`rounded-full px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${
                              scenario.is_active
                                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                                : "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                            }`}
                          >
                            {scenario.is_active ? "Active" : "Inactive"}
                          </span>
                          {scenario.deleted_at && (
                            <span className="rounded-full bg-rose-100 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                              Deleted
                            </span>
                          )}
                        </div>
                        <div className="flex items-center justify-end gap-3">
                          <button
                            type="button"
                            onClick={() => openEditScenario(scenario)}
                            className="text-xs font-bold text-primary"
                          >
                            <PencilSimple size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleToggleScenario(scenario.id)}
                            className="text-xs font-bold text-zinc-600 dark:text-zinc-300"
                          >
                            Toggle
                          </button>
                          {scenario.deleted_at ? (
                            <button
                              type="button"
                              onClick={() => handleRestoreScenario(scenario.id)}
                              className="text-xs font-bold text-emerald-600 dark:text-emerald-300"
                            >
                              <ArrowCounterClockwise size={16} />
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleDeleteScenario(scenario.id)}
                              className="text-xs font-bold text-rose-600 dark:text-rose-300"
                            >
                              <Trash size={16} />
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3">
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Page {filters.page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => updateFilter("page", Math.max(1, filters.page - 1))}
                  disabled={filters.page === 1}
                  className="rounded-2xl border border-zinc-200 px-4 py-2 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => updateFilter("page", Math.min(totalPages, filters.page + 1))}
                  disabled={filters.page >= totalPages}
                  className="rounded-2xl border border-zinc-200 px-4 py-2 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Scenario Detail</p>
              {isLoadingDetail && (
                <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">Loading selected scenario...</p>
              )}
              {!isLoadingDetail && selectedScenario && (
                <>
                  <h3 className="mt-1 font-display text-3xl font-black tracking-tight">{selectedScenario.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">{selectedScenario.description}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(selectedScenario.target_skills || []).map((skill) => (
                      <span
                        key={skill}
                        className="rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-primary"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        Duration
                      </p>
                      <p className="mt-2 text-sm font-semibold">
                        {selectedScenario.estimated_duration_minutes || 0} minutes
                      </p>
                    </div>
                    <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        Pre-generation
                      </p>
                      <p className="mt-2 text-sm font-semibold">
                        {selectedScenario.is_pre_generated ? `${selectedScenario.pre_gen_count} targets` : "Dynamic only"}
                      </p>
                    </div>
                  </div>
                  <div className="mt-5">
                    <PromptQualityBadge quality={selectedScenario.latest_prompt_quality} />
                  </div>
                </>
              )}
            </div>
          </div>
        </section>

        <VariationPanel
          scenario={selectedScenario}
          variations={variations}
          search={variationSearch}
          onSearchChange={setVariationSearch}
          onCreateVariation={handleCreateVariation}
          onUpdateVariation={handleUpdateVariation}
          onDeleteVariation={handleDeleteVariation}
          onGenerateVariations={handleGenerateVariations}
          generationTask={generationTask}
          isLoading={isLoadingDetail}
        />
      </div>

      {isScenarioModalOpen && (
        <ScenarioEditorModal
          key={editingScenario?.id || "new-scenario"}
          scenario={editingScenario}
          promptHistory={promptHistory}
          onClose={() => setIsScenarioModalOpen(false)}
          onSubmit={handleSaveScenario}
          onSuggestSkills={handleSuggestSkills}
          isSaving={isSavingScenario}
        />
      )}
    </AdminShell>
  );
};

export default AdminScenarios;
