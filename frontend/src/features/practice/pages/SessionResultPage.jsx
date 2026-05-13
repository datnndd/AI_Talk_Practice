import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  ChatCenteredText,
  CheckCircle,
  Crown,
  Lightning,
  Textbox,
  Trophy,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
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
const ANALYSIS_POLL_INTERVAL_MS = 3000;
const ANALYSIS_MAX_POLLS = 20;

const isTerminalAnalysisStatus = (status) => ["completed", "failed", "skipped"].includes(status);

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

const RealtimeFeedbackCard = ({ message, index }) => {
  const feedback = message.realtime_feedback;
  const isGood = Boolean(feedback?.is_good);
  const betterAnswer = feedback?.better_answer || "";
  const Icon = isGood ? CheckCircle : WarningCircle;
  const tone = isGood
    ? "border-emerald-100 bg-emerald-50 text-emerald-950"
    : "border-amber-100 bg-amber-50 text-amber-950";

  return (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.05 }}
    className={`rounded-xl border p-4 ${tone}`}
  >
    <div className="flex items-start gap-3">
      <Icon size={20} weight="fill" className={isGood ? "text-emerald-600" : "text-amber-600"} />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-black uppercase tracking-[0.18em] opacity-70">Turn {index + 1}</p>
        <p className="mt-1 text-sm leading-relaxed text-zinc-700">{message.content}</p>
        <p className="mt-3 text-sm font-bold">
          {isGood ? "Câu này ổn rồi" : `Nên nói: ${betterAnswer || "Try a shorter, clearer answer."}`}
        </p>
      </div>
    </div>
  </motion.div>
  );
};

const SessionResultPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { user } = useAuth();
  const sessionId = Number(id);
  const hasProAccess = canAccessSubscriptionFeatures(user);
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
    let pollTimer = null;

    const loadSession = async (pollCount = 0) => {
      if (pollCount === 0) {
        setIsLoading(true);
      }
      setError("");
      try {
        const response = await practiceApi.getSession(sessionId);
        if (!isMounted) {
          return;
        }
        setSession(response);

        const finalEvaluation = response?.metadata?.final_evaluation || {};
        const analysisStatus = finalEvaluation.evaluation_status || "";
        const shouldPollAnalysis =
          response?.status !== "active" &&
          !response?.score &&
          !isTerminalAnalysisStatus(analysisStatus) &&
          pollCount < ANALYSIS_MAX_POLLS;

        if (shouldPollAnalysis) {
          pollTimer = window.setTimeout(() => {
            void loadSession(pollCount + 1);
          }, ANALYSIS_POLL_INTERVAL_MS);
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
      if (pollTimer) {
        window.clearTimeout(pollTimer);
      }
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
      <div className="app-page-narrow rounded-lg border border-rose-100 bg-white p-6 shadow-sm">
        <div className="flex items-start gap-3 text-rose-600">
          <WarningCircle size={24} weight="fill" className="mt-0.5 shrink-0" />
          <div>
            <h1 className="font-display text-2xl font-black text-zinc-950">Session result unavailable</h1>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{error || "This session could not be loaded."}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate("/scenarios")}
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
  const finalEvaluation = session.metadata?.final_evaluation || {};
  const analysisStatus = finalEvaluation.evaluation_status || (score ? "completed" : "pending");
  const profileExtractionStatus = finalEvaluation.profile_extraction_status;
  const isAnalysisPending = !score && !isTerminalAnalysisStatus(analysisStatus);
  const skillBreakdown = Object.fromEntries(
    Object.entries(score?.skill_breakdown || {}).filter(([key]) => VISIBLE_SKILL_KEYS.has(key))
  );
  const strengths = scoreMeta.strengths || [];
  const improvements = scoreMeta.improvements || [];
  const realtimeFeedbackMessages = userMessages.filter((message) => message.realtime_feedback);
  const nextSteps = scoreMeta.next_steps || [];
  const objectiveCompletion = scoreMeta.objective_completion;
  const detailedMetrics = [
    { label: "Vocabulary", value: skillBreakdown.vocabulary ?? "Preview" },
    { label: "Fluency", value: skillBreakdown.fluency ?? "Preview" },
  ];

  const completionBadge = {
    completed: { label: "Ho?n th?nh", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: CheckCircle },
    partial: { label: "G?n ho?n th?nh", color: "bg-amber-100 text-amber-700 border-amber-200", icon: WarningCircle },
    not_completed: { label: "C?n luy?n th?m", color: "bg-rose-100 text-rose-700 border-rose-200", icon: XCircle },
  }[objectiveCompletion] || null;
  const scenarioId = session.scenario?.id;
  const scenarioTitle = session.scenario?.title || "Conversation session";
  const hasRetryTarget = Number.isFinite(Number(scenarioId));
  const heroTitle = score ? "B?n ?? ho?n th?nh k?ch b?n" : "?? l?u b?i n?i c?a b?n";
  const heroMessage = score
    ? "T?t l?m. Xem nhanh ph?n h?i r?i ti?p t?c b?i h?c k? ti?p."
    : "B?n c? th? ti?p t?c h?c ngay. AI feedback s? c?p nh?t khi ph?n t?ch xong.";
  const quickFeedbackSections = [
    {
      title: "?i?m m?nh",
      icon: Trophy,
      tone: "border-emerald-200 bg-emerald-50 text-emerald-950",
      titleClass: "text-emerald-700",
      iconClass: "text-emerald-600",
      items: strengths,
      empty: score ? "Ch?a c? ?i?m m?nh n?i b?t trong l?n ph?n t?ch n?y." : "?ang ch? AI ph?n t?ch ?i?m m?nh.",
    },
    {
      title: "C?n c?i thi?n",
      icon: WarningCircle,
      tone: "border-amber-200 bg-amber-50 text-amber-950",
      titleClass: "text-amber-700",
      iconClass: "text-amber-600",
      items: improvements,
      empty: score ? "Ch?a c? g?i ? c?i thi?n c? th?." : "?ang ch? AI t?m ?i?m c?n luy?n th?m.",
    },
    {
      title: "B??c ti?p theo",
      icon: ArrowRight,
      tone: "border-primary/20 bg-primary/5 text-zinc-800",
      titleClass: "text-primary",
      iconClass: "text-primary",
      items: nextSteps,
      empty: score ? "Ti?p t?c h?c ?? gi? nh?p luy?n n?i h?m nay." : "Ti?p t?c h?c trong l?c feedback ???c t?o.",
    },
  ];

  return (
    <div className="flex w-full flex-col gap-5">
      <section className="overflow-hidden rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-primary/10 p-6 shadow-sm">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white/80 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-700">
              <CheckCircle size={14} weight="fill" />
              {score ? "Ho?n th?nh" : "?? l?u b?i"}
            </div>
            <p className="mt-4 text-[11px] font-black uppercase tracking-[0.24em] text-primary">K?t qu? luy?n n?i</p>
            <h1 className="mt-2 font-display text-3xl font-black tracking-tight text-zinc-950 sm:text-4xl">
              {heroTitle}
            </h1>
            <p className="mt-3 text-base font-bold text-zinc-800">{scenarioTitle}</p>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              {session.scenario?.description || heroMessage}
            </p>
            <p className="mt-3 text-sm font-semibold text-emerald-700">{heroMessage}</p>
          </div>

          <div className="rounded-2xl border border-white/80 bg-white/90 p-5 shadow-sm lg:min-w-[260px]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">?i?m t?ng</p>
                <p className="mt-2 text-4xl font-black text-zinc-950">
                  {score ? Number(score.overall_score || 0).toFixed(1) : "--"}
                </p>
              </div>
              {score ? (
                <div className="relative flex items-center justify-center">
                  <ScoreRing score={score.overall_score} size={84} />
                  <span className="absolute text-xs font-black uppercase tracking-wider text-zinc-500">/10</span>
                </div>
              ) : (
                <div className="h-16 w-16 animate-spin rounded-full border-4 border-sky-100 border-t-sky-500" />
              )}
            </div>
            <div className="mt-5 grid gap-2 text-sm">
              <div className="flex items-center justify-between rounded-xl bg-zinc-50 px-3 py-2">
                <span className="font-bold text-zinc-500">Th?i l??ng</span>
                <span className="font-black text-zinc-950">{formatDuration(session.duration_seconds)}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-zinc-50 px-3 py-2">
                <span className="font-bold text-zinc-500">Tr?ng th?i</span>
                <span className="font-black capitalize text-zinc-950">{session.status}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-zinc-50 px-3 py-2">
                <span className="font-bold text-zinc-500">L? do</span>
                <span className="text-right font-black text-zinc-950">{endReason}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={() => navigate("/scenarios")}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-zinc-950 px-6 py-3 text-sm font-black text-white shadow-sm transition hover:bg-zinc-800"
          >
            Ti?p t?c h?c
            <ArrowRight size={18} weight="bold" />
          </button>
          {hasRetryTarget ? (
            <button
              type="button"
              onClick={() => navigate(`/practice/${scenarioId}/preview`)}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-6 py-3 text-sm font-black text-zinc-800 shadow-sm transition hover:bg-zinc-50"
            >
              Luy?n l?i k?ch b?n
            </button>
          ) : null}
        </div>
      </section>

      {isAnalysisPending && (
        <section className="rounded-xl border border-sky-200 bg-sky-50 p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="mt-1 h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-sky-200 border-t-sky-600" />
            <div>
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-sky-700">AI Feedback</p>
              <h2 className="mt-1 font-display text-xl font-black text-sky-950">?ang t?o ph?n h?i chi ti?t</h2>
              <p className="mt-2 text-sm leading-relaxed text-sky-800">
                B?i n?i ?? ???c l?u. B?n c? th? ti?p t?c h?c, feedback s? t? c?p nh?t khi AI ph?n t?ch xong.
              </p>
            </div>
          </div>
        </section>
      )}

      {!score && isTerminalAnalysisStatus(analysisStatus) && analysisStatus !== "completed" && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-amber-700">AI Feedback</p>
          <h2 className="mt-1 font-display text-xl font-black text-amber-950">Ch?a c? ph?n t?ch chi ti?t</h2>
          <p className="mt-2 text-sm leading-relaxed text-amber-900">
            B?i n?i ?? ???c l?u, nh?ng AI ch?a ho?n t?t ph?n t?ch. L? do: {finalEvaluation.reason || analysisStatus}.
          </p>
        </section>
      )}

      {score?.feedback_summary ? (
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">T?m t?t feedback</p>
          <p className="mt-3 text-sm leading-relaxed text-zinc-700 italic">{score.feedback_summary}</p>
          {completionBadge && (() => {
            const BadgeIcon = completionBadge.icon;
            return (
              <span className={`mt-4 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-black ${completionBadge.color}`}>
                <BadgeIcon size={13} weight="fill" />
                {completionBadge.label}
              </span>
            );
          })()}
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        {quickFeedbackSections.map((section) => {
          const Icon = section.icon;
          return (
            <section key={section.title} className={`rounded-xl border p-5 shadow-sm ${section.tone}`}>
              <div className="flex items-center gap-2">
                <Icon size={18} weight="fill" className={section.iconClass} />
                <p className={`text-[11px] font-black uppercase tracking-[0.2em] ${section.titleClass}`}>{section.title}</p>
              </div>
              <ul className="mt-4 space-y-2">
                {section.items.length > 0 ? section.items.slice(0, 3).map((item, index) => (
                  <li key={`${section.title}-${index}`} className="flex items-start gap-2 text-sm">
                    <CheckCircle size={15} weight="fill" className={`mt-0.5 shrink-0 ${section.iconClass}`} />
                    <span>{item}</span>
                  </li>
                )) : (
                  <li className="text-sm leading-relaxed opacity-80">{section.empty}</li>
                )}
              </ul>
            </section>
          );
        })}
      </div>

      {Object.keys(skillBreakdown).length > 0 && (
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">K? n?ng</p>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {Object.entries(skillBreakdown).map(([key, val]) => (
              <SkillCard key={key} skillKey={key} value={val} />
            ))}
          </div>
          {profileExtractionStatus ? (
            <p className="mt-3 text-xs font-bold uppercase tracking-[0.16em] text-zinc-400">
              Learner signals: {profileExtractionStatus}
            </p>
          ) : null}
        </section>
      )}

      {realtimeFeedbackMessages.length > 0 && (
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Realtime Feedback</p>
          <h2 className="mt-1 font-display text-xl font-black text-zinc-950">{realtimeFeedbackMessages.length} speaking note{realtimeFeedbackMessages.length !== 1 ? "s" : ""}</h2>
          <div className="mt-4 space-y-3">
            {realtimeFeedbackMessages.map((message, i) => (
              <RealtimeFeedbackCard key={message.id || i} message={message} index={i} />
            ))}
          </div>
        </section>
      )}

      <section className={`rounded-xl border p-4 shadow-sm ${
        hasProAccess
          ? "border-amber-200 bg-gradient-to-br from-amber-50 to-purple-50"
          : "border-zinc-200 bg-white"
      }`}>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Crown size={16} weight="fill" className="text-amber-600" />
              <p className="text-[11px] font-black uppercase tracking-[0.2em] text-amber-700">Detailed Feedback</p>
            </div>
            <h2 className="mt-1 font-display text-lg font-black text-zinc-950">
              {hasProAccess ? "Pro insights unlocked" : "Pro insights preview"}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-zinc-600">
              {hasProAccess
                ? "Theo d?i ph?t ?m, v?n t? v? ?? tr?i ch?y sau m?i bu?i luy?n n?i."
                : "N?ng c?p Pro ?? m? kh?a ph?n t?ch s?u sau m?i bu?i luy?n n?i."}
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[360px]">
            {detailedMetrics.map((metric) => (
              <div key={metric.label} className={`rounded-lg border px-3 py-2 ${hasProAccess ? "border-white/80 bg-white/80" : "border-zinc-200 bg-zinc-50"}`}>
                <p className="text-[9px] font-black uppercase tracking-[0.18em] text-zinc-500">{metric.label}</p>
                <p className="mt-1 text-sm font-black text-zinc-950">
                  {typeof metric.value === "number" ? Number(metric.value).toFixed(1) : metric.value}
                </p>
              </div>
            ))}
          </div>
          {!hasProAccess ? (
            <button
              type="button"
              onClick={() => navigate("/subscription")}
              className="inline-flex w-fit items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2.5 text-sm font-black text-white"
            >
              <Crown size={16} weight="fill" />
              N?ng c?p Pro
            </button>
          ) : null}
        </div>
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Saved Conversation</p>
            <h2 className="mt-1 font-display text-xl font-black text-zinc-950">{userMessages.length} speaking turns</h2>
            <p className="mt-1 text-sm text-zinc-500">Transcript l?u l?i ?? xem sau khi c?n ?n l?i c? th?.</p>
          </div>
          <ChatCenteredText size={26} weight="fill" className="text-primary" />
        </div>

        <div className="mt-4 space-y-2">
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

