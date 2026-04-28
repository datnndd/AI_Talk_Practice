import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  ChatCenteredText,
  CheckCircle,
  Clock,
  Lightning,
  Textbox,
  Trophy,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { useNavigate, useParams } from "react-router-dom";
import { practiceApi } from "@/features/practice/api/practiceApi";
import { formatLessonEndReason } from "@/features/practice/utils/lessonState";

const formatDuration = (seconds) => {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "Not available";
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes <= 0) {
    return `${remainingSeconds}s`;
  }
  return `${minutes}m ${remainingSeconds}s`;
};

const SKILL_META = {
  fluency: { label: "Fluency", icon: Lightning, color: "bg-purple-50 border-purple-200 text-purple-700" },
  grammar: { label: "Grammar", icon: Textbox, color: "bg-amber-50 border-amber-200 text-amber-700" },
  vocabulary: { label: "Vocabulary", icon: ChatCenteredText, color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  relevance: { label: "Relevance", icon: CheckCircle, color: "bg-teal-50 border-teal-200 text-teal-700" },
};

const VISIBLE_SKILL_KEYS = new Set(Object.keys(SKILL_META));

const ScoreRing = ({ score, size = 80 }) => {
  const pct = Math.min(100, Math.max(0, (score / 10) * 100));
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 70 ? "#10b981" : pct >= 45 ? "#f59e0b" : "#ef4444";
  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e5e7eb" strokeWidth={8} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={8}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
      />
    </svg>
  );
};

const SkillCard = ({ skillKey, value }) => {
  const meta = SKILL_META[skillKey] || { label: skillKey, color: "bg-zinc-50 border-zinc-200 text-zinc-700" };
  const Icon = meta.icon;
  const avg = typeof value === "object" ? value.avg : value;
  return (
    <div className={`rounded-xl border p-4 ${meta.color}`}>
      <div className="flex items-center gap-2">
        {Icon && <Icon size={16} weight="bold" />}
        <p className="text-[10px] font-black uppercase tracking-[0.18em]">{meta.label}</p>
      </div>
      <p className="mt-2 text-2xl font-black">{Number(avg || 0).toFixed(1)}</p>
    </div>
  );
};

const CorrectionCard = ({ correction, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.05 }}
    className="rounded-xl border border-rose-100 bg-rose-50 p-4"
  >
    <div className="flex items-start gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-rose-600 mb-2">Original</p>
        <p className="text-sm text-rose-900 line-through opacity-70">
          {correction.original || correction.original_text}
        </p>
      </div>
      <ArrowRight size={16} className="mt-5 shrink-0 text-rose-400" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-600 mb-2">Correction</p>
        <p className="text-sm font-semibold text-emerald-900">
          {correction.suggestion || correction.corrected_text}
        </p>
      </div>
    </div>
    {correction.explanation && (
      <p className="mt-3 border-t border-rose-200 pt-3 text-xs leading-relaxed text-zinc-600">
        {correction.explanation}
      </p>
    )}
  </motion.div>
);

const SessionResultPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const sessionId = Number(id);
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isFinite(sessionId)) {
      setError("Invalid session id.");
      setIsLoading(false);
      return undefined;
    }

    let isMounted = true;
    const loadSession = async () => {
      setIsLoading(true);
      setError("");
      try {
        const response = await practiceApi.getSession(sessionId);
        if (isMounted) {
          setSession(response);
        }
      } catch (loadError) {
        if (isMounted) {
          setError(loadError?.response?.data?.detail || "Unable to load this session result.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadSession();
    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  const endReason = useMemo(() => {
    const rawReason = session?.metadata?.end_reason || session?.metadata?.reason;
    return formatLessonEndReason(rawReason) || "Session ended";
  }, [session]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="mx-auto max-w-2xl rounded-lg border border-rose-100 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-3 text-rose-600">
          <WarningCircle size={24} weight="fill" className="mt-0.5 shrink-0" />
          <div>
            <h1 className="font-display text-2xl font-black text-zinc-950">Session result unavailable</h1>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{error || "This session could not be loaded."}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-zinc-950 px-5 py-3 text-sm font-bold text-white"
        >
          <ArrowLeft size={18} weight="bold" />
          Back to topics
        </button>
      </div>
    );
  }

  const messages = session.messages || [];
  const userMessages = messages.filter((m) => m.role === "user");
  const score = session.score;
  const scoreMeta = score?.metadata || {};
  const skillBreakdown = Object.fromEntries(
    Object.entries(score?.skill_breakdown || {}).filter(([key]) => VISIBLE_SKILL_KEYS.has(key))
  );
  const strengths = scoreMeta.strengths || [];
  const improvements = scoreMeta.improvements || [];
  const corrections = scoreMeta.corrections || [];
  const nextSteps = scoreMeta.next_steps || [];
  const objectiveCompletion = scoreMeta.objective_completion;

  const completionBadge = {
    completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: CheckCircle },
    partial: { label: "Partial", color: "bg-amber-100 text-amber-700 border-amber-200", icon: WarningCircle },
    not_completed: { label: "Not completed", color: "bg-rose-100 text-rose-700 border-rose-200", icon: XCircle },
  }[objectiveCompletion] || null;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <button
        type="button"
        onClick={() => navigate("/dashboard")}
        className="inline-flex w-fit items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-bold text-zinc-700 shadow-sm transition hover:bg-zinc-50"
      >
        <ArrowLeft size={18} weight="bold" />
        Back to topics
      </button>

      {/* Header */}
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Practice Result</p>
        <h1 className="mt-2 font-display text-3xl font-black tracking-tight text-zinc-950">
          {session.scenario?.title || "Conversation session"}
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          {session.scenario?.description || "Your speaking session is ready for review."}
        </p>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Status</p>
            <p className="mt-2 text-lg font-black capitalize text-zinc-950">{session.status}</p>
          </div>
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Reason</p>
            <p className="mt-2 text-lg font-black text-zinc-950">{endReason}</p>
          </div>
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
            <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">
              <Clock size={14} weight="bold" />
              Duration
            </div>
            <p className="mt-2 text-lg font-black text-zinc-950">{formatDuration(session.duration_seconds)}</p>
          </div>
        </div>
      </section>

      {/* Overall Score + Objective */}
      {score && (
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Score</p>
          <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="flex flex-col items-center gap-2">
              <div className="relative flex items-center justify-center">
                <ScoreRing score={score.overall_score} size={100} />
                <div className="absolute flex flex-col items-center">
                  <span className="text-2xl font-black text-zinc-900">{Number(score.overall_score || 0).toFixed(1)}</span>
                  <span className="text-[9px] font-black uppercase tracking-wider text-zinc-500">overall</span>
                </div>
              </div>
              {completionBadge && (() => {
                const BadgeIcon = completionBadge.icon;
                return (
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-black ${completionBadge.color}`}>
                    <BadgeIcon size={13} weight="fill" />
                    {completionBadge.label}
                  </span>
                );
              })()}
            </div>
            <div className="flex-1">
              {score.feedback_summary && (
                <p className="text-sm leading-relaxed text-zinc-700 italic">{score.feedback_summary}</p>
              )}
              {Object.keys(skillBreakdown).length > 0 && (
                <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {Object.entries(skillBreakdown).map(([key, val]) => (
                    <SkillCard key={key} skillKey={key} value={val} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Strengths + Improvements */}
      {(strengths.length > 0 || improvements.length > 0) && (
        <div className="grid gap-4 sm:grid-cols-2">
          {strengths.length > 0 && (
            <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
              <div className="flex items-center gap-2">
                <Trophy size={18} weight="fill" className="text-emerald-600" />
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-emerald-700">Strengths</p>
              </div>
              <ul className="mt-4 space-y-2">
                {strengths.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-emerald-950">
                    <CheckCircle size={16} weight="fill" className="mt-0.5 shrink-0 text-emerald-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {improvements.length > 0 && (
            <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
              <div className="flex items-center gap-2">
                <WarningCircle size={18} weight="fill" className="text-amber-600" />
                <p className="text-[11px] font-black uppercase tracking-[0.24em] text-amber-700">Areas to improve</p>
              </div>
              <ul className="mt-4 space-y-2">
                {improvements.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-950">
                    <ArrowRight size={16} className="mt-0.5 shrink-0 text-amber-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      {/* Corrections */}
      {corrections.length > 0 && (
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Language Corrections</p>
          <h2 className="mt-1 font-display text-xl font-black text-zinc-950">{corrections.length} correction{corrections.length !== 1 ? "s" : ""}</h2>
          <div className="mt-4 space-y-3">
            {corrections.map((c, i) => (
              <CorrectionCard key={i} correction={c} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Next Steps */}
      {nextSteps.length > 0 && (
        <section className="rounded-xl border border-primary/20 bg-primary/5 p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Next Steps</p>
          <ul className="mt-4 space-y-2">
            {nextSteps.map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-800">
                <ArrowRight size={16} weight="bold" className="mt-0.5 shrink-0 text-primary" />
                {step}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Conversation transcript */}
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Saved Conversation</p>
            <h2 className="mt-1 font-display text-2xl font-black text-zinc-950">{userMessages.length} speaking turns</h2>
          </div>
          <ChatCenteredText size={28} weight="fill" className="text-primary" />
        </div>

        <div className="mt-5 space-y-3">
          {messages.length ? messages.map((message) => (
            <div
              key={message.id}
              className={`rounded-lg border px-4 py-3 ${
                message.role === "assistant"
                  ? "border-zinc-200 bg-zinc-50 text-zinc-800"
                  : "border-primary/20 bg-[#eef6ff] text-zinc-950"
              }`}
            >
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">
                {message.role === "assistant" ? "Partner" : "You"}
              </p>
              <p className="mt-2 text-sm leading-relaxed">{message.content}</p>
            </div>
          )) : (
            <p className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-5 text-sm text-zinc-500">
              No clear speaking turns were saved for this session.
            </p>
          )}
        </div>
      </section>
    </div>
  );
};

export default SessionResultPage;
