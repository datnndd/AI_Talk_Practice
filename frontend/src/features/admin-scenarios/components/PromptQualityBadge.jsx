const toneForScore = (score = 0) => {
  if (score >= 85) {
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300";
  }
  if (score >= 70) {
    return "bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300";
  }
  return "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300";
};

const PromptQualityBadge = ({ quality, compact = false }) => {
  if (!quality) {
    return null;
  }

  if (compact) {
    return (
      <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${toneForScore(quality.score)}`}>
        Prompt {quality.score}
      </span>
    );
  }

  return (
    <div className="rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
            Prompt Quality
          </p>
          <p className="mt-2 font-display text-3xl font-black tracking-tight">{quality.score}/100</p>
        </div>
        <span className={`rounded-full px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] ${toneForScore(quality.score)}`}>
          {quality.is_acceptable ? "Approved" : "Needs Work"}
        </span>
      </div>

      {quality.warnings?.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">Warnings</p>
          <ul className="mt-2 space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
            {quality.warnings.map((warning) => (
              <li key={warning} className="rounded-2xl bg-rose-50 px-3 py-2 dark:bg-rose-500/10">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {quality.suggestions?.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">Suggestions</p>
          <ul className="mt-2 space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
            {quality.suggestions.map((suggestion) => (
              <li key={suggestion} className="rounded-2xl bg-zinc-100 px-3 py-2 dark:bg-zinc-800">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PromptQualityBadge;
