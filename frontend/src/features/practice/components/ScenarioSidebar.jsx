import { CheckCircle } from "@phosphor-icons/react";
import Live2DAvatarPanel from "@/features/practice/components/Live2DAvatarPanel";

const compactItems = (items = [], limit = 5) => {
  if (typeof items === "string" && items.trim()) {
    return [items.trim()].slice(0, limit);
  }

  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter((item) => typeof item === "string" && item.trim())
    .map((item) => item.trim())
    .slice(0, limit);
};

const CharacterCameraCard = ({ scenario, character = null, live2DStatus = "idle", lipSyncLevel = 0 }) => {
  const partnerName = scenario?.ai_role || "Emma";
  const modelUrl = character?.model_url || scenario?.character?.model_url || "";
  const coreUrl = character?.core_url || scenario?.character?.core_url || "";

  return (
    <Live2DAvatarPanel
      status={live2DStatus}
      scenarioTitle={partnerName}
      lipSyncLevel={lipSyncLevel}
      modelUrl={modelUrl}
      coreUrl={coreUrl}
      className="min-h-[220px] rounded-xl border border-border bg-card/70 shadow-[0_18px_40px_-30px_rgba(15,23,42,0.9)] lg:min-h-[225px]"
      canvasClassName="min-h-[220px] bg-transparent lg:min-h-[225px]"
    />
  );
};

const ScenarioSidebar = ({ scenario, guidance, completedCount = 0, character = null, live2DStatus = "idle", lipSyncLevel = 0 }) => {
  const focusItems = compactItems(scenario?.tasks || guidance?.evaluationFocus, 10);

  return (
    <aside className="flex min-h-0 flex-col gap-3 overflow-hidden rounded-2xl border border-border bg-card/40 p-3 backdrop-blur lg:gap-4 lg:overflow-y-auto lg:rounded-none lg:border-0 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
      <div className="flex justify-center lg:justify-start">
        <span className="rounded-full bg-[var(--chip-bg)] px-4 py-1.5 text-xs font-semibold text-[var(--chip-text)] lg:rounded-none lg:bg-transparent lg:px-0 lg:py-0 lg:text-sm lg:uppercase lg:tracking-wider lg:text-[var(--page-subtle)]">
          <span className="lg:hidden">💬 Role-play started!</span>
          <span className="hidden lg:inline">Role-Play</span>
        </span>
      </div>

      <div className="grid min-h-0 grid-cols-[65fr_35fr] gap-3 lg:flex lg:flex-col lg:gap-4">
        <CharacterCameraCard
          scenario={scenario}
          character={character}
          live2DStatus={live2DStatus}
          lipSyncLevel={lipSyncLevel}
        />

        <div className="min-h-0 overflow-hidden rounded-2xl border border-border bg-card/60 p-3 backdrop-blur lg:p-5">
          <div className="mb-3 flex items-center justify-between gap-2 lg:mb-4">
            <h3 className="text-sm font-bold text-[var(--page-fg)] lg:text-lg">Tasks</h3>
            <span className="rounded-lg border border-border px-2 py-1 text-xs font-semibold text-[var(--page-fg)] lg:px-3 lg:text-sm">✓ {completedCount}/{focusItems.length}</span>
          </div>
          <ol className="max-h-[190px] space-y-3 overflow-y-auto pr-1 lg:mt-5 lg:max-h-none lg:space-y-4 lg:overflow-visible lg:pr-0">
            {focusItems.map((item, index) => {
              const done = index < completedCount;
              return (
                <li key={`${item}-${index}`} className="flex items-start gap-2 lg:gap-3">
                  <CheckCircle className={`mt-0.5 h-4 w-4 shrink-0 lg:h-5 lg:w-5 ${done ? "text-[var(--success-text)]" : "text-[var(--page-subtle)]"}`} weight={done ? "fill" : "regular"} />
                  <p className={`text-xs leading-snug lg:text-sm ${done ? "text-[var(--page-fg)]/60 line-through" : "text-[var(--page-fg)]"}`}>{item}</p>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </aside>
  );
};

export default ScenarioSidebar;
