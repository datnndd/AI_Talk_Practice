import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  CaretLeft,
  CheckCircle,
  Fire,
  Gift,
  LockKey,
  PlayCircle,
  Sparkle,
  Star,
  Target,
  Trophy,
  X,
} from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { useAuth } from "@/features/auth/context/AuthContext";

const sectionColors = [
  "from-sky-500 to-cyan-400",
  "from-emerald-500 to-lime-400",
  "from-violet-500 to-fuchsia-400",
  "from-amber-500 to-orange-400",
  "from-rose-500 to-pink-400",
];

const unitStatus = (unit, currentUnitId) => {
  if (unit.progress_status === "completed") return "completed";
  if (unit.is_locked) return "locked";
  if (unit.id === currentUnitId) return "current";
  return "open";
};

const getUnitRewards = (unit) => {
  const lessons = unit.lessons || [];
  return lessons.reduce(
    (total, lesson) => ({
      xp: total.xp + Number(lesson.xp_reward || 0),
      coin: total.coin + Number(lesson.coin_reward || 0),
    }),
    { xp: Number(unit.xp_reward || 0), coin: Number(unit.coin_reward || 0) },
  );
};

const getAllUnits = (sections = []) => sections.flatMap((section) => (section.units || []).map((unit) => ({ ...unit, section })));

const LessonNode = ({ unit, index, status, accent, onSelect }) => {
  const Icon = status === "completed" ? CheckCircle : status === "locked" ? LockKey : status === "current" ? PlayCircle : Star;
  const rewards = getUnitRewards(unit);

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 16, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.04, type: "spring", stiffness: 180, damping: 18 }}
      whileHover={status === "locked" ? {} : { scale: 1.04, y: -4 }}
      whileTap={status === "locked" ? {} : { scale: 0.98 }}
      onClick={() => onSelect(unit)}
      className={`group relative flex min-h-[150px] flex-col items-center justify-center rounded-[32px] border-2 border-b-[6px] p-5 text-center transition ${
        status === "completed"
          ? "border-emerald-200 border-b-emerald-300 bg-emerald-50 text-emerald-700 shadow-lg shadow-emerald-900/5"
          : status === "current"
            ? `border-white/40 border-b-white/60 bg-gradient-to-br ${accent} text-white shadow-2xl shadow-sky-900/20`
            : status === "locked"
              ? "border-zinc-200 border-b-zinc-300 bg-zinc-100 text-zinc-400 opacity-70"
              : "border-zinc-200 border-b-zinc-300 bg-white text-zinc-700 shadow-sm hover:border-primary/30"
      }`}
    >
      {status === "current" && <span className="absolute inset-0 animate-ping rounded-[32px] border-4 border-white/30" />}
      <span className="relative z-10 mb-3 flex h-16 w-16 items-center justify-center rounded-3xl bg-white/90 text-zinc-900 shadow-sm group-hover:rotate-3">
        <Icon size={34} weight="fill" className={status === "completed" ? "text-emerald-500" : status === "current" ? "text-primary" : ""} />
      </span>
      <p className="relative z-10 line-clamp-2 text-sm font-black">{unit.title}</p>
      <div className="relative z-10 mt-3 flex flex-wrap justify-center gap-2 text-[10px] font-black uppercase tracking-[0.14em]">
        <span className="rounded-full bg-white/80 px-2.5 py-1 text-amber-600">+{rewards.coin} coin</span>
        <span className="rounded-full bg-white/80 px-2.5 py-1 text-sky-600">+{rewards.xp} XP</span>
      </div>
    </motion.button>
  );
};

