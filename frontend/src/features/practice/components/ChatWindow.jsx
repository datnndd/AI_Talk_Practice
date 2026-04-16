import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  ChatCenteredDots,
  ClipboardText,
  Flag,
  Microphone,
  Robot,
  Target,
  User,
} from "@phosphor-icons/react";

const compactItems = (items = [], limit = 3) => {
  if (typeof items === "string" && items.trim()) {
    return [items.trim()].slice(0, limit);
  }

  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter((item) => typeof item === "string" && item.trim())
    .map((item) => item.trim())
    .slice(0, limit);
};

const ContextRow = ({ icon: Icon, label, value }) => {
  if (!value) {
    return null;
  }

  return (
    <div className="flex min-w-0 items-start gap-3 border-t border-zinc-200 px-1 py-3 first:border-t-0 lg:border-l lg:border-t-0 lg:px-4 lg:first:border-l-0">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-900 text-white">
        <Icon size={16} weight="fill" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-500">{label}</p>
        <p className="mt-1 text-sm font-semibold leading-relaxed text-zinc-900">{value}</p>
      </div>
    </div>
  );
};

const ScenarioContext = ({ scenario, lessonState, guidance }) => {
  const learningObjectives = compactItems(scenario?.learning_objectives);
  const targetSkills = compactItems(scenario?.target_skills);
  const focusItems = lessonState?.lesson_goals?.length
    ? compactItems(lessonState.lesson_goals, 4)
    : compactItems(guidance?.evaluationFocus, 4);

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-zinc-200 bg-white p-4 shadow-[0_18px_40px_-34px_rgba(15,23,42,0.32)]"
    >
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            <ClipboardText size={13} weight="fill" />
            Scenario
          </div>
          <h2 className="mt-2 font-display text-2xl font-black tracking-tight text-zinc-950">
            {scenario?.title || guidance?.topic || "Practice session"}
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-zinc-600">
            {scenario?.description || guidance?.assignedTask || "Stay on topic and answer naturally."}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 xl:w-64">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-500">Partner</p>
          <p className="mt-1 text-sm font-semibold leading-relaxed text-zinc-900">
            {lessonState?.persona || "Friendly speaking partner"}
          </p>
        </div>
      </div>

      <div className="mt-4 grid rounded-lg border border-zinc-200 bg-zinc-50 px-3 lg:grid-cols-2">
        <ContextRow
          icon={Target}
          label="Your Task"
          value={lessonState?.assigned_task || guidance?.assignedTask}
        />
        <ContextRow
          icon={Flag}
          label="Current Goal"
          value={lessonState?.current_objective?.goal || learningObjectives[0] || targetSkills[0]}
        />
      </div>

      {focusItems.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {focusItems.map((item) => (
            <span
              key={item}
              className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-bold text-zinc-700"
            >
              {item}
            </span>
          ))}
        </div>
      ) : null}
    </motion.article>
  );
};

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
      <header className="border-b border-zinc-200 bg-white px-5 py-3">
        <div className="flex items-start gap-3">
          <span className="mt-1 h-9 w-1 shrink-0 rounded-full bg-primary" />
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-zinc-500">
              Current Prompt
            </p>
            <p className="mt-1 text-sm font-semibold leading-relaxed text-zinc-800">
              {lessonState?.current_question || "Start the session and answer the partner naturally."}
            </p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <ScenarioContext scenario={scenario} lessonState={lessonState} guidance={guidance} />

        {messages.length === 0 && !partialTranscript && !assistantDraft && !isListening ? (
          <div className="mx-auto mt-8 max-w-xl rounded-lg border border-dashed border-zinc-300 bg-white/80 p-8 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <ChatCenteredDots size={28} weight="fill" />
            </div>
            <p className="mt-5 text-lg font-bold text-zinc-950">Your conversation will appear here.</p>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              Speak when ready. Your answer and the partner reply will stay with the scenario context.
            </p>
          </div>
        ) : (
          <div className="mt-6 space-y-6">
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

        <div ref={endRef} />
      </div>
    </section>
  );
};

export default ChatWindow;
