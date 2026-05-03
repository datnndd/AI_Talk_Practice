import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  ChatCenteredDots,
  Check,
  Microphone,
  Translate,
  CircleNotch,
} from "@phosphor-icons/react";
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

const RealtimeCorrectionCard = ({ correctedText, corrections = [] }) => {
  if (!correctedText && corrections.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 shadow-sm"
    >
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700">
        <Check size={14} weight="bold" />
        Correction
      </div>
      {correctedText ? (
        <p className="mt-2 text-sm font-semibold leading-relaxed text-emerald-950">{correctedText}</p>
      ) : null}
      {corrections.length > 0 ? (
        <div className="mt-3 space-y-2">
          {corrections.map((item, index) => (
            <div key={`${item.corrected_text || item.original_text}-${index}`} className="rounded-lg bg-card/85 px-3 py-2">
              <p className="text-xs font-semibold text-zinc-700">
                {(item.original_text || "").trim()} {"->"} {(item.corrected_text || "").trim()}
              </p>
              {item.explanation ? (
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{item.explanation}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </motion.div>
  );
};

const MessageBubble = ({
  content,
  role,
  isAI,
  isLive = false,
  targetLanguage = "vi",
  correctedText = "",
  corrections = [],
}) => {
  const isNotice = role === "notice" || role === "system";
  const isCompletion = isCompletionNotice(role, content);
  const alignClass = isNotice ? "justify-center" : isAI ? "justify-start" : "justify-end";
  const bubbleClass = isCompletion
    ? "bg-[var(--success-bg)] text-[var(--success-text)]"
    : isNotice
      ? "bg-[var(--chip-neutral-bg)] text-[var(--chip-neutral-text)]"
      : isAI
        ? "rounded-bl-md bg-card/80 text-[var(--page-fg)]"
        : "rounded-br-md bg-primary text-white";


  const [translation, setTranslation] = useState("");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationError, setTranslationError] = useState("");

  const handleTranslate = async () => {
    if (translation || isTranslating || isLive) return;
    setIsTranslating(true);
    setTranslationError("");
    try {
      const response = await practiceApi.translate({ text: content, targetLanguage });
      setTranslation(response.translated_text);
    } catch {
      setTranslationError("Không thể dịch nội dung này.");
    } finally {
      setIsTranslating(false);
    }
  };

  return (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className={`flex items-end gap-2 ${alignClass}`}
  >
    {isAI && !isNotice ? (
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-card/80 text-base shadow-sm">👩‍🦰</span>
    ) : null}

    <div className="flex max-w-[75%] flex-col gap-2">
      <div
        className={`relative rounded-2xl p-3.5 shadow-[0_16px_40px_-28px_rgba(15,23,42,0.8)] group ${bubbleClass} ${isLive ? "border border-dashed border-current/30" : ""}`}
      >
        <p className={`text-sm font-medium leading-relaxed ${isLive ? "italic opacity-70" : ""}`}>{content}</p>
        
        {isAI && !isLive && !isNotice && !translation && (
          <button
            onClick={handleTranslate}
            disabled={isTranslating}
            title="Dịch câu này"
            className="absolute -right-10 top-2 rounded-full p-2 text-[var(--page-muted)] opacity-0 transition-opacity hover:bg-white/10 hover:text-primary group-hover:opacity-100 disabled:opacity-50"
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

      {!isAI && !isLive ? (
        <RealtimeCorrectionCard correctedText={correctedText} corrections={corrections} />
      ) : null}
    </div>
  </motion.div>
  );
};

const ListeningBubble = () => (
  <motion.div
    initial={{ opacity: 0, scale: 0.96, y: 10 }}
    animate={{ opacity: 1, scale: 1, y: 0 }}
    className="flex items-end justify-end gap-2"
  >
    <div className="max-w-[75%] rounded-2xl rounded-br-md bg-primary px-5 py-4 text-white shadow-[0_16px_40px_-28px_rgba(15,23,42,0.8)]">
      <div className="flex items-center gap-3">
        <Microphone size={18} weight="fill" />
        <span className="text-sm font-semibold leading-relaxed">Listening</span>
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
              className="w-1 rounded-full bg-white"
            />
          ))}
        </div>
      </div>
    </div>
  </motion.div>
);

const formatScenarioDuration = (seconds) => {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "3 - 5 minutes";
  }

  const minutes = Math.max(1, Math.round(seconds / 60));
  return `${minutes} minute${minutes === 1 ? "" : "s"}`;
};

const formatCountdown = (seconds) => {
  const safeSeconds = Math.max(0, Math.floor(Number(seconds) || 0));
  const minutes = Math.floor(safeSeconds / 60);
  const restSeconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(restSeconds).padStart(2, "0")}`;
};

const ChatWindow = ({
  scenario,
  guidance,
  messages,
  assistantDraft,
  isListening = false,
  durationSeconds = 0,
  timeLimitSeconds = null,
  userNativeLanguage = "vi",
}) => {
  const endRef = useRef(null);
  const scenarioTitle = scenario?.title || guidance?.topic || "Practice session";
  const difficulty = scenario?.difficulty || "Easy";
  const countdownLimit = timeLimitSeconds || scenario?.estimated_duration || 0;
  const remainingSeconds = countdownLimit ? Math.max(0, countdownLimit - durationSeconds) : null;
  const descriptionText = (scenario?.description || "").trim();
  const introMessage = descriptionText
    ? messages.find((message) => message.role === "assistant" && (message.content || "").trim() === descriptionText)
    : null;
  const visibleMessages = introMessage
    ? messages.filter((message) => message.id !== introMessage.id)
    : messages;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [assistantDraft, messages]);

  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-card/40 backdrop-blur">
      <header className="border-b border-border px-4 py-3 lg:px-6">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="truncate text-base font-black leading-tight text-[var(--page-fg)]">
              {scenarioTitle}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs font-semibold text-[var(--page-subtle)]">
              <span>{formatScenarioDuration(scenario?.estimated_duration)}</span>
              <span className="h-1 w-1 rounded-full bg-[var(--page-subtle)]/50" />
              <span className="capitalize">{difficulty}</span>
            </div>
          </div>
          {remainingSeconds !== null ? (
            <div className="shrink-0 rounded-full bg-[var(--chip-bg)] px-3 py-1.5 text-xs font-semibold text-[var(--chip-text)]">
              ⏱ {formatCountdown(remainingSeconds)}
            </div>
          ) : null}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8">
        <div>
          {messages.length === 0 && !assistantDraft && !isListening ? (
            <div className="mx-auto mt-4 max-w-xl rounded-2xl border border-dashed border-border bg-card/70 p-8 text-center shadow-sm">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <ChatCenteredDots size={28} weight="fill" />
              </div>
              <p className="mt-5 text-lg font-bold text-[var(--page-fg)]">Cuộc hội thoại sẽ xuất hiện tại đây</p>
              <p className="mt-2 text-sm leading-relaxed text-[var(--page-muted)]">
                Hãy bắt đầu nói khi bạn đã sẵn sàng. Câu trả lời của bạn và phản hồi từ đối tác sẽ được lưu lại.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {introMessage ? (
                <MessageBubble
                  key={introMessage.id}
                  content={introMessage.content}
                  role={introMessage.role}
                  isAI
                  targetLanguage={userNativeLanguage}
                  correctedText={introMessage.correctedText}
                  corrections={introMessage.corrections || []}
                />
              ) : null}
              {visibleMessages.map((message) => (
                <MessageBubble
                  key={message.id}
                  content={message.content}
                  role={message.role}
                  isAI={message.role === "assistant"}
                  targetLanguage={userNativeLanguage}
                  correctedText={message.correctedText}
                  corrections={message.corrections || []}
                />
              ))}

              {isListening ? (
                <ListeningBubble />
              ) : null}

              {assistantDraft ? (
                <MessageBubble content={assistantDraft} role="assistant" isAI isLive targetLanguage={userNativeLanguage} />
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

