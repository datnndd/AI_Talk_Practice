import { ClipboardText, Target } from "@phosphor-icons/react";

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

const ScenarioSidebar = ({ scenario, guidance }) => {
  const focusItems = compactItems(scenario?.tasks || guidance?.evaluationFocus, 10);

  return (
    <aside className="flex flex-col gap-5 overflow-y-auto rounded-lg border border-zinc-200 bg-white p-5 shadow-[0_20px_54px_-42px_rgba(15,23,42,0.55)]">
      <section>
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-600">
          <ClipboardText size={16} weight="fill" />
          Tình huống
        </div>
        <h2 className="mt-3 font-display text-2xl font-black tracking-tight text-zinc-950">
          {scenario?.title || guidance?.topic || "Practice session"}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          {scenario?.description || guidance?.assignedTask || "Hoàn thành cuộc hội thoại dựa trên tình huống thiết lập."}
        </p>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-zinc-50/50 p-4">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
          <Target size={16} weight="fill" />
          Nhiệm vụ
        </div>
        
        {focusItems.length > 0 ? (
          <ul className="mt-3 grid gap-2">
            {focusItems.map((item, index) => (
              <li key={`${item}-${index}`} className="flex items-start gap-2.5 text-sm font-medium text-zinc-700">
                <span className="mt-2 flex h-1.5 w-1.5 shrink-0 rounded-full bg-primary/40" />
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm font-medium text-zinc-500">
            {guidance?.assignedTask || "Hoàn thành các thử thách thực tế từ đối tác hội thoại."}
          </p>
        )}
      </section>
    </aside>
  );
};

export default ScenarioSidebar;
