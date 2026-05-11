import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import {
  CheckCircle,
  LockKey,
  PlayCircle,
  Star,
  X,
} from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

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

const cefrOrder = { A1: 0, A2: 1, B1: 2, B2: 3, C1: 4, C2: 5 };

const getUnitLabel = (unit) => {
  if (unit.progress_status === "completed") return "Completed";
  if (unit.is_locked) return "Complete previous units";
  if (unit.id === unit.current_unit_id) return "Recommended";
  if ((cefrOrder[unit.section_cefr_level] ?? 0) < (cefrOrder[unit.current_cefr] ?? 0)) return "Review";
  return "Open";
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
      <span className="relative z-10 mt-2 rounded-full bg-white/80 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.14em] text-zinc-600">
        {getUnitLabel(unit)}
      </span>
      <div className="relative z-10 mt-3 flex flex-wrap justify-center gap-2 text-[10px] font-black uppercase tracking-[0.14em]">
        <span className="rounded-full bg-white/80 px-2.5 py-1 text-amber-600">+{rewards.coin} coin</span>
        <span className="rounded-full bg-white/80 px-2.5 py-1 text-sky-600">+{rewards.xp} XP</span>
      </div>
    </motion.button>
  );
};

const PreviewDrawer = ({ unit, onClose }) => {
  if (!unit) return null;
  const rewards = getUnitRewards(unit);
  const lessons = unit.lessons || [];
  const locked = unit.is_locked;
  const lockedCopy = getUnitLabel(unit);

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
            {locked ? lockedCopy : "Start Quest"}
          </Link>
        </motion.aside>
      </motion.div>
    </AnimatePresence>
  );
};

const LearnPage = () => {
  const [data, setData] = useState(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [expandedSectionIds, setExpandedSectionIds] = useState(() => new Set());
  const [loadingSectionId, setLoadingSectionId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSectionDetail = async (sectionId) => {
    setLoadingSectionId(sectionId);
    setError("");
    try {
      const section = await curriculumApi.getSection(sectionId);
      setData((current) => ({
        ...current,
        sections: (current?.sections || []).map((item) => (item.id === sectionId ? section : item)),
      }));
      setExpandedSectionIds((current) => new Set(current).add(sectionId));
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải chi tiết section.");
    } finally {
      setLoadingSectionId(null);
    }
  };

  const toggleSection = async (sectionId) => {
    if (expandedSectionIds.has(sectionId)) {
      setExpandedSectionIds((current) => {
        const next = new Set(current);
        next.delete(sectionId);
        return next;
      });
      return;
    }
    await loadSectionDetail(sectionId);
  };

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

  if (isLoading) {
    return <div className="py-8 text-sm font-semibold text-muted-foreground">Đang tải lộ trình...</div>;
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 pb-10">
      <div className="relative overflow-hidden rounded-[30px] bg-gradient-to-br from-zinc-950 via-indigo-950 to-primary p-5 text-white shadow-xl shadow-primary/10 md:p-6">
        <div className="pointer-events-none absolute -right-14 -top-20 h-44 w-44 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/2 h-48 w-48 rounded-full bg-sky-300/20 blur-3xl" />
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] backdrop-blur">
              <Star size={13} weight="fill" /> Learning Path
            </div>
            <h1 className="mt-3 max-w-3xl text-2xl font-black tracking-tight md:text-3xl">Học theo lộ trình, mở khóa từng nhiệm vụ</h1>
            <p className="mt-2 max-w-2xl text-sm font-semibold leading-6 text-white/70">
              Hoàn thành bài học ngắn, luyện nói từng bước, tích XP và coin rồi tiếp tục lên cấp theo đúng tiến độ của bạn.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-[11px] font-black">
            <div className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2 backdrop-blur">
              <Star size={15} weight="fill" /> Start
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2 backdrop-blur">
              <PlayCircle size={15} weight="fill" /> Practice
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-3 py-2 backdrop-blur">
              <CheckCircle size={15} weight="fill" /> Level up
            </div>
          </div>
        </div>
      </div>

      {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{error}</div>}

      <div className="space-y-8">
          {(data?.sections || []).map((section, sectionIndex) => {
            const accent = sectionColors[sectionIndex % sectionColors.length];
            const isExpanded = expandedSectionIds.has(section.id);
            const isSectionLoading = loadingSectionId === section.id;
            return (
              <section key={section.id} className="rounded-[36px] border border-border bg-card p-5 shadow-sm">
                <button type="button" onClick={() => toggleSection(section.id)} className="mb-5 flex w-full flex-wrap items-center justify-between gap-3 text-left">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.2em] text-primary">{section.cefr_level || section.code || "Path"}</p>
                    <h2 className="mt-1 text-2xl font-black text-foreground">{section.title}</h2>
                    {section.description && <p className="mt-2 max-w-2xl text-sm font-semibold leading-6 text-muted-foreground">{section.description}</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    {isSectionLoading && <span className="text-[10px] font-black uppercase tracking-[0.18em] text-muted-foreground">Đang tải</span>}
                    <div className={`rounded-2xl bg-gradient-to-br ${accent} px-4 py-3 text-sm font-black text-white shadow-lg`}>
                      {isExpanded ? `${(section.units || []).length} quests` : "Xem chi tiết"}
                    </div>
                  </div>
                </button>

                {isExpanded && (
                <div className="relative grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {(section.units || []).map((unit, unitIndex) => (
                    <LessonNode
                      key={unit.id}
                      unit={{
                        ...unit,
                        current_unit_id: data?.current_unit_id,
                        current_cefr: data?.current_cefr,
                        section_cefr_level: section.cefr_level,
                      }}
                      index={unitIndex}
                      status={unitStatus(unit, data?.current_unit_id)}
                      accent={accent}
                      onSelect={setSelectedUnit}
                    />
                  ))}
                </div>
                )}
              </section>
            );
          })}
      </div>

      <PreviewDrawer unit={selectedUnit} onClose={() => setSelectedUnit(null)} />
    </div>
  );
};

export default LearnPage;
