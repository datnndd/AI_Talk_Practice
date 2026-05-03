import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Clock, Target } from "@phosphor-icons/react";

import fallbackScenarioImage from "@/assets/buddy_talk_logo.jpg";
import { practiceApi } from "@/features/practice/api/practiceApi";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const emojiByCategory = {
  travel: "🚗",
  transport: "🚗",
  work: "💼",
  interview: "💼",
  cafe: "☕",
  restaurant: "🍽️",
  hotel: "🏨",
  health: "🩺",
  shopping: "🛍️",
  school: "🎓",
  social: "💬",
};

const formatDuration = (seconds) => {
  const totalSeconds = Number(seconds);
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) return "3 - 5 minutes";
  const minutes = Math.max(1, Math.round(totalSeconds / 60));
  if (minutes <= 5) return "3 - 5 minutes";
  return `${minutes} minutes`;
};

const formatDifficulty = (difficulty = "medium") => {
  const labels = { easy: "Easy", medium: "Medium", hard: "Hard" };
  return labels[difficulty] || "Medium";
};

const getFullImageUrl = (url) => {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  const host = getApiBaseUrl().replace("/api", "");
  return `${host}${url}`;
};

const getScenarioEmoji = (scenario) => {
  const keys = [scenario?.category, ...(Array.isArray(scenario?.tags) ? scenario.tags : [])]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase());
  const match = keys.find((key) => emojiByCategory[key]);
  return match ? emojiByCategory[match] : "💬";
};

const splitDescription = (description = "") => {
  const parts = description.split(/\n+/).map((part) => part.trim()).filter(Boolean);
  return {
    english: parts[0] || description || "Read the situation, complete the tasks, then start your speaking practice.",
    vietnamese: parts[1] || "Đọc tình huống, hoàn thành nhiệm vụ, rồi bắt đầu luyện nói.",
  };
};

const ScenarioPreviewPage = () => {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const [scenario, setScenario] = useState(() => practiceApi.getCachedScenario(id));
  const [isLoading, setIsLoading] = useState(!scenario);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setError("");
    setIsLoading(!practiceApi.getCachedScenario(id));

    void practiceApi.getScenario(id).then((data) => {
      if (mounted) setScenario(data);
    }).catch((err) => {
      if (mounted) setError(err?.response?.data?.detail || "Không thể tải tình huống luyện nói.");
    }).finally(() => {
      if (mounted) setIsLoading(false);
    });

    return () => {
      mounted = false;
    };
  }, [id]);

  const startUrl = useMemo(() => {
    const query = searchParams.toString();
    return `/practice/${id}${query ? `?${query}` : ""}`;
  }, [id, searchParams]);

  if (isLoading) {
    return <div className="py-8 text-sm font-semibold text-muted-foreground">Đang tải tình huống...</div>;
  }

  if (error || !scenario) {
    return (
      <div className="app-page-narrow py-6">
        <p className="rounded-2xl bg-rose-50 px-5 py-4 text-sm font-bold text-rose-700">{error || "Không tìm thấy tình huống."}</p>
        <Link to="/dashboard" className="mt-5 inline-flex items-center gap-2 text-sm font-black text-primary">
          <ArrowLeft size={18} weight="bold" />
          Quay lại
        </Link>
      </div>
    );
  }

  const imageUrl = getFullImageUrl(scenario.image_url);
  const { english, vietnamese } = splitDescription(scenario.description);
  const tasks = Array.isArray(scenario.tasks) && scenario.tasks.length > 0
    ? scenario.tasks
    : ["Start the conversation naturally.", "Ask and answer follow-up questions.", "Close the conversation politely."];

  return (
    <div className="app-page-wide">
      <Link to="/dashboard" className="mb-6 inline-flex items-center gap-2 text-sm font-black uppercase tracking-wide text-muted-foreground hover:text-foreground">
        <ArrowLeft size={18} weight="bold" />
        Back
      </Link>

      <div className="grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:items-start">
        <div className="relative aspect-[4/3] overflow-hidden rounded-3xl bg-gradient-to-br from-amber-500/30 via-rose-500/20 to-indigo-700/40 shadow-[var(--shadow-card)]">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={scenario.title}
              onError={(event) => {
                event.currentTarget.src = fallbackScenarioImage;
              }}
              className="absolute inset-0 h-full w-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 grid place-items-center text-[180px] drop-shadow-2xl">{getScenarioEmoji(scenario)}</div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-black/5 to-transparent" />
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between rounded-xl bg-black/35 px-3 py-2 text-xs font-semibold text-white backdrop-blur">
            <span className="inline-flex items-center gap-1.5">
              <Clock size={14} weight="bold" />
              {formatDuration(scenario.estimated_duration)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Target size={14} weight="bold" />
              {formatDifficulty(scenario.difficulty)}
            </span>
          </div>
        </div>

        <div className="flex flex-col">
          <h1 className="text-3xl font-bold leading-tight text-foreground sm:text-4xl">{scenario.title}</h1>
          <p className="mt-3 text-base leading-7 text-foreground/80">{english}</p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{vietnamese}</p>

          <div className="mt-6 flex items-center gap-3">
            <span className="text-2xl">📝</span>
            <h2 className="text-xl font-bold text-foreground">Your tasks</h2>
          </div>

          <ol className="mt-3 space-y-3">
            {tasks.map((task, index) => (
              <li key={`${task}-${index}`} className="flex items-start gap-3 rounded-xl border border-border bg-card/60 p-4 backdrop-blur">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary/20 text-sm font-bold text-primary">{index + 1}</span>
                <p className="flex-1 text-sm font-medium leading-relaxed text-foreground/90">{task}</p>
                <CheckCircle size={20} weight="bold" className="mt-0.5 shrink-0 text-muted-foreground/30" />
              </li>
            ))}
          </ol>

          <Link to={startUrl} className="mt-8 w-full rounded-2xl bg-primary py-4 text-center text-base font-semibold text-primary-foreground shadow-[var(--shadow-glow)] transition-transform hover:scale-[1.01] active:scale-[0.99]">
            Start Conversation
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ScenarioPreviewPage;



