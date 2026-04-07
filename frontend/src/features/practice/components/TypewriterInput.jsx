import { motion } from "framer-motion";
import {
  ArrowsClockwise,
  Microphone,
  PauseCircle,
  Sparkle,
  WarningCircle,
} from "@phosphor-icons/react";

const STATUS_COPY = {
  closed: "Tap the mic to connect to the live conversation session.",
  idle: "Tap the mic when you're ready to speak.",
  recording: "Listening now. Speak naturally, then stop to send your turn.",
  processing: "Processing your speech and drafting the assistant reply.",
  assistant: "The assistant is responding with text and audio.",
  connecting: "Connecting your live conversation session.",
};

const TypewriterInput = ({
  partialTranscript,
  recordingState,
  connectionState,
  onToggleRecording,
  onReconnect,
  disabled,
  error,
}) => {
  const isRecording = recordingState === "recording";
  const transcript = partialTranscript || STATUS_COPY[recordingState] || STATUS_COPY.idle;
  const buttonLabel =
    connectionState === "ready"
      ? isRecording
        ? "Stop Turn"
        : "Start Speaking"
      : connectionState === "connecting"
        ? "Connecting..."
        : "Connect Session";

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
              className={`flex min-w-40 items-center justify-center gap-3 rounded-full px-5 py-4 text-sm font-bold text-white shadow-lg transition-all ${
                disabled
                  ? "cursor-not-allowed bg-zinc-300 shadow-none"
                  : isRecording
                    ? "bg-rose-500 shadow-rose-500/25"
                    : "bg-primary shadow-primary/30"
              }`}
            >
              {isRecording ? <PauseCircle weight="fill" size={22} /> : <Microphone weight="fill" size={22} />}
              <span>{buttonLabel}</span>
            </motion.button>

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
      </div>
    </footer>
  );
};

export default TypewriterInput;
