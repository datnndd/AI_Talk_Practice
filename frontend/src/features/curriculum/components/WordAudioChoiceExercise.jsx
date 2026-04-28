import { useMemo, useState } from "react";
import { CheckCircle, SpeakerHigh } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const shuffle = (items) =>
  [...items]
    .map((item) => ({ item, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map(({ item }) => item);

const absoluteAudioUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${getApiBaseUrl()}${url.startsWith("/") ? url : `/${url}`}`;
};

const WordAudioChoiceExercise = ({ exercise, onAttempt }) => {
  const [selectedWord, setSelectedWord] = useState("");
  const [result, setResult] = useState(exercise.progress?.state?.last_feedback || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const options = useMemo(() => shuffle(exercise.content?.options || []), [exercise.id]);
  const promptWord = exercise.content?.prompt_word || "";

  const submit = async () => {
    if (!selectedWord) return;
    setIsSubmitting(true);
    setError("");
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, {
        answer: { selected_word: selectedWord },
      });
      setResult(response.feedback);
      onAttempt(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể chấm bài.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-border bg-zinc-50 p-4">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">Choose the matching audio</p>
        <h3 className="mt-2 text-3xl font-black text-zinc-950">{promptWord}</h3>
        <p className="mt-2 text-xs font-semibold text-muted-foreground">
          Audio source: dict.minhqnd.com
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option, index) => {
          const active = selectedWord === option.word;
          return (
            <button
              type="button"
              key={`${option.word}-${index}`}
              onClick={() => setSelectedWord(option.word)}
              className={`rounded-xl border p-4 text-left transition ${
                active ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2 text-sm font-black">
                  <SpeakerHigh size={18} weight="fill" /> Audio {index + 1}
                </span>
                {active && <CheckCircle size={18} weight="fill" className="text-primary" />}
              </div>
              {option.audio_url && (
                <audio
                  controls
                  src={absoluteAudioUrl(option.audio_url)}
                  className="mt-3 h-10 w-full"
                  onClick={(event) => event.stopPropagation()}
                />
              )}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        disabled={!selectedWord || isSubmitting}
        onClick={submit}
        className="rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Đang chấm..." : "Chọn đáp án"}
      </button>

      {result && (
        <div className={`rounded-xl px-4 py-3 text-sm font-bold ${result.correct ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
          {result.correct ? "Đúng." : `Chưa đúng. Đáp án là ${result.correct_word}.`}
        </div>
      )}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default WordAudioChoiceExercise;
