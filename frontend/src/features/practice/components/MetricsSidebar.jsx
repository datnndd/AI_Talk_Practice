import { useMemo, useState } from "react";
import {
  ArrowsClockwise,
  BookOpen,
  CheckCircle,
  Clock,
  Lightning,
  SignOut,
  Sparkle,
} from "@phosphor-icons/react";
import { formatDuration } from "@/features/practice/services/realtimeAudio";
import { formatScenarioList } from "@/features/practice/utils/conversationGuidance";
import { formatLessonEndReason, getLessonStatusLabel } from "@/features/practice/utils/lessonState";

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
  interrupting: "Stopping reply",
};

const SectionCard = ({ title, children }) => (
  <section className="rounded-[28px] border border-white/40 bg-white/80 p-5 shadow-[0_18px_40px_-30px_rgba(15,23,42,0.45)] backdrop-blur-xl">
    <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-zinc-400">{title}</p>
    <div className="mt-4">{children}</div>
  </section>
);

const StatCard = ({ icon: Icon, label, value }) => (
  <div className="rounded-2xl border border-zinc-200 bg-zinc-50/80 p-4">
    <div className="mb-1 flex items-center gap-2 text-zinc-400">
      <Icon size={14} />
      <span className="text-[9px] font-bold uppercase tracking-wider">{label}</span>
    </div>
    <span className="text-lg font-mono font-bold text-zinc-900">{value}</span>
  </div>
);

const CoverageGroup = ({ title, items, tone = "sky", emptyCopy }) => {
  const styles =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-sky-200 bg-sky-50 text-sky-700";

  return (
    <div className="rounded-2xl border border-zinc-200 bg-zinc-50/80 p-4">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length > 0 ? items.map((item) => (
          <span
            key={item}
            className={`inline-flex rounded-full border px-3 py-2 text-xs font-bold ${styles}`}
          >
            {item}
          </span>
        )) : (
          <span className="text-sm text-zinc-500">{emptyCopy}</span>
        )}
      </div>
    </div>
  );
};

