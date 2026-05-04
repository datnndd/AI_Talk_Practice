import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Crown, Headphones, LockSimple, MagnifyingGlass, PlayCircle, Sparkle, Target, Timer } from "@phosphor-icons/react";

import fallbackScenarioImage from "@/assets/buddy_talk_logo.jpg";
import { practiceApi } from "@/features/practice/api/practiceApi";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const DIFFICULTY_GROUPS = [
  { key: "easy", title: "Mới bắt đầu", badge: "Easy", accent: "from-emerald-500 to-lime-400", chip: "bg-emerald-100 text-emerald-700" },
  { key: "medium", title: "Trung cấp", badge: "Medium", accent: "from-amber-500 to-orange-400", chip: "bg-amber-100 text-amber-700" },
  { key: "hard", title: "Nâng cao", badge: "Hard", accent: "from-rose-500 to-pink-500", chip: "bg-rose-100 text-rose-700" },
];

const formatCategory = (category = "") =>
  category
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || "Scenario";

const formatDuration = (seconds) => {
  const totalSeconds = Number(seconds);
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) return "3-5 phút";
  const minutes = Math.max(1, Math.round(totalSeconds / 60));
  return `${minutes} phút`;
};

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

const normalizeDifficulty = (difficulty) =>
  DIFFICULTY_GROUPS.some((group) => group.key === difficulty) ? difficulty : "medium";

const getDifficultyMeta = (difficulty) =>
  DIFFICULTY_GROUPS.find((group) => group.key === normalizeDifficulty(difficulty)) || DIFFICULTY_GROUPS[1];

const ScenarioCard = ({ scenario, hasProAccess, featured = false }) => {
  const difficulty = getDifficultyMeta(scenario.difficulty);
  const isProScenario = Boolean(scenario.is_pro);
  const isLocked = isProScenario && !hasProAccess;

  return (
    <Link
      to={isLocked ? "/subscription" : `/practice/${scenario.id}/preview`}
      onMouseEnter={() => !isLocked && practiceApi.prefetchScenario(scenario.id)}
      onFocus={() => !isLocked && practiceApi.prefetchScenario(scenario.id)}
      className="group relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="relative m-3 mb-0 flex aspect-[16/10] items-center justify-center overflow-hidden rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800">
        <img
          alt={scenario.title}
          loading="lazy"
          src={getScenarioImage(scenario)}
          onError={(event) => {
            event.currentTarget.src = fallbackScenarioImage;
          }}
          className={`max-h-full max-w-full object-contain transition duration-500 group-hover:scale-105 ${isLocked ? "blur-[1px] saturate-75" : ""}`}
        />
        <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-zinc-950/55 to-transparent" />
        <div className="absolute left-3 top-3 flex flex-wrap gap-2">
          <span className={`rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] ${difficulty.chip}`}>{difficulty.badge}</span>
          {isProScenario ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-amber-800">
              <Crown size={12} weight="fill" /> {isLocked ? "Pro" : "Unlocked"}
            </span>
          ) : null}
        </div>
        <div className="absolute bottom-3 left-3 right-3 text-white">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-white/75">{formatCategory(scenario.category)}</p>
        </div>
        {isLocked ? (
          <div className="absolute inset-0 grid place-items-center bg-zinc-950/35">
            <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-[11px] font-black uppercase tracking-[0.18em] text-amber-700 shadow-lg">
              <LockSimple size={14} weight="fill" /> Mở khóa Pro
            </div>
          </div>
        ) : null}
      </div>

      <div className="p-4">
        <h3 className="line-clamp-2 min-h-[2.5rem] text-base font-black leading-tight text-foreground transition group-hover:text-primary">{scenario.title}</h3>
        <p className="mt-2 line-clamp-2 min-h-[2.5rem] text-xs font-semibold leading-5 text-muted-foreground">{scenario.description}</p>
        <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[11px] font-black">
          <div className="rounded-2xl bg-muted px-2 py-3"><Headphones className="mx-auto mb-1" size={17} weight="fill" />{formatDuration(scenario.estimated_duration)}</div>
          <div className="rounded-2xl bg-muted px-2 py-3"><Target className="mx-auto mb-1" size={17} weight="fill" />{scenario.tasks?.length || 0} tasks</div>
          <div className="rounded-2xl bg-muted px-2 py-3"><Sparkle className="mx-auto mb-1" size={17} weight="fill" />Live AI</div>
        </div>
        <div className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-black text-white transition group-hover:bg-primary/90">
          <PlayCircle size={18} weight="fill" /> {isLocked ? "Upgrade to play" : "Preview roleplay"}
        </div>
      </div>
    </Link>
  );
};

