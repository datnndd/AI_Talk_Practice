import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle, Circle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import VocabularyPronunciationExercise from "@/features/curriculum/components/VocabularyPronunciationExercise";
import ClozeDictationExercise from "@/features/curriculum/components/ClozeDictationExercise";
import SentencePronunciationExercise from "@/features/curriculum/components/SentencePronunciationExercise";
import ConversationExerciseLauncher from "@/features/curriculum/components/ConversationExerciseLauncher";

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
  return <p className="text-sm text-muted-foreground">Unsupported exercise type.</p>;
};

const LessonPlayerPage = () => {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [rewardNotice, setRewardNotice] = useState("");

  const loadLesson = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await curriculumApi.getLesson(lessonId);
      setLesson(data);
      const firstOpen = data.exercises.findIndex((item) => item.progress?.status !== "completed");
      setActiveIndex(firstOpen >= 0 ? firstOpen : 0);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể tải bài học.");
    } finally {
      setIsLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    void loadLesson();
  }, [loadLesson]);

  const activeExercise = useMemo(() => lesson?.exercises?.[activeIndex], [lesson, activeIndex]);

  const handleAttempt = (result) => {
    if (result.reward) {
      setRewardNotice(`+${result.reward.xp_earned || 0} XP · +${result.reward.coin_earned || 0} Coin`);
    }
    setLesson((current) => {
      if (!current) return current;
      return {
        ...current,
        progress_status: result.lesson_completed ? "completed" : current.progress_status,
        exercises: current.exercises.map((exercise) =>
          exercise.id === result.exercise_id
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

  if (error || !lesson) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <Link to="/learn" className="inline-flex items-center gap-2 text-sm font-bold text-primary">
          <ArrowLeft size={16} /> Quay lại lộ trình
        </Link>
        <div className="mt-6 rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
          {error || "Bài học không tồn tại."}
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
          <h1 className="text-2xl font-black text-zinc-950">{lesson.title}</h1>
          {lesson.description && <p className="mt-2 text-sm leading-6 text-muted-foreground">{lesson.description}</p>}
        </div>
        <div className="space-y-2">
          {lesson.exercises.map((exercise, index) => {
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
            Hoàn thành bài học: {rewardNotice}
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
                Pass {Math.round(activeExercise.pass_score)} · +{lesson.xp_reward || 0} XP · +{lesson.coin_reward || 0} Coin
              </span>
            </div>
            {renderExercise(activeExercise, handleAttempt)}
            <div className="mt-8 flex justify-end">
              <button
                type="button"
                disabled={!canGoNext || activeIndex >= lesson.exercises.length - 1}
                onClick={() => setActiveIndex((current) => Math.min(current + 1, lesson.exercises.length - 1))}
                className="rounded-xl bg-zinc-950 px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                Bài tập tiếp theo
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default LessonPlayerPage;