const MetricsSidebar = ({
  durationSeconds,
  sessionId,
  turnCount,
  connectionState,
  recordingState,
  onReconnect,
  onEndSession,
  lessonState,
}) => {
  const [mobileTab, setMobileTab] = useState("progress");
  const statusClassName = STATUS_STYLES[connectionState] || STATUS_STYLES.closed;
  const lessonGoals = useMemo(
    () => formatScenarioList(lessonState?.lesson_goals),
    [lessonState?.lesson_goals],
  );
  const currentGoal = lessonState?.current_objective?.goal || "";
  const objectives = useMemo(() => {
    if (lessonGoals.length > 0) {
      return lessonGoals;
    }
    return currentGoal ? [currentGoal] : [];
  }, [currentGoal, lessonGoals]);

  const completedCount = lessonState?.progress?.completed || 0;
  const activeIndex = lessonState?.should_end
    ? Math.max(objectives.length - 1, 0)
    : Math.min(completedCount, Math.max(objectives.length - 1, 0));
  const coveredPoints = lessonState?.current_objective?.matched_points || [];
  const missingPoints = lessonState?.current_objective?.missing_points || [];
  const showProgressSection = mobileTab === "progress";
  const showDetailsSection = mobileTab === "details";

  return (
    <aside className="flex h-full flex-col gap-5 lg:col-span-4">
      <div className="grid grid-cols-2 gap-2 lg:hidden">
        <button
          type="button"
          onClick={() => setMobileTab("progress")}
          className={`rounded-2xl border px-4 py-3 text-xs font-bold uppercase tracking-[0.18em] ${
            showProgressSection
              ? "border-primary/20 bg-primary/10 text-primary"
              : "border-zinc-200 bg-white text-zinc-500"
          }`}
        >
          Progress
        </button>
        <button
          type="button"
          onClick={() => setMobileTab("details")}
          className={`rounded-2xl border px-4 py-3 text-xs font-bold uppercase tracking-[0.18em] ${
            showDetailsSection
              ? "border-primary/20 bg-primary/10 text-primary"
              : "border-zinc-200 bg-white text-zinc-500"
          }`}
        >
          Details
        </button>
      </div>

      <div className={`${showProgressSection ? "block" : "hidden"} space-y-5 lg:block`}>
        <SectionCard title="Conversation Goals">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-lg font-black text-zinc-950">
                {lessonState?.progress
                  ? `${lessonState.progress.completed}/${lessonState.progress.total} goals`
                  : "Waiting"}
              </p>
              <p className="mt-1 text-sm text-zinc-500">
                {lessonState?.status === "completed"
                  ? "The guided conversation is ready to finish."
                  : getLessonStatusLabel(lessonState)}
              </p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${statusClassName}`}>
              {connectionState}
            </span>
          </div>

          {lessonState?.progress ? (
            <div className="mt-4 h-3 overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${lessonState.progress.percent}%` }}
              />
            </div>
          ) : null}

          <div className="mt-5 space-y-3">
            {objectives.length > 0 ? objectives.map((objective, index) => {
              const isCompleted = index < completedCount;
              const isActive = !lessonState?.should_end && index === activeIndex;
              const toneClass = isCompleted
                ? "border-emerald-200 bg-emerald-50"
                : isActive
                  ? "border-primary/20 bg-primary/[0.05]"
                  : "border-zinc-200 bg-zinc-50";

              return (
                <div key={`${objective}-${index}`} className={`rounded-2xl border p-4 ${toneClass}`}>
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-black ${
                        isCompleted
                          ? "bg-emerald-600 text-white"
                          : isActive
                            ? "bg-primary text-white"
                            : "bg-white text-zinc-500"
                      }`}
                    >
                      {isCompleted ? <CheckCircle size={14} weight="fill" /> : index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-semibold leading-relaxed text-zinc-900">{objective}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-zinc-500">
                        {isCompleted ? "Completed" : isActive ? "Current goal" : "Upcoming"}
                      </p>
                    </div>
                  </div>
                </div>
              );
            }) : (
              <p className="text-sm text-zinc-500">Goals will appear once the conversation is ready.</p>
            )}
          </div>
        </SectionCard>
      </div>

      <div className={`${showDetailsSection ? "block" : "hidden"} space-y-5 lg:block`}>
        <SectionCard title="Answer Coverage">
          <div className="space-y-4">
            <CoverageGroup
              title="Still To Mention"
              items={missingPoints}
              emptyCopy="No missing points right now."
            />
            <CoverageGroup
              title="Already Covered"
              items={coveredPoints}
              emptyCopy="Covered points will appear after each answer."
              tone="success"
            />
          </div>
        </SectionCard>

        <SectionCard title="Session Details">
          <div className="grid grid-cols-2 gap-3">
            <StatCard icon={Clock} label="Duration" value={formatDuration(durationSeconds)} />
            <StatCard icon={BookOpen} label="Turns" value={String(turnCount).padStart(2, "0")} />
            <StatCard icon={Sparkle} label="Mode" value={lessonState ? "Guided" : "Voice"} />
            <StatCard
              icon={Lightning}
              label="Status"
              value={RECORDING_COPY[recordingState] || RECORDING_COPY.idle}
            />
          </div>

          <div className="mt-4 rounded-2xl border border-zinc-200 bg-zinc-50/80 p-4">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Partner Persona</p>
            <p className="mt-2 text-sm font-semibold text-zinc-900">
              {lessonState?.persona || "Friendly speaking partner"}
            </p>
            {lessonState?.current_objective ? (
              <p className="mt-3 text-sm leading-relaxed text-zinc-600">
                {lessonState.current_objective.remaining_follow_ups} follow-up
                {lessonState.current_objective.remaining_follow_ups === 1 ? "" : "s"} left for this goal.
              </p>
            ) : null}
            {lessonState?.end_reason ? (
              <p className="mt-3 text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                {formatLessonEndReason(lessonState.end_reason)}
              </p>
            ) : null}
          </div>

          <div className="mt-4 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.18em] text-zinc-400">
            <span>Session ID</span>
            <span className="rounded-full bg-zinc-100 px-2 py-1 font-mono text-zinc-700">
              {sessionId || "pending"}
            </span>
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Actions">
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
      </SectionCard>
    </aside>
  );
};

export default MetricsSidebar;
