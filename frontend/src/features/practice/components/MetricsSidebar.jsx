import { motion } from "framer-motion";
import {
  ArrowsClockwise,
  BookOpen,
  Clock,
  Lightning,
  SignOut,
  SpeakerHigh,
} from "@phosphor-icons/react";
import { formatDuration } from "@/features/practice/services/realtimeAudio";

const STATUS_STYLES = {
  connecting: "bg-amber-100 text-amber-700 border-amber-200",
  ready: "bg-emerald-100 text-emerald-700 border-emerald-200",
  closed: "bg-zinc-100 text-zinc-700 border-zinc-200",
  error: "bg-rose-100 text-rose-700 border-rose-200",
};

const RECORDING_COPY = {
  idle: "Ready",
  recording: "Listening",
  processing: "Processing",
  assistant: "Assistant speaking",
};

const StatCard = ({ icon: Icon, label, value }) => (
  <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4">
    <div className="mb-1 flex items-center gap-2 text-zinc-400">
      <Icon size={14} />
      <span className="text-[9px] font-bold uppercase tracking-wider">{label}</span>
    </div>
    <span className="text-xl font-mono font-bold text-zinc-900">{value}</span>
  </div>
);

const MetricsSidebar = ({
  scenario,
  durationSeconds,
  sessionId,
  turnCount,
  connectionState,
  recordingState,
  onReconnect,
  onEndSession,
}) => {
  const statusClassName = STATUS_STYLES[connectionState] || STATUS_STYLES.closed;

  return (
    <aside className="flex h-full flex-col gap-6 lg:col-span-4">
      <section className="flex-1 rounded-4xl border border-white/20 p-8 shadow-xl liquid-glass refraction">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
            Session Health
          </h3>
          <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${statusClassName}`}>
            {connectionState}
          </span>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-4">
          <StatCard icon={Clock} label="Duration" value={formatDuration(durationSeconds)} />
          <StatCard icon={BookOpen} label="Turns" value={String(turnCount).padStart(2, "0")} />
          <StatCard icon={SpeakerHigh} label="Mode" value="Voice" />
          <StatCard
            icon={Lightning}
            label="Status"
            value={RECORDING_COPY[recordingState] || RECORDING_COPY.idle}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-10 rounded-3xl border border-primary/10 bg-primary/5 p-5"
        >
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            Active Scenario
          </p>
          <p className="mt-3 text-lg font-bold text-zinc-950">{scenario?.title || "Connecting..."}</p>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            {scenario?.learning_objectives || "Scenario objectives will appear once the session is ready."}
          </p>
          <div className="mt-4 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-zinc-400">
            <span>Session ID</span>
            <span className="rounded-full bg-white px-2 py-1 font-mono text-zinc-700">
              {sessionId || "pending"}
            </span>
          </div>
        </motion.div>
      </section>

      <section className="rounded-4xl border border-white/20 p-8 shadow-xl liquid-glass refraction">
        <div className="flex gap-3">
          <button
            onClick={onReconnect}
            className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white py-4 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-600 transition-all hover:bg-zinc-50"
          >
            <ArrowsClockwise weight="bold" />
            Reconnect
          </button>
          <button
            onClick={onEndSession}
            className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-zinc-950 py-4 text-[10px] font-bold uppercase tracking-[0.2em] text-white transition-all hover:bg-zinc-800"
          >
            <SignOut weight="bold" />
            End Session
          </button>
        </div>
      </section>
    </aside>
  );
};

export default MetricsSidebar;
