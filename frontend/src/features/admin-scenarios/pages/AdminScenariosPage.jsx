import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowCounterClockwise,
  CheckSquareOffset,
  FadersHorizontal,
  PencilSimple,
  Plus,
  Trash,
} from "@phosphor-icons/react";

import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import ScenarioEditorModal from "@/features/admin-scenarios/components/ScenarioEditorModal";
import { adminApi } from "@/features/admin-scenarios/api/adminScenariosApi";

const DEFAULT_FILTERS = {
  search: "",
  category: "",
  difficulty: "",
  tag: "",
  include_deleted: false,
  page: 1,
  page_size: 12,
};

const formatMinutes = (value) => {
  const minutes = Number(value || 0);
  return `${minutes} min`;
};

const StatusBadge = ({ children, tone = "zinc" }) => {
  const tones = {
    emerald: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
    rose: "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300",
    zinc: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  };

  return (
    <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${tones[tone]}`}>
      {children}
    </span>
  );
};

const AdminScenarios = () => {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [scenarios, setScenarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(null);
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState(null);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);
  const [isSavingScenario, setIsSavingScenario] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) || scenarios[0] || null,
    [scenarios, selectedScenarioId],
  );

  const updateFilter = (field, value) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === "page" ? value : 1,
    }));
  };

  const loadScenarios = useCallback(async () => {
    setIsLoadingScenarios(true);
    setError("");
    try {
      const data = await adminApi.listScenarios(filters);
      setScenarios(data.items);
      setTotal(data.total);
      setSelectedScenarioId((current) => {
        if (current && data.items.some((item) => item.id === current)) {
          return current;
        }
        return data.items[0]?.id || null;
      });
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || "Failed to load scenarios.");
    } finally {
      setIsLoadingScenarios(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadScenarios();
  }, [loadScenarios]);

  const openCreateScenario = () => {
    setEditingScenario(null);
    setIsScenarioModalOpen(true);
  };

  const openEditScenario = (scenario = selectedScenario) => {
    if (!scenario) return;
    setEditingScenario({ ...scenario });
    setIsScenarioModalOpen(true);
  };

  const handleSaveScenario = async (payload) => {
    setIsSavingScenario(true);
    setError("");
    try {
      if (editingScenario) {
        await adminApi.updateScenario(editingScenario.id, payload);
      } else {
        await adminApi.createScenario(payload);
      }
      setNotice(editingScenario ? "Scenario updated." : "Scenario created.");
      setIsScenarioModalOpen(false);
      await loadScenarios();
    } catch (saveError) {
      setError(saveError?.response?.data?.detail || "Failed to save scenario.");
      throw saveError;
    } finally {
      setIsSavingScenario(false);
    }
  };

  const handleGenerateDefaultPrompt = async (payload) => {
    const data = await adminApi.generateDefaultPrompt(payload);
    return data;
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
    } catch (restoreError) {
      setError(restoreError?.response?.data?.detail || "Failed to restore scenario.");
    }
  };

  const handleToggleScenario = async (scenarioId) => {
    try {
      await adminApi.toggleScenario(scenarioId);
      setNotice("Scenario visibility updated.");
      await loadScenarios();
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
      });
      setNotice(response.message);
      setSelectedIds([]);
      await loadScenarios();
    } catch (bulkError) {
      setError(bulkError?.response?.data?.detail || "Bulk action failed.");
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / filters.page_size));
  const selectedCount = selectedIds.length;

  return (
    <AdminShell
      title="Scenario Admin Panel"
      subtitle="Manage reusable speaking scenarios with a master-detail workflow and contextual actions."
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

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]" id="scenario-library">
          <div className="min-w-0 rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Master List</p>
                <h2 className="mt-1 font-display text-3xl font-black tracking-tight">Scenarios</h2>
                <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                  {total} total, {selectedCount} selected
                </p>
              </div>
              <button
                type="button"
                onClick={openCreateScenario}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5"
              >
                <Plus size={16} />
                New Scenario
              </button>
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

            <div className="mt-4 flex flex-wrap items-center gap-2">
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
              <div className="grid grid-cols-[44px_minmax(0,1fr)_92px_100px] gap-3 bg-zinc-50 px-4 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                <button
                  type="button"
                  onClick={() =>
                    setSelectedIds((current) =>
                      current.length === scenarios.length ? [] : scenarios.map((item) => item.id),
                    )
                  }
                  className="text-left"
                >
                  <CheckSquareOffset size={18} />
                </button>
                <span>Scenario</span>
                <span>Usage</span>
                <span>Status</span>
              </div>

              <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {isLoadingScenarios && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">Loading scenarios...</div>
                )}

                {!isLoadingScenarios && scenarios.length === 0 && (
                  <div className="px-4 py-8 text-sm text-zinc-500 dark:text-zinc-400">No scenarios found.</div>
                )}

                {!isLoadingScenarios &&
                  scenarios.map((scenario) => {
                    const isChecked = selectedIds.includes(scenario.id);
                    const isSelected = selectedScenario?.id === scenario.id;

                    return (
                      <div
                        key={scenario.id}
                        data-testid={`scenario-row-${scenario.id}`}
                        className={`grid grid-cols-[44px_minmax(0,1fr)_92px_100px] gap-3 px-4 py-4 text-sm transition ${
                          isSelected ? "bg-primary/5 dark:bg-primary/10" : "hover:bg-zinc-50 dark:hover:bg-zinc-950/60"
                        }`}
                      >
                        <label className="flex items-start pt-1">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(event) =>
                              setSelectedIds((current) =>
                                event.target.checked
                                  ? [...new Set([...current, scenario.id])]
                                  : current.filter((item) => item !== scenario.id),
                              )
                            }
                          />
                        </label>
                        <button
                          type="button"
                          onClick={() => setSelectedScenarioId(scenario.id)}
                          className="min-w-0 text-left"
                        >
                          <p className="truncate font-semibold text-zinc-900 dark:text-zinc-100">{scenario.title}</p>
                          <p className="mt-1 line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                            {scenario.description}
                          </p>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            <StatusBadge>{scenario.difficulty}</StatusBadge>
                            {scenario.is_pro && <StatusBadge tone="amber">VIP</StatusBadge>}
                            {(scenario.tags || []).slice(0, 2).map((tag) => (
                              <StatusBadge key={tag}>{tag}</StatusBadge>
                            ))}
                          </div>
                        </button>
                        <div className="flex items-center text-zinc-600 dark:text-zinc-300">{scenario.usage_count}</div>
                        <div className="flex flex-col justify-center gap-1">
                          <StatusBadge tone={scenario.is_active ? "emerald" : "zinc"}>
                            {scenario.is_active ? "Active" : "Inactive"}
                          </StatusBadge>
                          {scenario.deleted_at && <StatusBadge tone="rose">Deleted</StatusBadge>}
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

          <aside className="min-w-0 rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 xl:sticky xl:top-28 xl:max-h-[calc(100dvh-8rem)] xl:overflow-y-auto">
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Detail</p>

            {!selectedScenario ? (
              <div className="mt-6 rounded-[24px] bg-zinc-50 p-5 text-sm text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
                Select a scenario to inspect details and actions.
              </div>
            ) : (
              <div className="mt-2 space-y-5">
                <div>
                  <h3 className="font-display text-3xl font-black tracking-tight">{selectedScenario.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                    {selectedScenario.description}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge tone={selectedScenario.is_active ? "emerald" : "zinc"}>
                      {selectedScenario.is_active ? "Active" : "Inactive"}
                    </StatusBadge>
                    {selectedScenario.deleted_at && <StatusBadge tone="rose">Deleted</StatusBadge>}
                    {selectedScenario.is_pro ? <StatusBadge tone="amber">VIP only</StatusBadge> : <StatusBadge>Free</StatusBadge>}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ["Category", selectedScenario.category],
                    ["Difficulty", selectedScenario.difficulty],
                    ["Usage", selectedScenario.usage_count],
                    ["Duration", formatMinutes(selectedScenario.estimated_duration_minutes)],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-[20px] bg-zinc-50 px-4 py-3 dark:bg-zinc-950">
                      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        {label}
                      </p>
                      <p className="mt-1 truncate text-sm font-semibold">{value || "Not set"}</p>
                    </div>
                  ))}
                </div>

                <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                    Roles
                  </p>
                  <div className="mt-3 space-y-3 text-sm">
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        AI
                      </p>
                      <p className="mt-1 font-semibold">{selectedScenario.ai_role || "Not set"}</p>
                    </div>
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                        Learner
                      </p>
                      <p className="mt-1 font-semibold">{selectedScenario.user_role || "Not set"}</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                    Learner Tasks
                  </p>
                  {(selectedScenario.tasks || []).length > 0 ? (
                    <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-6 text-zinc-700 dark:text-zinc-200">
                      {selectedScenario.tasks.map((task) => (
                        <li key={task}>{task}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">No learner tasks configured.</p>
                  )}
                </div>

                <div className="rounded-[24px] bg-zinc-50 p-4 dark:bg-zinc-950">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                    Contextual Actions
                  </p>
                  <div className="mt-4 grid gap-2">
                    <button
                      type="button"
                      onClick={() => openEditScenario(selectedScenario)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white transition hover:-translate-y-0.5"
                    >
                      <PencilSimple size={16} />
                      Edit Scenario
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleScenario(selectedScenario.id)}
                      disabled={Boolean(selectedScenario.deleted_at)}
                      className="inline-flex items-center justify-center rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                    >
                      {selectedScenario.is_active ? "Deactivate" : "Activate"}
                    </button>
                    {selectedScenario.deleted_at ? (
                      <button
                        type="button"
                        onClick={() => handleRestoreScenario(selectedScenario.id)}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-emerald-200 px-4 py-3 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50 dark:border-emerald-500/30 dark:text-emerald-300 dark:hover:bg-emerald-500/10"
                      >
                        <ArrowCounterClockwise size={16} />
                        Restore
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleDeleteScenario(selectedScenario.id)}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-200 px-4 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 dark:border-rose-500/30 dark:text-rose-300 dark:hover:bg-rose-500/10"
                      >
                        <Trash size={16} />
                        Soft-delete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </aside>
        </section>
      </div>

      {isScenarioModalOpen && (
        <ScenarioEditorModal
          key={editingScenario?.id || "new-scenario"}
          scenario={editingScenario}
          onClose={() => setIsScenarioModalOpen(false)}
          onSubmit={handleSaveScenario}
          onGeneratePrompt={handleGenerateDefaultPrompt}
          isSaving={isSavingScenario}
        />
      )}
    </AdminShell>
  );
};

export default AdminScenarios;
