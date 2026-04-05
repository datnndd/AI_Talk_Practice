import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { ChatCenteredDots, Robot, Sparkle, User } from "@phosphor-icons/react";
import CameraOverlay from "./CameraOverlay";

const MessageBubble = ({ content, isAI, isLive = false }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className={`flex items-start gap-4 max-w-[85%] ${isAI ? "" : "ml-auto flex-row-reverse"}`}
  >
    <div
      className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl border ${
        isAI
          ? "border-zinc-200 bg-zinc-100 text-zinc-500"
          : "border-primary bg-primary/10 text-primary shadow-sm"
      }`}
    >
      {isAI ? <Robot size={22} /> : <User size={22} />}
    </div>

    <div
      className={`relative overflow-hidden rounded-3xl border p-5 shadow-sm ${
        isAI
          ? "rounded-tl-none border-white/40 bg-white/70 text-zinc-900"
          : "rounded-tr-none border-primary/20 bg-white text-zinc-950"
      } ${isLive ? "border-dashed" : ""}`}
    >
      {isAI && <div className="absolute right-0 top-0 -mr-12 -mt-12 h-24 w-24 rounded-full bg-primary/5" />}
      <p className={`relative z-10 text-sm leading-relaxed ${isLive ? "italic text-zinc-500" : ""}`}>
        {content}
      </p>
    </div>
  </motion.div>
);

const ChatWindow = ({
  scenario,
  messages,
  partialTranscript,
  assistantDraft,
  connectionState,
  recordingState,
}) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [assistantDraft, messages, partialTranscript]);

  const isConnected = connectionState === "ready";

  return (
    <section className="relative flex h-full flex-col overflow-hidden rounded-4xl border border-white/20 shadow-2xl liquid-glass refraction">
      <CameraOverlay connectionState={connectionState} recordingState={recordingState} />

      <header className="flex items-end justify-between gap-6 border-b border-zinc-200/50 px-8 py-5">
        <div className="max-w-2xl">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-zinc-400">
            Scenario
          </p>
          <h1 className="mt-2 text-2xl font-black tracking-tight text-zinc-950 font-display">
            {scenario?.title || "Loading scenario..."}
          </h1>
          <p className="mt-2 text-sm font-medium leading-relaxed text-zinc-500">
            {scenario?.description || "Connecting your live conversation workspace."}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs font-bold text-zinc-950">Linguist AI</p>
            <div className="mt-0.5 flex items-center justify-end gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isConnected ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-amber-500"
                }`}
              />
              <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                {isConnected ? "Realtime" : "Waiting"}
              </span>
            </div>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20">
            <Sparkle weight="fill" size={24} />
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-8 pb-8 pt-36">
        {messages.length === 0 && !partialTranscript && !assistantDraft ? (
          <div className="mx-auto mt-10 max-w-xl rounded-3xl border border-dashed border-zinc-200 bg-white/60 p-8 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <ChatCenteredDots size={28} weight="fill" />
            </div>
            <p className="mt-5 text-lg font-bold text-zinc-950">Start the conversation with your mic.</p>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              Your transcript will appear here first, then the assistant reply and streamed audio.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                content={message.content}
                isAI={message.role === "assistant"}
              />
            ))}

            {partialTranscript ? (
              <MessageBubble content={partialTranscript} isAI={false} isLive />
            ) : null}

            {assistantDraft ? (
              <MessageBubble content={assistantDraft} isAI isLive />
            ) : null}
          </div>
        )}

        <div ref={endRef} />
      </div>
    </section>
  );
};

export default ChatWindow;
