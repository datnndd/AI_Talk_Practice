import { useMemo, useState } from "react";
import { CheckCircle, SpeakerHigh } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const shuffle = (items) => [...items].map((item) => ({ item, sort: Math.random() })).sort((a, b) => a.sort - b.sort).map(({ item }) => item);

const DefinitionChoiceExercise = ({ exercise, onAttempt }) => {
  const [selectedWord, setSelectedWord] = useState("");
  const [result, setResult] = useState(exercise.progress?.state?.last_feedback || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const content = exercise.content || {};
  const options = useMemo(() => shuffle(content.options || []), [exercise.id]);

  const submit = async () => {
    if (!selectedWord) return;
    setIsSubmitting(true);
    setError("");
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, { answer: { selected_word: selectedWord } });
      setResult(response.feedback);
      onAttempt(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Kh?ng th? ch?m b?i.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-zinc-50 p-5 dark:bg-zinc-900">
        <p className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wide text-muted-foreground"><SpeakerHigh size={18} weight="fill" /> Nghe ??nh ngh?a v? ch?n t?</p>
        {content.definition_audio_url && <audio controls src={absoluteAudioUrl(content.definition_audio_url)} className="mt-3 w-full" />}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option, index) => {
          const active = selectedWord === option.word;
          return (
            <button key={`${option.word}-${index}`} type="button" onClick={() => setSelectedWord(option.word)} className={`rounded-xl border p-4 text-left transition ${active ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"}`}>
              <div className="flex items-center justify-between gap-3">
                <span className="text-base font-black">{option.word}</span>
                {active && <CheckCircle size={18} weight="fill" className="text-primary" />}
              </div>
              {option.meaning_vi && <p className="mt-1 text-xs font-semibold text-muted-foreground">{option.meaning_vi}</p>}
            </button>
          );
        })}
      </div>
      <button type="button" disabled={!selectedWord || isSubmitting} onClick={submit} className="rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-50">{isSubmitting ? "?ang ch?m..." : "Ch?n ??p ?n"}</button>
      {result && <div className={`rounded-xl px-4 py-3 text-sm font-bold ${result.correct ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>{result.correct ? "??ng." : `Ch?a ??ng. ??p ?n l? ${result.correct_word}.`}</div>}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default DefinitionChoiceExercise;
