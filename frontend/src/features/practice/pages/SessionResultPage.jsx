import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ChatCenteredText, Clock, WarningCircle } from "@phosphor-icons/react";
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
          onClick={() => navigate("/topics")}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-zinc-950 px-5 py-3 text-sm font-bold text-white"
        >
          <ArrowLeft size={18} weight="bold" />
          Back to topics
        </button>
      </div>
    );
  }

  const messages = session.messages || [];
  const userMessages = messages.filter((message) => message.role === "user");

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5">
      <button
        type="button"
        onClick={() => navigate("/topics")}
        className="inline-flex w-fit items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-bold text-zinc-700 shadow-sm transition hover:bg-zinc-50"
      >
        <ArrowLeft size={18} weight="bold" />
        Back to topics
      </button>

      <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Practice Result</p>
        <h1 className="mt-2 font-display text-3xl font-black tracking-tight text-zinc-950">
          {session.scenario?.title || "Conversation session"}
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          {session.scenario?.description || "Your speaking session is ready for review."}
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
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

        {session.score ? (
          <div className="mt-5 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-emerald-950">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-700">Overall Score</p>
            <p className="mt-2 text-3xl font-black">{Number(session.score.overall_score || 0).toFixed(1)}</p>
            {session.score.feedback_summary ? (
              <p className="mt-2 text-sm leading-relaxed">{session.score.feedback_summary}</p>
            ) : null}
          </div>
        ) : null}
      </section>

      <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
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
