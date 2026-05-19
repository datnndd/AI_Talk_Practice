import { useMemo, useState } from "react";
import { CheckCircle, SpeakerHigh } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const shuffle = (items) => [...items].map((item) => ({ item, sort: Math.random() })).sort((a, b) => a.sort - b.sort).map(({ item }) => item);
const EMPTY_OPTIONS = [];

const DefinitionChoiceExercise = ({ exercise, onAttempt }) => {
  const [selectedWord, setSelectedWord] = useState("");
  const [result, setResult] = useState(exercise.progress?.state?.last_feedback || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const isCompleted = exercise.progress?.status === "completed";
  const content = exercise.content || {};
  const contentOptions = content.options || EMPTY_OPTIONS;
  const options = useMemo(() => shuffle(contentOptions), [contentOptions]);

  const selectWord = (word) => {
    if (isCompleted) return;
    setSelectedWord(word);
    setResult(null);
    setError("");
  };

  const submit = async () => {
    if (!selectedWord || isSubmitting || isCompleted) return;
    const previousResult = result;
    const correctOption = contentOptions.find((option) => option?.is_correct === true);
    const selectedOption = contentOptions.find((option) => option?.word === selectedWord);
    const localResult = {
      correct: Boolean(selectedOption?.is_correct),
      correct_word: correctOption?.word || "",
      selected_word: selectedWord,
    };
    setResult(localResult);
    setIsSubmitting(true);
    setError("");
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, { answer: { selected_word: selectedWord } });
      setResult(response.feedback);
      onAttempt(response);
    } catch (err) {
      setResult(previousResult);
      setError(err?.response?.data?.detail || "Không thể chấm bài.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
    <div className="rounded-xl bg-muted p-5 text-[var(--page-fg)]">
        <p className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wide text-muted-foreground"><SpeakerHigh size={18} weight="fill" /> Nghe định nghĩa và chọn từ</p>
        {content.definition_audio_url && <audio controls src={absoluteAudioUrl(content.definition_audio_url)} className="mt-3 w-full" />}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option, index) => {
          const active = selectedWord === option.word;
          return (
            <button key={`${option.word}-${index}`} type="button" disabled={isSubmitting || isCompleted} onClick={() => selectWord(option.word)} className={`rounded-xl border p-4 text-left transition disabled:cursor-not-allowed disabled:opacity-70 ${active ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"}`}>
              <div className="flex items-center justify-between gap-3">
                <span className="text-base font-black">{option.word}</span>
                {active && <CheckCircle size={18} weight="fill" className="text-primary" />}
              </div>
              {option.meaning_vi && <p className="mt-1 text-xs font-semibold text-muted-foreground">{option.meaning_vi}</p>}
            </button>
          );
        })}
      </div>
      <button type="button" disabled={!selectedWord || isSubmitting || isCompleted} onClick={submit} className="rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-50">
        {isCompleted ? "Đã hoàn thành" : isSubmitting ? "Đang lưu kết quả..." : result?.correct ? "Đúng rồi" : result && !result.correct ? "Chưa đúng" : "Chọn đáp án"}
      </button>
      {isCompleted && <div className="rounded-xl bg-muted px-4 py-3 text-sm font-bold text-muted-foreground">Bài đã hoàn thành. Bạn chỉ có thể xem lại đáp án, không thể làm lại.</div>}
      {result && <div className={`rounded-xl px-4 py-3 text-sm font-bold ${result.correct ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>{result.correct ? "Đúng rồi." : `Chưa đúng. Đáp án là ${result.correct_word}.`}</div>}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default DefinitionChoiceExercise;
