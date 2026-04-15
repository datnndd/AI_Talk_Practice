import { CheckCircle, ChatCircleDots, Sparkle, Target } from "@phosphor-icons/react";
import { getLessonStatusCopy } from "@/features/practice/utils/lessonState";

const Badge = ({ label, value, tone = "neutral" }) => {
  const toneClass =
    tone === "primary"
      ? "border-primary/20 bg-primary/8 text-primary"
      : tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-zinc-200 bg-white text-zinc-700";

  return (
    <div className={`rounded-2xl border px-4 py-3 ${toneClass}`}>
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-70">{label}</p>
      <p className="mt-1 text-sm font-semibold leading-relaxed">{value}</p>
    </div>
  );
};

const ChipGroup = ({ title, items, emptyCopy, tone = "sky" }) => {
  const styles =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-sky-200 bg-sky-50 text-sky-700";

  return (
    <div className="rounded-3xl border border-white/60 bg-white/80 p-4">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length > 0 ? (
          items.map((item) => (
            <span
              key={item}
              className={`inline-flex rounded-full border px-3 py-2 text-xs font-bold ${styles}`}
            >
              {item}
            </span>
          ))
        ) : (
          <span className="text-sm text-zinc-500">{emptyCopy}</span>
        )}
      </div>
    </div>
  );
};

const CurrentQuestionCard = ({
  lessonState,
  guidance,
  connectionState,
  recordingState,
}) => {
  const statusCopy = getLessonStatusCopy({ lessonState, recordingState, connectionState });
  const missingPoints = lessonState?.current_objective?.missing_points || [];
  const matchedPoints = lessonState?.current_objective?.matched_points || [];

  return (
    <section className="rounded-[32px] border border-white/40 bg-white/78 p-6 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.35)] backdrop-blur-xl">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.22em] text-primary">
              <ChatCircleDots size={12} weight="fill" />
              Current Step
            </div>
            <h2 className="mt-3 font-display text-3xl font-black tracking-tight text-zinc-950">
              {lessonState?.current_question || "Preparing your opening question..."}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-600">
              {statusCopy || guidance?.completion?.detail || "The lesson guide will tell the learner what to do next."}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[320px]">
            <Badge
              label="Current Goal"
              value={lessonState?.current_objective?.goal || "Waiting for lesson state"}
              tone="primary"
            />
            <Badge
              label="Partner Persona"
              value={lessonState?.persona || "Friendly speaking partner"}
            />
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div className="rounded-[28px] border border-zinc-200 bg-zinc-50/80 p-5">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">
              <Target size={12} weight="fill" />
              Task Frame
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <Badge label="Topic" value={lessonState?.topic || guidance?.topic || "Scenario topic"} />
              <Badge label="Assigned Task" value={lessonState?.assigned_task || guidance?.assignedTask || "Follow the current scenario prompt."} />
            </div>
          </div>

          <div className="rounded-[28px] border border-zinc-200 bg-zinc-50/80 p-5">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">
              <Sparkle size={12} weight="fill" />
              Progress Signal
            </div>
            <p className="mt-3 text-lg font-black text-zinc-950">
              {lessonState?.progress ? `${lessonState.progress.completed}/${lessonState.progress.total} goals complete` : "Waiting for progress"}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              {lessonState?.should_end
                  ? lessonState.completion_message || "The lesson is ready to close."
                : lessonState?.current_objective?.remaining_follow_ups > 0
                  ? `${lessonState.current_objective.remaining_follow_ups} follow-up prompts left for this goal.`
                  : "This goal is close to completion."}
            </p>
          </div>
        </div>

        <div className="grid gap-3 xl:grid-cols-2">
          <ChipGroup
            title="Need To Mention"
            items={missingPoints}
            emptyCopy="No missing points right now."
          />
          <ChipGroup
            title="Already Covered"
            items={matchedPoints}
            emptyCopy="Covered points will appear after the learner answers."
            tone="success"
          />
        </div>
      </div>
    </section>
  );
};

export default CurrentQuestionCard;
