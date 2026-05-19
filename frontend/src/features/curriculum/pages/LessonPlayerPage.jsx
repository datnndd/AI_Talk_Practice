import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Circle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const ShadowingExercise = lazy(() => import("@/features/curriculum/components/ShadowingExercise"));
const ReadAloudExercise = lazy(() => import("@/features/curriculum/components/ReadAloudExercise"));
const DefinitionChoiceExercise = lazy(() => import("@/features/curriculum/components/DefinitionChoiceExercise"));
const QuickQaExercise = lazy(() => import("@/features/curriculum/components/QuickQaExercise"));

const renderExercise = (exercise, onAttempt) => {
  if (exercise.type === "shadowing") {
    return <ShadowingExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "read_aloud") {
    return <ReadAloudExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "definition_choice") {
    return <DefinitionChoiceExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "quick_qa") {
    return <QuickQaExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  return <p className="text-sm text-muted-foreground">Unsupported exercise type.</p>;
};

const buildLessonQueue = (lessons = []) => lessons.filter((item) => item.progress?.status !== "completed").map((item) => item.id);

const LessonPlayerPage = () => {
  const { unitId } = useParams();
  const [unit, setUnit] = useState(null);
  const [lessonQueue, setLessonQueue] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [rewardNotice, setRewardNotice] = useState("");

  const loadUnit = useCallback(async () => {
    const cachedUnit = curriculumApi.getCachedUnit(unitId);
    if (cachedUnit) {
      setUnit(cachedUnit);
      setLessonQueue(buildLessonQueue(cachedUnit.lessons));
    }
    setIsLoading(!cachedUnit);
    setError("");
    try {
      const data = await curriculumApi.getUnit(unitId);
      setUnit(data);
      setLessonQueue(buildLessonQueue(data.lessons));
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải unit.");
    } finally {
      setIsLoading(false);
    }
  }, [unitId]);

  useEffect(() => {
    void loadUnit();
    if (curriculumApi.getCachedUnit(unitId)) {
      void curriculumApi.getUnit(unitId, { force: true }).then((data) => {
        setUnit(data);
        setLessonQueue(buildLessonQueue(data.lessons));
      }).catch(() => null);
    }
  }, [loadUnit, unitId]);

  const activeLessonId = lessonQueue[0] || unit?.lessons?.find((item) => item.progress?.status !== "completed")?.id || unit?.lessons?.[0]?.id;
  const activeExercise = useMemo(
    () => unit?.lessons?.find((item) => item.id === activeLessonId) || null,
    [unit, activeLessonId],
  );

  const refreshUnit = useCallback(async () => {
    const data = await curriculumApi.getUnit(unitId, { force: true });
    setUnit(data);
    setLessonQueue(buildLessonQueue(data.lessons));
  }, [unitId]);

  const handleAttempt = (result) => {
    if (result.reward) {
      setRewardNotice(`+${result.reward.xp_earned || 0} XP · +${result.reward.coin_earned || 0} Coin`);
    }
    setUnit((current) => {
      if (!current) return current;
      return {
        ...current,
        progress_status: result.unit_completed ? "completed" : current.progress_status,
        lessons: current.lessons.map((exercise) =>
          exercise.id === result.lesson_id
            ? { ...exercise, progress: result.progress }
            : exercise
        ),
      };
    });
    setLessonQueue((currentQueue) => {
      const remaining = currentQueue.filter((lessonId) => lessonId !== result.lesson_id);
      if (result.progress?.status === "completed") {
        if (remaining.length === 0 && !result.unit_completed) {
          void refreshUnit().catch(() => null);
        }
        return remaining;
      }
      return [...remaining, result.lesson_id];
    });
  };

  const activeQueuePosition = activeExercise ? Math.max(lessonQueue.indexOf(activeExercise.id), 0) : 0;
  const queueTotal = lessonQueue.length;

  if (isLoading) {
    return <div className="py-8 text-sm font-semibold text-muted-foreground">Đang tải bài học...</div>;
  }

  if (error || !unit) {
    return (
      <div className="app-page-narrow py-6">
        <Link to="/learn" className="inline-flex items-center gap-2 text-sm font-bold text-primary">
          <ArrowLeft size={16} /> Quay lại lộ trình
        </Link>
        <div className="mt-6 rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error || "Unit không tồn tại."}
        </div>
      </div>
    );
  }

  return (
    <div className="app-page-wide grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="space-y-4">
        <Link to="/learn" className="inline-flex items-center gap-2 text-sm font-bold text-primary">
          <ArrowLeft size={16} /> Lộ trình
        </Link>
        <div className="rounded-xl border border-border bg-card p-4">
          <h1 className="text-2xl font-black text-[var(--page-fg)]">{unit.title}</h1>
          {unit.description && <p className="mt-2 text-sm leading-6 text-muted-foreground">{unit.description}</p>}
        </div>
        <div className="space-y-2">
          {unit.lessons.map((exercise) => {
            const completed = exercise.progress?.status === "completed";
            return (
              <button
                key={exercise.id}
                type="button"
                onClick={() => setLessonQueue((currentQueue) => [exercise.id, ...currentQueue.filter((lessonId) => lessonId !== exercise.id)])}
                className={`flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left text-sm font-bold ${
                  activeExercise?.id === exercise.id ? "border-primary bg-primary/5" : "border-border bg-card"
                }`}
              >
                {completed ? <CheckCircle size={18} weight="fill" className="text-emerald-600" /> : <Circle size={18} />}
                <span className="min-w-0 flex-1 truncate">{exercise.title}</span>
              </button>
            );
          })}
        </div>
      </aside>

      <main className="rounded-xl border border-border bg-card p-5 shadow-sm">
        {rewardNotice && (
          <div className="mb-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-black text-emerald-700">
                Hoàn thành unit: {rewardNotice}
          </div>
        )}
        {activeExercise && (
          <>
            <div className="mb-5 flex flex-col gap-2 border-b border-border pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.18em] text-primary">
                  {activeExercise.type.replaceAll("_", " ")}
                </p>
                <h2 className="mt-1 text-2xl font-black text-[var(--page-fg)]">{activeExercise.title}</h2>
              </div>
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-black text-[var(--page-muted)]">
                Pass {Math.round(activeExercise.pass_score)} · +{unit.xp_reward || 0} XP · +{unit.coin_reward || 0} Coin
              </span>
            </div>
            <Suspense fallback={<div className="py-6 text-sm font-semibold text-muted-foreground">Đang tải nội dung bài...</div>}>
              {renderExercise(activeExercise, handleAttempt)}
            </Suspense>
            <div className="mt-8 rounded-xl bg-muted px-4 py-3 text-sm font-bold text-muted-foreground ">
              {queueTotal > 0
                ? `H?ng ??i luy?n t?p: ${activeQueuePosition + 1}/${queueTotal}. Sai th? b?i s? quay l?i cu?i h?ng.`
                : "B?n ?? ho?n th?nh t?t c? b?i trong h?ng ??i."}
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default LessonPlayerPage;



