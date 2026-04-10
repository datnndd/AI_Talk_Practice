import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { ChatCenteredDots, Robot, User } from "@phosphor-icons/react";

const MessageBubble = ({ content, isAI, isLive = false }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className={`flex max-w-[88%] items-start gap-4 ${isAI ? "" : "ml-auto flex-row-reverse"}`}
  >
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border ${
        isAI
          ? "border-zinc-200 bg-zinc-100 text-zinc-500"
          : "border-primary/20 bg-primary/10 text-primary"
      }`}
    >
      {isAI ? <Robot size={20} /> : <User size={20} />}
    </div>

    <div
      className={`rounded-[26px] border px-5 py-4 shadow-sm ${
        isAI
          ? "rounded-tl-none border-zinc-200 bg-white text-zinc-900"
          : "rounded-tr-none border-primary/20 bg-primary/[0.04] text-zinc-950"
      } ${isLive ? "border-dashed" : ""}`}
    >
      <p className={`text-sm leading-relaxed ${isLive ? "italic text-zinc-500" : ""}`}>{content}</p>
    </div>
  </motion.div>
);

const ChatWindow = ({
  messages,
  partialTranscript,
  assistantDraft,
}) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [assistantDraft, messages, partialTranscript]);

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[32px] border border-white/40 bg-white/76 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.35)] backdrop-blur-xl">
      <header className="border-b border-zinc-200/70 px-6 py-5">
        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-zinc-400">
          Conversation Transcript
        </p>
        <p className="mt-2 text-sm leading-relaxed text-zinc-500">
          Keep this panel as history only. The live question and speaking cues are shown above the transcript.
        </p>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && !partialTranscript && !assistantDraft ? (
          <div className="mx-auto mt-10 max-w-xl rounded-[28px] border border-dashed border-zinc-200 bg-zinc-50/80 p-8 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <ChatCenteredDots size={28} weight="fill" />
            </div>
            <p className="mt-5 text-lg font-bold text-zinc-950">Transcript appears here after each turn.</p>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              The learner answer and assistant reply are stored here as conversation history, while the current speaking task stays above.
            </p>
          </div>
        ) : (
          <div className="space-y-7">
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
