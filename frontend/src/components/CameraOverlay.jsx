import { motion } from "framer-motion";
import { Microphone, SpeakerHigh, Waveform } from "@phosphor-icons/react";

const STATUS_COPY = {
  recording: "Listening live",
  processing: "Processing your turn",
  assistant: "AI is speaking",
  idle: "Ready for your next turn",
};

const CameraOverlay = ({ connectionState, recordingState }) => {
  const isConnected = connectionState === "ready";
  const statusLabel = STATUS_COPY[recordingState] || STATUS_COPY.idle;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute top-6 left-6 z-20 w-[min(22rem,calc(100%-3rem))] rounded-3xl border border-white/35 bg-zinc-950/70 p-5 text-white shadow-2xl backdrop-blur-xl"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-white/55">
            Voice Channel
          </p>
          <p className="mt-2 text-lg font-bold">{statusLabel}</p>
        </div>
        <div
          className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] ${
            isConnected ? "bg-emerald-400/15 text-emerald-200" : "bg-amber-400/15 text-amber-100"
          }`}
        >
          {isConnected ? "Connected" : "Offline"}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <Microphone size={18} className="text-primary" weight="fill" />
          <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.15em] text-white/55">
            Input
          </p>
          <p className="mt-1 text-sm font-semibold">
            {recordingState === "recording" ? "Hot mic" : "Standby"}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <Waveform size={18} className="text-cyan-300" weight="fill" />
          <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.15em] text-white/55">
            Model
          </p>
          <p className="mt-1 text-sm font-semibold">
            {recordingState === "processing" ? "Thinking" : "Streaming"}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <SpeakerHigh size={18} className="text-emerald-300" weight="fill" />
          <p className="mt-3 text-[11px] font-bold uppercase tracking-[0.15em] text-white/55">
            Output
          </p>
          <p className="mt-1 text-sm font-semibold">
            {recordingState === "assistant" ? "Playing" : "Queued"}
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default CameraOverlay;
