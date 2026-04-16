import { ArrowLeft, ArrowsClockwise } from "@phosphor-icons/react";

const SessionHeader = ({ onBack, onReconnect, connectionState }) => {
  return (
    <header className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-zinc-200 bg-white text-zinc-700 shadow-[0_14px_30px_-24px_rgba(15,23,42,0.5)] transition hover:text-rose-600"
          title="Kết thúc buổi học"
        >
          <ArrowLeft size={18} weight="bold" />
        </button>
        <span className="text-sm font-bold tracking-tight text-zinc-400">Kết thúc</span>
      </div>

      <div className="flex items-center gap-2">
        {onReconnect && (
          <button
            onClick={onReconnect}
            disabled={connectionState === "connecting"}
            className="flex h-11 items-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-500 shadow-sm transition hover:bg-zinc-50 disabled:opacity-50"
          >
            <ArrowsClockwise size={16} weight="bold" />
            Thử kết nối lại
          </button>
        )}
      </div>
    </header>
  );
};

export default SessionHeader;