const PlaylistSection = ({ scenarios = [], isLoading = false, error = "", hasProAccess = false }) => {
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState("all");
  const [category, setCategory] = useState("all");

  const categories = useMemo(() => {
    const values = new Set(scenarios.map((scenario) => scenario.category).filter(Boolean));
    return Array.from(values).sort();
  }, [scenarios]);

  const filteredScenarios = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return scenarios.filter((scenario) => {
      const matchesQuery = !normalizedQuery
        || scenario.title?.toLowerCase().includes(normalizedQuery)
        || scenario.description?.toLowerCase().includes(normalizedQuery)
        || formatCategory(scenario.category).toLowerCase().includes(normalizedQuery);
      const matchesDifficulty = difficulty === "all" || normalizeDifficulty(scenario.difficulty) === difficulty;
      const matchesCategory = category === "all" || scenario.category === category;
      return matchesQuery && matchesDifficulty && matchesCategory;
    });
  }, [category, difficulty, query, scenarios]);

  return (
    <section className="relative mb-8 mt-12 space-y-6">
      <div className="overflow-hidden rounded-[36px] bg-gradient-to-br from-zinc-950 via-indigo-950 to-primary p-6 text-white shadow-2xl shadow-primary/10 md:p-8">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] backdrop-blur">
              <Sparkle size={15} weight="fill" /> Roleplay Command Center
            </div>
            <h2 className="mt-5 text-4xl font-black tracking-tight md:text-5xl">Chọn bối cảnh, vào vai, nói thật tự nhiên</h2>
            <p className="mt-3 max-w-2xl text-sm font-semibold leading-6 text-white/70">
              Lọc kịch bản theo cấp độ và chủ đề, xem nhiệm vụ trước khi bước vào phòng hội thoại AI.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-3xl bg-white/10 p-4 backdrop-blur"><p className="text-3xl font-black">{scenarios.length}</p><p className="text-[10px] font-black uppercase text-white/60">Scenarios</p></div>
            <div className="rounded-3xl bg-white/10 p-4 backdrop-blur"><p className="text-3xl font-black">{categories.length}</p><p className="text-[10px] font-black uppercase text-white/60">Topics</p></div>
            <div className="rounded-3xl bg-white/10 p-4 backdrop-blur"><Timer className="mx-auto" size={28} weight="fill" /><p className="mt-1 text-[10px] font-black uppercase text-white/60">3-5 min</p></div>
          </div>
        </div>
      </div>

      <div className="rounded-[30px] border border-border bg-card p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_190px_220px]">
          <label className="relative block">
            <MagnifyingGlass size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tìm theo tình huống, chủ đề, mục tiêu..."
              className="w-full rounded-2xl border border-border bg-muted px-11 py-3 text-sm font-semibold outline-none transition focus:border-primary"
            />
          </label>
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} className="rounded-2xl border border-border bg-muted px-4 py-3 text-sm font-black outline-none focus:border-primary">
            <option value="all">All levels</option>
            {DIFFICULTY_GROUPS.map((group) => <option key={group.key} value={group.key}>{group.title}</option>)}
          </select>
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="rounded-2xl border border-border bg-muted px-4 py-3 text-sm font-black outline-none focus:border-primary">
            <option value="all">All topics</option>
            {categories.map((item) => <option key={item} value={item}>{formatCategory(item)}</option>)}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex min-h-[245px] items-center justify-center rounded-[30px] border border-border bg-card">
          <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-primary" />
        </div>
      ) : null}

      {!isLoading && error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">{error}</div>
      ) : null}

      {!isLoading && !error && filteredScenarios.length === 0 ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-10 text-center text-sm font-semibold text-muted-foreground">Không tìm thấy kịch bản phù hợp.</div>
      ) : null}

      {!isLoading && !error && filteredScenarios.length > 0 ? (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filteredScenarios.map((scenario) => <ScenarioCard key={scenario.id} scenario={scenario} hasProAccess={hasProAccess} />)}
        </div>
      ) : null}
    </section>
  );
};

export default PlaylistSection;
