import { Link } from "react-router-dom";
import { Crown, Headphones, LockSimple } from "@phosphor-icons/react";

import fallbackScenarioImage from "@/assets/buddy_talk_logo.jpg";
import { practiceApi } from "@/features/practice/api/practiceApi";

const DIFFICULTY_GROUPS = [
  {
    key: "easy",
    title: "Mới bắt đầu",
    badge: "Easy",
    badgeClass: "bg-difficulty-easy",
  },
  {
    key: "medium",
    title: "Trung cấp",
    badge: "Medium",
    badgeClass: "bg-brand-orange",
  },
  {
    key: "hard",
    title: "Nâng cao",
    badge: "Hard",
    badgeClass: "bg-difficulty-hard",
  },
];

const formatCategory = (category = "") =>
  category
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Scenario";

const formatDuration = (seconds) => {
  const totalSeconds = Number(seconds);
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    return "3-5 phút";
  }

  const minutes = Math.max(1, Math.round(totalSeconds / 60));
  return `${minutes} phút`;
};

import { getApiBaseUrl } from "@/shared/api/httpClient";

const getFullImageUrl = (url) => {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  const host = getApiBaseUrl().replace("/api", "");
  return `${host}${url}`;
};

const getScenarioImage = (scenario) =>
  getFullImageUrl(scenario?.image_url)
    || getFullImageUrl(scenario?.thumbnail_url)
    || getFullImageUrl(scenario?.cover_url)
    || fallbackScenarioImage;

const groupScenariosByDifficulty = (scenarios) =>
  scenarios.reduce(
    (groups, scenario) => {
      const difficulty = DIFFICULTY_GROUPS.some((group) => group.key === scenario.difficulty)
        ? scenario.difficulty
        : "medium";

      groups[difficulty].push(scenario);
      return groups;
    },
    { easy: [], medium: [], hard: [] },
  );

const ScenarioCard = ({ scenario, group, hasProAccess }) => {
  const isProScenario = Boolean(scenario.is_pro);
  const isLocked = isProScenario && !hasProAccess;

  return (
  <Link
    to={isLocked ? "/subscription" : `/practice/${scenario.id}`}
    onMouseEnter={() => !isLocked && practiceApi.prefetchScenario(scenario.id)}
    onFocus={() => !isLocked && practiceApi.prefetchScenario(scenario.id)}
    className="group relative col-span-12 block cursor-pointer overflow-hidden rounded-xl bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md dark:bg-gray-800 sm:col-span-6 md:col-span-3 2xl:col-span-2"
  >
    <div className="relative aspect-video w-full overflow-hidden bg-gray-100 dark:bg-gray-700">
      <img
        alt={scenario.title}
        loading="lazy"
        src={getScenarioImage(scenario)}
        onError={(event) => {
          event.currentTarget.src = fallbackScenarioImage;
        }}
        className={`size-full object-cover transition-transform group-hover:scale-105 ${isLocked ? "blur-[1px] saturate-75" : ""}`}
      />
      <span className={`absolute left-2 top-2 rounded px-1.5 py-0.5 text-[9px] font-extrabold uppercase tracking-wide text-white ${group.badgeClass}`}>
        {group.badge}
      </span>
      <div className="absolute bottom-2 right-2 flex items-center gap-1 rounded-lg bg-black/80 px-2 py-0.5 text-sm font-medium text-white backdrop-blur">
        <Headphones size={16} weight="fill" />
        {formatDuration(scenario.estimated_duration)}
      </div>
      {isProScenario ? (
        <span className="absolute right-2 top-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-1 text-[9px] font-black uppercase tracking-[0.16em] text-amber-800 ring-1 ring-amber-200">
          <Crown size={11} weight="fill" />
          {isLocked ? "Pro" : "Unlocked"}
        </span>
      ) : null}
      {isLocked ? (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-950/35 text-white">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/95 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-amber-700 shadow-lg">
            <LockSimple size={13} weight="fill" />
            Mở khóa Pro
          </div>
        </div>
      ) : null}
    </div>
    <div className="p-3">
      <h3 className="line-clamp-2 min-h-[2.5rem] font-semibold text-gray-900 transition-colors group-hover:text-brand-purple dark:text-white">
        {scenario.title}
      </h3>
      <p className="mt-1 line-clamp-2 min-h-[2rem] text-xs text-gray-600 dark:text-gray-400">
        {scenario.description}
      </p>
      <div className="mt-2 flex items-center justify-between gap-2 text-sm">
        <span className="truncate font-medium text-gray-700 dark:text-gray-300">
          {formatCategory(scenario.category)}
        </span>
        <span className="shrink-0 rounded-lg bg-primary/10 px-2 py-1 text-[11px] font-bold uppercase text-primary">
          {scenario.tasks?.length || 0} tasks
        </span>
      </div>
    </div>
  </Link>
  );
};

const ScenarioGroup = ({ group, scenarios, hasProAccess }) => {
  if (scenarios.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-black uppercase tracking-[0.16em] text-foreground/70">
          {group.title}
        </h3>
        <span className="text-xs font-bold text-muted-foreground">{scenarios.length} kịch bản</span>
      </div>
      <div className="grid min-h-[245px] grid-cols-12 gap-4">
        {scenarios.map((scenario) => (
          <ScenarioCard key={scenario.id} scenario={scenario} group={group} hasProAccess={hasProAccess} />
        ))}
      </div>
    </section>
  );
};

const PlaylistSection = ({ scenarios = [], isLoading = false, error = "", hasProAccess = false }) => {
  const groupedScenarios = groupScenariosByDifficulty(scenarios);

  return (
    <div className="relative mt-12 mb-8 space-y-8">
      <div className="relative col-span-4 w-full overflow-hidden bg-cover bg-center bg-no-repeat">
        <div className="w-fit overflow-visible pl-2">
          <div className="relative inline-block">
            <div className="absolute inset-0 -skew-x-12 bg-gradient-to-r from-primary/20 to-primary/10"></div>
            <p className="relative px-6 py-2 font-display text-2xl font-bold">Kịch bản luyện nói</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-[245px] items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-primary" />
        </div>
      ) : null}

      {!isLoading && error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">
          {error}
        </div>
      ) : null}

      {!isLoading && !error && scenarios.length === 0 ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-10 text-center text-sm font-semibold text-muted-foreground">
          Chưa có kịch bản khả dụng.
        </div>
      ) : null}

      {!isLoading && !error ? (
        <div className="space-y-8">
          {DIFFICULTY_GROUPS.map((group) => (
            <ScenarioGroup key={group.key} group={group} scenarios={groupedScenarios[group.key]} hasProAccess={hasProAccess} />
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default PlaylistSection;
