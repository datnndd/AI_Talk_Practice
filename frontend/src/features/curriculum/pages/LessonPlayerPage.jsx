import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Circle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const ShadowingExercise = lazy(() => import("@/features/curriculum/components/ShadowingExercise"));
const DefinitionChoiceExercise = lazy(() => import("@/features/curriculum/components/DefinitionChoiceExercise"));
const QuickQaExercise = lazy(() => import("@/features/curriculum/components/QuickQaExercise"));

const renderExercise = (exercise, onAttempt) => {
  if (exercise.type === "shadowing") {
    return <ShadowingExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "definition_choice") {
    return <DefinitionChoiceExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "quick_qa") {
    return <QuickQaExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  return <p className="text-sm text-muted-foreground">Unsupported exercise type.</p>;
};

const getFirstOpenExerciseId = (lessons = []) => lessons.find((item) => item.progress?.status !== "completed")?.id || lessons[0]?.id || null;

const getFirstOpenExerciseIndex = (lessons = []) => {
  const index = lessons.findIndex((item) => item.progress?.status !== "completed");
  return index >= 0 ? index : Math.max(lessons.length - 1, 0);
};

const LessonPlayerPage = () => {
  const { unitId } = useParams();
  const [unit, setUnit] = useState(null);
  const [selectedExerciseId, setSelectedExerciseId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [rewardNotice, setRewardNotice] = useState("");

  const loadUnit = useCallback(async () => {
    const cachedUnit = curriculumApi.getCachedUnit(unitId);
    if (cachedUnit) {
      setUnit(cachedUnit);
      setSelectedExerciseId(getFirstOpenExerciseId(cachedUnit.lessons));
    }
    setIsLoading(!cachedUnit);
    setError("");
    try {
      const data = await curriculumApi.getUnit(unitId);
      setUnit(data);
      setSelectedExerciseId(getFirstOpenExerciseId(data.lessons));
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
        setSelectedExerciseId(getFirstOpenExerciseId(data.lessons));
      }).catch(() => null);
    }
  }, [loadUnit, unitId]);

  const firstOpenIndex = useMemo(() => getFirstOpenExerciseIndex(unit?.lessons || []), [unit]);
  const selectedExerciseIndex = useMemo(
    () => unit?.lessons?.findIndex((item) => item.id === selectedExerciseId) ?? -1,
    [unit, selectedExerciseId],
  );
  const activeExercise = useMemo(() => {
    const lessons = unit?.lessons || [];
    if (!lessons.length) return null;
    if (selectedExerciseIndex >= 0 && selectedExerciseIndex <= firstOpenIndex) {
      return lessons[selectedExerciseIndex];
    }
    return lessons[firstOpenIndex] || lessons[0] || null;
  }, [firstOpenIndex, selectedExerciseIndex, unit]);

  const refreshUnit = useCallback(async () => {
    const data = await curriculumApi.getUnit(unitId, { force: true });
    setUnit(data);
    setSelectedExerciseId(getFirstOpenExerciseId(data.lessons));
  }, [unitId]);

  const handleAttempt = (result) => {
    if (result.reward) {
      setRewardNotice(`+${result.reward.xp_earned || 0} XP · +${result.reward.coin_earned || 0} Coin`);
    }
    setUnit((current) => {
      if (!current) return current;
      const nextLessons = current.lessons.map((exercise) =>
        exercise.id === result.lesson_id
          ? { ...exercise, progress: result.progress }
          : exercise
      );
      if (result.progress?.status === "completed") {
        setSelectedExerciseId(getFirstOpenExerciseId(nextLessons));
      }
      return {
        ...current,
        progress_status: result.unit_completed ? "completed" : current.progress_status,
        lessons: nextLessons,
      };
    });
    if (result.progress?.status === "completed" && !result.unit_completed) {
      void refreshUnit().catch(() => null);
    }
  };

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
          {unit.lessons.map((exercise, index) => {
            const completed = exercise.progress?.status === "completed";
            const unlocked = index <= firstOpenIndex;
            return (
              <button
                key={exercise.id}
                type="button"
                disabled={!unlocked}
                onClick={() => setSelectedExerciseId(exercise.id)}
                className={`flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left text-sm font-bold ${
                  activeExercise?.id === exercise.id
                    ? "border-primary bg-primary/5"
                    : unlocked
                      ? "border-border bg-card"
                      : "cursor-not-allowed border-border bg-muted opacity-60"
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
              {unit.progress_status === "completed"
                ? "Bạn đã hoàn thành tất cả bài trong unit."
                : "Hoàn thành bài hiện tại để mở bài tiếp theo."}
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default LessonPlayerPage;



