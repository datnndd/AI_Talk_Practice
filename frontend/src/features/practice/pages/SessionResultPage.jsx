import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  ChatCenteredText,
  CheckCircle,
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

  const score = session.score;
  const scoreMeta = score?.metadata || {};
  const finalEvaluation = session.metadata?.final_evaluation || {};
  const analysisStatus = finalEvaluation.evaluation_status || (score ? "completed" : "pending");
  const isAnalysisPending = !score && !isTerminalAnalysisStatus(analysisStatus);
  const skillBreakdown = Object.fromEntries(
    Object.entries(score?.skill_breakdown || {}).filter(([key]) => VISIBLE_SKILL_KEYS.has(key))
  );
  const strengths = scoreMeta.strengths || [];
  const improvements = scoreMeta.improvements || [];
  const nextSteps = scoreMeta.next_steps || [];
  const objectiveCompletion = scoreMeta.objective_completion;

  const completionBadge = {
    completed: { label: "Hoàn thành", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: CheckCircle },
    partial: { label: "Gần hoàn thành", color: "bg-amber-100 text-amber-700 border-amber-200", icon: WarningCircle },
    not_completed: { label: "Cần luyện thêm", color: "bg-rose-100 text-rose-700 border-rose-200", icon: XCircle },
  }[objectiveCompletion] || null;
  const scenarioId = session.scenario?.id;
  const scenarioTitle = session.scenario?.title || "Conversation session";
  const hasRetryTarget = Number.isFinite(Number(scenarioId));
  const heroTitle = score ? "Bạn đã hoàn thành kịch bản" : "Đã lưu bài nói của bạn";
  const heroMessage = score
    ? "Tốt lắm. Xem nhanh phản hồi rồi tiếp tục bài học kế tiếp."
    : "Bạn có thể tiếp tục học ngay. AI feedback sẽ cập nhật khi phân tích xong.";
  const quickFeedbackSections = [
    {
      title: "Điểm mạnh",
      icon: Trophy,
      tone: "border-emerald-200 bg-emerald-50 text-emerald-950",
      titleClass: "text-emerald-700",
      iconClass: "text-emerald-600",
      items: strengths,
      empty: score ? "Chưa có điểm mạnh nổi bật trong lần phân tích này." : "Đang chờ AI phân tích điểm mạnh.",
    },
    {
      title: "Cần cải thiện",
      icon: WarningCircle,
      tone: "border-amber-200 bg-amber-50 text-amber-950",
      titleClass: "text-amber-700",
      iconClass: "text-amber-600",
      items: improvements,
      empty: score ? "Chưa có gợi ý cải thiện cụ thể." : "Đang chờ AI tìm điểm cần luyện thêm.",
    },
    {
      title: "Bước tiếp theo",
      icon: ArrowRight,
      tone: "border-primary/20 bg-primary/5 text-zinc-800",
      titleClass: "text-primary",
      iconClass: "text-primary",
      items: nextSteps,
      empty: score ? "Tiếp tục học để giữ nhịp luyện nói hôm nay." : "Tiếp tục học trong lúc feedback được tạo.",
    },
  ];

  return (
    <div className="flex w-full flex-col gap-5">
      <section className="overflow-hidden rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-primary/10 p-6 shadow-sm">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white/80 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-700">
              <CheckCircle size={14} weight="fill" />
              {score ? "Hoàn thành" : "Đã lưu bài"}
            </div>
            <p className="mt-4 text-[11px] font-black uppercase tracking-[0.24em] text-primary">Kết quả luyện nói</p>
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
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Điểm tổng</p>
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
                <span className="font-bold text-zinc-500">Thời lượng</span>
                <span className="font-black text-zinc-950">{formatDuration(session.duration_seconds)}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-zinc-50 px-3 py-2">
                <span className="font-bold text-zinc-500">Trạng thái</span>
                <span className="font-black capitalize text-zinc-950">{session.status}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-zinc-50 px-3 py-2">
                <span className="font-bold text-zinc-500">Lý do</span>
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
            Tiếp tục học
            <ArrowRight size={18} weight="bold" />
          </button>
          {hasRetryTarget ? (
            <button
              type="button"
              onClick={() => navigate(`/practice/${scenarioId}/preview`)}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-6 py-3 text-sm font-black text-zinc-800 shadow-sm transition hover:bg-zinc-50"
            >
              Luyện lại kịch bản
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
              <h2 className="mt-1 font-display text-xl font-black text-sky-950">Đang tạo phản hồi chi tiết</h2>
              <p className="mt-2 text-sm leading-relaxed text-sky-800">
                Bài nói đã được lưu. Bạn có thể tiếp tục học, feedback sẽ tự cập nhật khi AI phân tích xong.
              </p>
            </div>
          </div>
        </section>
      )}

      {!score && isTerminalAnalysisStatus(analysisStatus) && analysisStatus !== "completed" && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-amber-700">AI Feedback</p>
          <h2 className="mt-1 font-display text-xl font-black text-amber-950">Chưa có phân tích chi tiết</h2>
          <p className="mt-2 text-sm leading-relaxed text-amber-900">
            Bài nói đã được lưu, nhưng AI chưa hoàn tất phân tích. Lý do: {finalEvaluation.reason || analysisStatus}.
          </p>
        </section>
      )}

      {score?.feedback_summary ? (
        <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Tóm tắt feedback</p>
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
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Kỹ năng</p>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {Object.entries(skillBreakdown).map(([key, val]) => (
              <SkillCard key={key} skillKey={key} value={val} />
            ))}
          </div>
        </section>
      )}

    </div>
  );

};

export default SessionResultPage;

