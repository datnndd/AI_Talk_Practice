import { motion } from "framer-motion";
import {
  ArrowsClockwise,
  Microphone,
  PauseCircle,
  SpeakerSlash,
  Sparkle,
  WarningCircle,
} from "@phosphor-icons/react";
import {
  getLessonStatusCopy,
} from "@/features/practice/utils/lessonState";

const STATUS_COPY = {
  closed: "Preparing the conversation session.",
  idle: "Tap the mic when you're ready to speak.",
  recording: "Listening now. Speak naturally, then stop when you finish.",
  processing: "Processing your full speech for the clearest transcript.",
  assistant: "Your conversation partner is replying with text and audio.",
  interrupting: "Stopping the current reply.",
  connecting: "Connecting your live conversation session.",
  reconnecting: "Reconnecting your live conversation session.",
};

const TypewriterInput = ({
  partialTranscript,
  recordingState,
  connectionState,
  onToggleRecording,
  onReconnect,
  disabled,
  error,
  lessonState,
  hint,
  isHintLoading = false,
  onRequestHint,
}) => {
  const isRecording = recordingState === "recording";
  const isAssistantSpeaking = recordingState === "assistant";
  const isInterrupting = recordingState === "interrupting";
  const lessonStatusCopy = getLessonStatusCopy({ lessonState, recordingState, connectionState });
  const transcript = partialTranscript || lessonStatusCopy || STATUS_COPY[recordingState] || STATUS_COPY.idle;
  const buttonLabel =
    connectionState === "ready"
      ? isRecording
        ? "Stop Turn"
        : isAssistantSpeaking
          ? "Stop Reply"
          : isInterrupting
            ? "Stopping..."
            : "Start Speaking"
      : connectionState === "connecting" || connectionState === "reconnecting"
        ? connectionState === "reconnecting" ? "Reconnecting..." : "Connecting..."
        : "Connect Session";

  const buttonIcon = isRecording
    ? <PauseCircle weight="fill" size={22} />
    : isAssistantSpeaking
      ? <SpeakerSlash weight="fill" size={22} />
      : <Microphone weight="fill" size={22} />;

  const buttonClassName = disabled
    ? "cursor-not-allowed bg-zinc-300 shadow-none"
    : isRecording
      ? "bg-rose-500 shadow-rose-500/25"
      : isAssistantSpeaking
        ? "bg-amber-500 shadow-amber-500/25"
        : "bg-primary shadow-primary/30";
  const canRequestHint =
    Boolean(onRequestHint) &&
    Boolean(lessonState?.lesson_id) &&
    Boolean(lessonState?.current_objective?.objective_id) &&
    !lessonState?.should_end &&
    recordingState !== "recording" &&
    recordingState !== "processing" &&
    recordingState !== "assistant";
  const sampleAnswers = hint?.sample_answers?.length
    ? hint.sample_answers
    : hint?.sample_answer
      ? [hint.sample_answer]
      : [];

  return (
    <footer className="rounded-lg border border-zinc-200 bg-white shadow-[0_20px_54px_-42px_rgba(15,23,42,0.55)]">
      {hint ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-b border-sky-100 bg-sky-50/80 p-3 text-sky-950"
        >
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">
            <Sparkle weight="fill" size={12} />
            Guided Hint
          </div>
          <div className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <div className="space-y-3">
              {hint.question ? (
                <div className="rounded-lg border border-sky-200 bg-white/85 p-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Current Question</p>
                  <p className="mt-2 text-sm font-semibold leading-relaxed text-zinc-800">{hint.question}</p>
                </div>
              ) : null}
              <div className="rounded-lg border border-sky-200 bg-white/85 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">AI đang hỏi gì?</p>
                <p className="mt-2 text-sm font-semibold leading-relaxed">{hint.analysis_vi}</p>
              </div>
              <div className="rounded-lg border border-sky-200 bg-white/85 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Nên trả lời thế nào?</p>
                <p className="mt-2 text-sm leading-relaxed text-sky-800">{hint.answer_strategy_vi}</p>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {hint.keywords?.map((keyword) => (
                  <span
                    key={keyword}
                    className="inline-flex rounded-lg border border-sky-200 bg-white px-3 py-2 text-xs font-bold uppercase tracking-wide text-sky-700"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-3">
              <div className="rounded-lg border border-white/70 bg-white/85 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Sample Answers</p>
                <div className="mt-2 space-y-2">
                  {sampleAnswers.map((answer, index) => (
                    <p key={`${answer}-${index}`} className="rounded-lg bg-zinc-50 px-3 py-2 text-sm leading-relaxed text-zinc-700">
                      {answer}
                    </p>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-white/70 bg-white/85 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Easy Version</p>
                <p className="mt-2 text-sm leading-relaxed text-zinc-700">{hint.sample_answer_easy}</p>
              </div>
            </div>
          </div>
        </motion.div>
      ) : null}

      <div className="flex flex-col gap-3 p-3 xl:flex-row xl:items-center">
        <div className="min-w-0 flex-1 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Speech-to-Text</p>
          <p className={`mt-1 min-h-6 text-sm leading-relaxed ${partialTranscript ? "font-semibold text-zinc-950" : "text-zinc-500"}`}>
            {transcript}
          </p>
          {error ? (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-600">
              <WarningCircle size={18} weight="fill" className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-3">
          <motion.button
            whileHover={{ scale: disabled ? 1 : 1.02 }}
            whileTap={{ scale: disabled ? 1 : 0.98 }}
            onClick={onToggleRecording}
            disabled={disabled}
            className={`flex min-w-40 items-center justify-center gap-3 rounded-lg px-5 py-3 text-sm font-bold text-white shadow-lg transition-all ${buttonClassName}`}
          >
            {buttonIcon}
            <span>{buttonLabel}</span>
          </motion.button>

          {canRequestHint ? (
            <button
              onClick={onRequestHint}
              disabled={isHintLoading}
              className="flex min-w-32 items-center justify-center gap-2 rounded-lg border border-primary/20 bg-white px-4 py-3 text-sm font-bold text-primary transition-colors hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Sparkle weight="fill" size={18} />
              <span>{isHintLoading ? "Loading..." : "Get Hint"}</span>
            </button>
          ) : null}

          <button
            onClick={onReconnect}
            disabled={connectionState === "connecting" || connectionState === "reconnecting"}
            className="flex h-12 w-12 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-500 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
            title="Reconnect session"
          >
            <ArrowsClockwise size={20} />
          </button>
        </div>
      </div>
    </footer>
  );
};

export default TypewriterInput;
