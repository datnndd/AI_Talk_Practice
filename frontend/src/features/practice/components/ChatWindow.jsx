import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  ChatCenteredDots,
  Microphone,
  Robot,
  User,
} from "@phosphor-icons/react";
import ScenarioSidebar from "./ScenarioSidebar";


const MessageBubble = ({ content, isAI, isLive = false }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className={`flex max-w-[90%] items-start gap-3 ${isAI ? "" : "ml-auto flex-row-reverse"}`}
  >
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
        isAI
          ? "border-zinc-200 bg-white text-zinc-500"
          : "border-primary/20 bg-primary text-white"
      }`}
    >
      {isAI ? <Robot size={20} /> : <User size={20} />}
    </div>

    <div
      className={`rounded-lg border px-5 py-4 shadow-sm ${
        isAI
          ? "border-zinc-200 bg-white text-zinc-900"
          : "border-primary/20 bg-[#eef6ff] text-zinc-950"
      } ${isLive ? "border-dashed" : ""}`}
    >
      <p className={`text-sm leading-relaxed ${isLive ? "italic text-zinc-500" : ""}`}>{content}</p>
    </div>
  </motion.div>
);

const ListeningBubble = () => (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className="ml-auto flex max-w-[90%] flex-row-reverse items-start gap-3"
  >
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary text-white">
      <Microphone size={20} weight="fill" />
    </div>

    <div className="rounded-lg border border-primary/20 bg-[#eef6ff] px-5 py-4 text-zinc-950 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold leading-relaxed text-zinc-800">Listening</span>
        <div className="flex h-5 items-end gap-1" aria-label="Speech recognition is active">
          {[0, 1, 2, 3].map((index) => (
            <motion.span
              key={index}
              animate={{ height: [6, 18, 8] }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                ease: "easeInOut",
                delay: index * 0.12,
              }}
              className="w-1 rounded-full bg-primary"
            />
          ))}
        </div>
      </div>
    </div>
  </motion.div>
);

const ChatWindow = ({
  scenario,
  lessonState,
  guidance,
  messages,
  partialTranscript,
  assistantDraft,
  isListening = false,
}) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [assistantDraft, messages, partialTranscript]);

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-zinc-200 bg-[#fbfcfb] shadow-[0_28px_70px_-48px_rgba(15,23,42,0.55)]">
      <header className="border-b border-zinc-100 bg-white/50 px-6 py-4 backdrop-blur-md">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <ChatCenteredDots size={18} weight="fill" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-zinc-400">
                Câu hỏi hiện tại
              </p>
              <p className="mt-0.5 truncate text-sm font-bold text-zinc-900">
                {lessonState?.current_question || "Đang khởi tạo buổi học..."}
              </p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="block border-b border-zinc-100 bg-white/30 lg:hidden">
          <div className="p-4">
            <ScenarioSidebar scenario={scenario} lessonState={lessonState} guidance={guidance} />
          </div>
        </div>
        <div className="bg-zinc-50/30 px-5 py-6">
          {messages.length === 0 && !partialTranscript && !assistantDraft && !isListening ? (
            <div className="mx-auto mt-4 max-w-xl rounded-2xl border border-dashed border-zinc-300 bg-white/80 p-8 text-center shadow-sm">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <ChatCenteredDots size={28} weight="fill" />
              </div>
              <p className="mt-5 text-lg font-bold text-zinc-950">Cuộc hội thoại sẽ xuất hiện tại đây</p>
              <p className="mt-2 text-sm leading-relaxed text-zinc-500">
                Hãy bắt đầu nói khi bạn đã sẵn sàng. Câu trả lời của bạn và phản hồi từ đối tác sẽ được lưu lại.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
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

              {isListening && !partialTranscript ? (
                <ListeningBubble />
              ) : null}

              {assistantDraft ? (
                <MessageBubble content={assistantDraft} isAI isLive />
              ) : null}
            </div>
          )}
        </div>
        <div ref={endRef} />
      </div>
    </section>
  );
};

export default ChatWindow;
