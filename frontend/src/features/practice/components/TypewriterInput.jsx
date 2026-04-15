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
  recording: "Listening now. Speak naturally, then stop to send your turn.",
  processing: "Processing your speech and choosing the next reply.",
  assistant: "Your conversation partner is replying with text and audio.",
  interrupting: "Stopping the current reply.",
  connecting: "Connecting your live conversation session.",
};

const COMPLETION_STYLES = {
  active: "border-zinc-200 bg-zinc-50 text-zinc-600",
  soon: "border-amber-200 bg-amber-50 text-amber-700",
  ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

const TypewriterInput = ({
  partialTranscript,
  recordingState,
  connectionState,
  onToggleRecording,
  onReconnect,
  disabled,
  error,
  suggestions = [],
  completion,
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
      : connectionState === "connecting"
        ? "Connecting..."
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
  const showSuggestions =
    suggestions.length > 0 &&
    !partialTranscript &&
    recordingState !== "recording" &&
    recordingState !== "processing" &&
    recordingState !== "assistant";
  const canRequestHint =
    Boolean(onRequestHint) &&
    Boolean(lessonState?.lesson_id) &&
    Boolean(lessonState?.current_objective?.objective_id) &&
    !lessonState?.should_end &&
    recordingState !== "recording" &&
    recordingState !== "processing" &&
    recordingState !== "assistant";
  const completionClassName = COMPLETION_STYLES[completion?.status] || COMPLETION_STYLES.active;
  return (
    <footer className="p-8 pt-2">
      <div className="rounded-[2rem] border border-white/40 bg-white/80 p-5 shadow-xl backdrop-blur-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
          <div className="flex-1">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
              <Sparkle weight="fill" className="text-primary/70" size={12} />
              Voice-first Practice
            </div>
            <p className={`mt-3 min-h-12 text-sm leading-relaxed ${partialTranscript ? "font-semibold text-zinc-950" : "text-zinc-500"}`}>
              {transcript}
            </p>
            {error ? (
              <div className="mt-3 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-600">
                <WarningCircle size={18} weight="fill" className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}
          </div>

          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: disabled ? 1 : 1.02 }}
              whileTap={{ scale: disabled ? 1 : 0.98 }}
              onClick={onToggleRecording}
              disabled={disabled}
              className={`flex min-w-40 items-center justify-center gap-3 rounded-full px-5 py-4 text-sm font-bold text-white shadow-lg transition-all ${buttonClassName}`}
            >
              {buttonIcon}
              <span>{buttonLabel}</span>
            </motion.button>

            {canRequestHint ? (
              <button
                onClick={onRequestHint}
                disabled={isHintLoading}
                className="flex min-w-32 items-center justify-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-4 text-sm font-bold text-primary transition-colors hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Sparkle weight="fill" size={18} />
                <span>{isHintLoading ? "Loading..." : "Get Hint"}</span>
              </button>
            ) : null}

            <button
              onClick={onReconnect}
              disabled={connectionState === "connecting"}
              className="flex h-14 w-14 items-center justify-center rounded-full border border-zinc-200 bg-white text-zinc-500 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
              title="Reconnect session"
            >
              <ArrowsClockwise size={20} />
            </button>
          </div>
        </div>

        {completion ? (
          <div className={`mt-4 rounded-3xl border px-4 py-3 ${completionClassName}`}>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em]">
              {completion.title}
            </p>
            <p className="mt-2 text-sm font-medium leading-relaxed">
              {completion.detail}
            </p>
          </div>
        ) : null}

        {hint ? (
          <div className="mt-4 rounded-3xl border border-sky-200 bg-sky-50/90 px-4 py-4 text-sky-900">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">
              <Sparkle weight="fill" size={12} />
              Guided Hint
            </div>
            <p className="mt-3 text-sm font-semibold leading-relaxed">{hint.analysis_vi}</p>
            <p className="mt-2 text-sm leading-relaxed text-sky-800">{hint.answer_strategy_vi}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {hint.keywords?.map((keyword) => (
                <span
                  key={keyword}
                  className="inline-flex rounded-full border border-sky-200 bg-white px-3 py-2 text-xs font-bold uppercase tracking-wide text-sky-700"
                >
                  {keyword}
                </span>
              ))}
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Sample Answer</p>
                <p className="mt-2 text-sm leading-relaxed text-zinc-700">{hint.sample_answer}</p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-700">Easy Version</p>
                <p className="mt-2 text-sm leading-relaxed text-zinc-700">{hint.sample_answer_easy}</p>
              </div>
            </div>
          </div>
        ) : null}

        {showSuggestions ? (
          <div className="mt-4 rounded-3xl border border-zinc-200 bg-zinc-50/80 px-4 py-4">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
              <Sparkle weight="fill" size={12} className="text-primary/70" />
              Stuck For Words?
            </div>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              Try saying one of these aloud to keep the conversation moving.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <span
                  key={suggestion}
                  className="inline-flex rounded-full border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-700 shadow-sm"
                >
                  {suggestion}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </footer>
  );
};

export default TypewriterInput;
