import { ArrowLeft, Broadcast, SignOut } from "@phosphor-icons/react";

const CONNECTION_STYLES = {
  closed: "bg-zinc-900/8 text-zinc-600",
  connecting: "bg-amber-500/12 text-amber-700",
  ready: "bg-emerald-500/12 text-emerald-700",
  error: "bg-rose-500/12 text-rose-700",
};

const SessionHeader = ({ scenarioTitle, connectionState, onBack, onExit }) => {
  const connectionClass = CONNECTION_STYLES[connectionState] || CONNECTION_STYLES.closed;

  return (
    <header className="rounded-[32px] border border-white/50 bg-white/70 px-4 py-4 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.35)] backdrop-blur-xl md:px-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-zinc-200/80 bg-white/80 text-zinc-700 transition hover:-translate-y-0.5 hover:text-primary"
            aria-label="Back to topics"
          >
            <ArrowLeft size={18} weight="bold" />
          </button>
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[0.24em] text-primary">Live Practice</p>
            <h1 className="truncate font-display text-2xl font-black tracking-tight text-zinc-950 md:text-[2rem]">
              {scenarioTitle}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <div className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] ${connectionClass}`}>
            <Broadcast size={14} weight="fill" />
            {connectionState}
          </div>
          <button
            type="button"
            onClick={onExit}
            className="inline-flex items-center gap-2 rounded-2xl bg-zinc-950 px-4 py-3 text-xs font-black uppercase tracking-[0.18em] text-white transition hover:-translate-y-0.5"
          >
            <SignOut size={16} weight="bold" />
            Leave
          </button>
        </div>
      </div>
    </header>
  );
};

export default SessionHeader;
