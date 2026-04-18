import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  ChatCenteredDots,
  CheckCircle,
  Microphone,
  Robot,
  Info,
  User,
  Translate,
  CircleNotch,
} from "@phosphor-icons/react";
import ScenarioSidebar from "./ScenarioSidebar";
import { practiceApi } from "../api/practiceApi";


const isCompletionNotice = (role, content) => {
  if (role !== "notice" && role !== "system") return false;
  const lower = (content || "").toLowerCase();
  return (
    content.trim().startsWith("✅") ||
    (lower.includes("objective") && (lower.includes("complete") || lower.includes("achieved"))) ||
    lower.includes("nice work") ||
    lower.includes("well done")
  );
};

const MessageBubble = ({ content, role, isAI, isLive = false }) => {
  const isNotice = role === "notice" || role === "system";
  const isCompletion = isCompletionNotice(role, content);
  const alignClass = isNotice ? "mx-auto" : isAI ? "" : "ml-auto flex-row-reverse";
  const iconClass = isCompletion
    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
    : isNotice
      ? "border-amber-200 bg-amber-50 text-amber-700"
      : isAI
        ? "border-zinc-200 bg-white text-zinc-500"
        : "border-primary/20 bg-primary text-white";
  const bubbleClass = isCompletion
    ? "border-emerald-200 bg-emerald-50 text-emerald-950"
    : isNotice
      ? "border-amber-200 bg-amber-50 text-amber-950"
      : isAI
        ? "border-zinc-200 bg-white text-zinc-900"
        : "border-primary/20 bg-[#eef6ff] text-zinc-950";


  const [translation, setTranslation] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationError, setTranslationError] = useState("");

  const handleTranslate = async () => {
    if (translation || isTranslating || isLive) return;
    setIsTranslating(true);
    setTranslationError("");
    try {
      const response = await practiceApi.translate({ text: content, targetLanguage: "vi" });
      setTranslation(response.translated_text);
    } catch (err) {
      setTranslationError("Không thể dịch nội dung này.");
    } finally {
      setIsTranslating(false);
    }
  };

  return (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className={`flex max-w-[90%] items-start gap-3 ${alignClass}`}
  >
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border flex-col ${iconClass} overflow-hidden`}
    >
      {isCompletion
        ? <CheckCircle size={20} weight="fill" />
        : isNotice
          ? <Info size={20} weight="fill" />
          : isAI
            ? <Robot size={20} />
            : <User size={20} />}
    </div>

    <div className="flex flex-col gap-2">
      <div
        className={`rounded-lg border px-5 py-4 shadow-sm relative group ${bubbleClass} ${isLive ? "border-dashed" : ""}`}
      >
        <p className={`text-sm leading-relaxed ${isLive ? "italic text-zinc-500" : ""}`}>{content}</p>
        
        {isAI && !isLive && !isNotice && !translation && (
          <button
            onClick={handleTranslate}
            disabled={isTranslating}
            title="Dịch câu này"
            className="absolute -right-10 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-2 text-zinc-400 hover:text-primary rounded-full hover:bg-primary/5 disabled:opacity-50"
          >
            {isTranslating ? <CircleNotch size={18} className="animate-spin" /> : <Translate size={18} />}
          </button>
        )}
      </div>
      
      {translation && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 shadow-sm"
        >
          <div className="flex items-start gap-2">
            <Translate size={16} className="text-primary mt-0.5 shrink-0" />
            <p className="text-sm leading-relaxed text-zinc-700 italic">{translation}</p>
          </div>
        </motion.div>
      )}
      
      {translationError && (
        <p className="text-xs text-red-500 ml-1">{translationError}</p>
      )}
    </div>
  </motion.div>
  );
};

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
  assistantDraft,
  isListening = false,
}) => {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [assistantDraft, messages]);

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
          {messages.length === 0 && !assistantDraft && !isListening ? (
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
                  role={message.role}
                  isAI={message.role === "assistant"}
                />
              ))}

              {isListening ? (
                <ListeningBubble />
              ) : null}

              {assistantDraft ? (
                <MessageBubble content={assistantDraft} role="assistant" isAI isLive />
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