const QuestHero = ({ nextUnit, progress, gamification }) => {
  const rewards = nextUnit ? getUnitRewards(nextUnit) : { xp: 0, coin: 0 };
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-[36px] bg-gradient-to-br from-primary via-sky-500 to-cyan-400 p-6 text-white shadow-2xl shadow-sky-900/20 md:p-8"
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs font-black uppercase tracking-[0.18em] backdrop-blur">
            <Sparkle size={16} weight="fill" /> Daily Quest
          </div>
          <h1 className="mt-5 text-4xl font-black tracking-tight md:text-5xl">Tiếp tục hành trình hôm nay</h1>
          <p className="mt-3 max-w-2xl text-sm font-semibold leading-6 text-white/80">
            Hoàn thành bài tiếp theo để nhận XP, coin và giữ nhịp học mỗi ngày.
          </p>

          <div className="mt-6 rounded-3xl bg-white/15 p-4 backdrop-blur">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-white/70">Next lesson</p>
                <h2 className="mt-1 text-2xl font-black">{nextUnit?.title || "Bạn đã hoàn thành lộ trình"}</h2>
              </div>
              {nextUnit && (
                <Link to={`/learn/units/${nextUnit.id}`} className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-black text-primary shadow-lg transition hover:-translate-y-0.5">
                  <PlayCircle size={18} weight="fill" /> Start
                </Link>
              )}
            </div>
            <div className="mt-5 h-4 overflow-hidden rounded-full bg-white/20">
              <motion.div initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 0.8 }} className="h-full rounded-full bg-lime-300" />
            </div>
            <p className="mt-2 text-xs font-bold text-white/70">Course progress {progress}%</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
          {[
            [Fire, "Streak", gamification?.check_in?.current_streak || 0, "text-orange-200"],
            [Trophy, "Level", gamification?.xp?.level || 1, "text-lime-200"],
            [Gift, "Reward", `+${rewards.coin}`, "text-amber-200"],
          ].map(([Icon, label, value, color]) => (
            <div key={label} className="rounded-3xl bg-white/15 p-4 backdrop-blur">
              <Icon size={28} weight="fill" className={color} />
              <p className="mt-3 text-3xl font-black">{value}</p>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-white/65">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.section>
  );
};

const PreviewDrawer = ({ unit, onClose }) => {
  if (!unit) return null;
  const rewards = getUnitRewards(unit);
  const lessons = unit.lessons || [];
  const locked = unit.is_locked;

  return (
    <AnimatePresence>
      <motion.div className="fixed inset-0 z-50 flex justify-end bg-black/35 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
        <motion.aside initial={{ x: 420 }} animate={{ x: 0 }} exit={{ x: 420 }} transition={{ type: "spring", damping: 24 }} className="h-full w-full max-w-xl overflow-y-auto bg-white p-5 shadow-2xl dark:bg-zinc-950">
          <div className="rounded-[30px] bg-gradient-to-br from-zinc-950 to-zinc-800 p-5 text-white">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.2em] text-white/60">Lesson Preview</p>
                <h2 className="mt-2 text-3xl font-black">{unit.title}</h2>
                <p className="mt-2 text-sm leading-6 text-white/70">{unit.description || unit.section?.title || "Practice speaking through short interactive quests."}</p>
              </div>
              <button type="button" onClick={onClose} className="rounded-2xl bg-white/10 p-3 text-white transition hover:bg-white/20">
                <X size={18} />
              </button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="rounded-3xl bg-amber-50 p-4 text-amber-700"><p className="text-2xl font-black">+{rewards.coin}</p><p className="text-[10px] font-black uppercase">Coin</p></div>
            <div className="rounded-3xl bg-sky-50 p-4 text-sky-700"><p className="text-2xl font-black">+{rewards.xp}</p><p className="text-[10px] font-black uppercase">XP</p></div>
            <div className="rounded-3xl bg-violet-50 p-4 text-violet-700"><p className="text-2xl font-black">{lessons.length}</p><p className="text-[10px] font-black uppercase">Tasks</p></div>
          </div>

          <div className="mt-5 rounded-[30px] border border-zinc-200 p-5 dark:border-zinc-800">
            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-zinc-500">Quest Tasks</p>
            <div className="mt-4 space-y-3">
              {lessons.length === 0 ? <p className="text-sm font-semibold text-zinc-500">No task details yet.</p> : lessons.map((lesson, index) => (
                <div key={lesson.id} className="flex items-center gap-3 rounded-2xl bg-zinc-50 p-3 dark:bg-zinc-900">
                  <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-sm font-black text-primary shadow-sm dark:bg-zinc-800">{index + 1}</span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-black">{lesson.title}</p>
                    <p className="text-xs font-semibold text-zinc-500">{lesson.type || "practice"} · pass {lesson.pass_score || 80}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Link to={locked ? "#" : `/learn/units/${unit.id}`} className={`mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-4 text-sm font-black text-white transition ${locked ? "pointer-events-none bg-zinc-300" : "bg-primary hover:-translate-y-0.5"}`}>
            {locked ? <LockKey size={18} weight="fill" /> : <PlayCircle size={18} weight="fill" />}
            {locked ? "Locked" : "Start Quest"}
          </Link>
        </motion.aside>
      </motion.div>
    </AnimatePresence>
  );
};

const LearnPage = () => {
  const { gamification } = useAuth();
  const [data, setData] = useState(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      const cachedCurriculum = curriculumApi.getCachedCurriculum();
      if (cachedCurriculum && mounted) {
        setData(cachedCurriculum);
        setIsLoading(false);
        void curriculumApi.prefetchUnit(cachedCurriculum?.current_unit_id);
      }
      try {
        const response = await curriculumApi.getCurriculum();
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || "Không thể tải lộ trình học.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    if (curriculumApi.getCachedCurriculum()) {
      void curriculumApi.getCurriculum({ force: true }).then((response) => {
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      }).catch(() => null);
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const allUnits = useMemo(() => getAllUnits(data?.sections || []), [data]);
  const completedCount = allUnits.filter((unit) => unit.progress_status === "completed").length;
  const progress = allUnits.length ? Math.round((completedCount / allUnits.length) * 100) : 0;
  const nextUnit = allUnits.find((unit) => unit.id === data?.current_unit_id) || allUnits.find((unit) => !unit.is_locked && unit.progress_status !== "completed") || allUnits[0];

  if (isLoading) {
    return <div className="py-8 text-sm font-semibold text-muted-foreground">Đang tải lộ trình...</div>;
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 pb-10">
      <header className="sticky top-0 z-20 flex h-[72px] items-center border-b border-border bg-background/80 backdrop-blur-md">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-black uppercase tracking-wide text-muted-foreground transition-colors hover:text-foreground">
          <CaretLeft size={20} weight="bold" />
          <span>Back</span>
        </Link>
      </header>

      {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{error}</div>}

      <QuestHero nextUnit={nextUnit} progress={progress} gamification={gamification} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-8">
          {(data?.sections || []).map((section, sectionIndex) => {
            const accent = sectionColors[sectionIndex % sectionColors.length];
            return (
              <section key={section.id} className="rounded-[36px] border border-border bg-card p-5 shadow-sm">
                <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.2em] text-primary">{section.cefr_level || section.code || "Path"}</p>
                    <h2 className="mt-1 text-2xl font-black text-foreground">{section.title}</h2>
                    {section.description && <p className="mt-2 max-w-2xl text-sm font-semibold leading-6 text-muted-foreground">{section.description}</p>}
                  </div>
                  <div className={`rounded-2xl bg-gradient-to-br ${accent} px-4 py-3 text-sm font-black text-white shadow-lg`}>{(section.units || []).length} quests</div>
                </div>

                <div className="relative grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {(section.units || []).map((unit, unitIndex) => (
                    <LessonNode
                      key={unit.id}
                      unit={unit}
                      index={unitIndex}
                      status={unitStatus(unit, data?.current_unit_id)}
                      accent={accent}
                      onSelect={setSelectedUnit}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        <aside className="hidden lg:block">
          <div className="sticky top-24 rounded-[32px] border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Target size={26} weight="fill" /></span>
              <div>
                <p className="text-sm font-black">Daily focus</p>
                <p className="text-xs font-semibold text-muted-foreground">Finish one quest today</p>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              <div className="rounded-2xl bg-zinc-50 p-4 dark:bg-zinc-900"><p className="text-xs font-black uppercase text-zinc-500">Completed</p><p className="mt-1 text-3xl font-black">{completedCount}/{allUnits.length}</p></div>
              <div className="rounded-2xl bg-amber-50 p-4 text-amber-700"><p className="text-xs font-black uppercase">Coin balance</p><p className="mt-1 text-3xl font-black">{Number(gamification?.coin?.balance || 0).toLocaleString("en-US")}</p></div>
            </div>
          </div>
        </aside>
      </div>

      <PreviewDrawer unit={selectedUnit} onClose={() => setSelectedUnit(null)} />
    </div>
  );
};

export default LearnPage;
