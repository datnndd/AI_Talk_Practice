import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowsClockwise, Clock } from "@phosphor-icons/react";

const formatCountdown = (seconds) => {
  const wholeSecs = Math.max(0, Math.floor(seconds));
  const min = Math.floor(wholeSecs / 60);
  const sec = wholeSecs % 60;
  return `${min}:${String(sec).padStart(2, "0")}`;
};

const SessionHeader = ({
  onBack,
  onReconnect,
  connectionState,
  durationSeconds = 0,
  timeLimitSeconds = null,
}) => {
  const [tick, setTick] = useState(0);

  // Re-render every second when a time limit is active to update countdown
  useEffect(() => {
    if (!timeLimitSeconds) return;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [timeLimitSeconds]);

  const remaining = useMemo(() => {
    if (!timeLimitSeconds) return null;
    return Math.max(0, timeLimitSeconds - durationSeconds);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLimitSeconds, durationSeconds, tick]);

  const pillColor = useMemo(() => {
    if (remaining === null || !timeLimitSeconds) return "border-zinc-200 bg-white text-zinc-500";
    const pct = remaining / timeLimitSeconds;
    if (pct <= 0.1) return "border-rose-200 bg-rose-50 text-rose-700 animate-pulse";
    if (pct <= 0.2) return "border-amber-200 bg-amber-50 text-amber-700";
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }, [remaining, timeLimitSeconds]);

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
        {/* Countdown pill — shown only when a time limit is active */}
        {remaining !== null && (
          <div
            className={`flex h-11 items-center gap-2 rounded-2xl border px-4 text-[11px] font-black uppercase tracking-[0.18em] transition ${pillColor}`}
          >
            <Clock size={14} weight="bold" />
            {remaining <= 0 ? "Time up" : formatCountdown(remaining)}
          </div>
        )}

        {onReconnect && (
          <button
            onClick={onReconnect}
            disabled={connectionState === "connecting" || connectionState === "reconnecting"}
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
