import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Circle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const VocabularyPronunciationExercise = lazy(() => import("@/features/curriculum/components/VocabularyPronunciationExercise"));
const ClozeDictationExercise = lazy(() => import("@/features/curriculum/components/ClozeDictationExercise"));
const SentencePronunciationExercise = lazy(() => import("@/features/curriculum/components/SentencePronunciationExercise"));
const ConversationExerciseLauncher = lazy(() => import("@/features/curriculum/components/ConversationExerciseLauncher"));
const WordAudioChoiceExercise = lazy(() => import("@/features/curriculum/components/WordAudioChoiceExercise"));

const renderExercise = (exercise, onAttempt) => {
  if (exercise.type === "vocab_pronunciation") {
    return <VocabularyPronunciationExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "cloze_dictation") {
    return <ClozeDictationExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "sentence_pronunciation") {
    return <SentencePronunciationExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "interactive_conversation") {
    return <ConversationExerciseLauncher exercise={exercise} onAttempt={onAttempt} />;
  }
  if (exercise.type === "word_audio_choice") {
    return <WordAudioChoiceExercise exercise={exercise} onAttempt={onAttempt} />;
  }
  return <p className="text-sm text-muted-foreground">Unsupported exercise type.</p>;
};

const LessonPlayerPage = () => {
  const { unitId } = useParams();
  const [unit, setUnit] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [rewardNotice, setRewardNotice] = useState("");

  const loadUnit = useCallback(async () => {
    const cachedUnit = curriculumApi.getCachedUnit(unitId);
    if (cachedUnit) {
      setUnit(cachedUnit);
      const firstOpen = cachedUnit.lessons.findIndex((item) => item.progress?.status !== "completed");
      setActiveIndex(firstOpen >= 0 ? firstOpen : 0);
    }
    setIsLoading(!cachedUnit);
    setError("");
    try {
      const data = await curriculumApi.getUnit(unitId);
      setUnit(data);
      const firstOpen = data.lessons.findIndex((item) => item.progress?.status !== "completed");
      setActiveIndex(firstOpen >= 0 ? firstOpen : 0);
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
        const firstOpen = data.lessons.findIndex((item) => item.progress?.status !== "completed");
        setActiveIndex(firstOpen >= 0 ? firstOpen : 0);
      }).catch(() => null);
    }
  }, [loadUnit]);

  const activeExercise = useMemo(() => unit?.lessons?.[activeIndex], [unit, activeIndex]);

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
  };

  const canGoNext = activeExercise?.progress?.status === "completed";

  if (isLoading) {
    return <div className="p-8 text-sm font-semibold text-muted-foreground">Đang tải bài học...</div>;
  }

  if (error || !unit) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
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
    <div className="mx-auto grid max-w-6xl gap-6 px-6 pb-12 pt-4 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="space-y-4">
        <Link to="/learn" className="inline-flex items-center gap-2 text-sm font-bold text-primary">
          <ArrowLeft size={16} /> Lộ trình
        </Link>
        <div className="rounded-xl border border-border bg-card p-4">
          <h1 className="text-2xl font-black text-zinc-950">{unit.title}</h1>
          {unit.description && <p className="mt-2 text-sm leading-6 text-muted-foreground">{unit.description}</p>}
        </div>
        <div className="space-y-2">
          {unit.lessons.map((exercise, index) => {
            const completed = exercise.progress?.status === "completed";
            return (
              <button
                key={exercise.id}
                type="button"
                onClick={() => setActiveIndex(index)}
                className={`flex w-full items-center gap-3 rounded-xl border px-3 py-3 text-left text-sm font-bold ${
                  activeIndex === index ? "border-primary bg-primary/5" : "border-border bg-card"
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
                <h2 className="mt-1 text-2xl font-black text-zinc-950">{activeExercise.title}</h2>
              </div>
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-black text-zinc-600">
                Pass {Math.round(activeExercise.pass_score)} · +{unit.xp_reward || 0} XP · +{unit.coin_reward || 0} Coin
              </span>
            </div>
            <Suspense fallback={<div className="py-6 text-sm font-semibold text-muted-foreground">Đang tải nội dung bài...</div>}>
              {renderExercise(activeExercise, handleAttempt)}
            </Suspense>
            <div className="mt-8 flex justify-end">
              <button
                type="button"
                disabled={!canGoNext || activeIndex >= unit.lessons.length - 1}
                onClick={() => setActiveIndex((current) => Math.min(current + 1, unit.lessons.length - 1))}
                className="rounded-xl bg-zinc-950 px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                Lesson tiếp theo
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default LessonPlayerPage;
