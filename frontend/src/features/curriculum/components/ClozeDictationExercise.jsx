import { useMemo, useState } from "react";
import { CheckCircle, XCircle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const ClozeDictationExercise = ({ exercise, onAttempt }) => {
  const blanks = useMemo(() => exercise.content?.blanks || [], [exercise]);
  const [answers, setAnswers] = useState(() => blanks.map(() => ""));
  const [result, setResult] = useState(exercise.progress?.state?.last_feedback || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    setIsSubmitting(true);
    setError("");
    try {
      const response = await curriculumApi.attemptExercise(exercise.id, { answer: { blanks: answers } });
      setResult(response.feedback);
      onAttempt(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể kiểm tra đáp án.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      {exercise.content?.audio_url && <audio controls src={exercise.content.audio_url} className="w-full" />}
      <p className="rounded-xl bg-zinc-50 p-4 text-base font-semibold leading-8 text-zinc-800">
        {exercise.content?.passage || "Listen and fill in the missing words."}
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        {blanks.map((blank, index) => {
          const row = result?.blank_results?.find((item) => item.index === index);
          return (
            <label key={`${blank.answer}-${index}`} className="block rounded-xl border border-border bg-card p-4">
              <span className="text-xs font-black uppercase tracking-wide text-muted-foreground">Blank {index + 1}</span>
              <div className="mt-2 flex items-center gap-2">
                <input
                  value={answers[index] || ""}
                  onChange={(event) => setAnswers((current) => current.map((item, i) => (i === index ? event.target.value : item)))}
                  className="min-w-0 flex-1 rounded-lg border border-border px-3 py-2 text-sm font-semibold outline-none focus:border-primary"
                />
                {row?.correct === true && <CheckCircle className="text-emerald-600" size={22} weight="fill" />}
                {row?.correct === false && <XCircle className="text-rose-600" size={22} weight="fill" />}
              </div>
              {row?.correct === false && (
                <p className="mt-2 text-sm leading-6 text-rose-700">
                  Đáp án: <b>{row.answer}</b>. {row.explanation_vi || row.meaning_vi || ""}
                </p>
              )}
            </label>
          );
        })}
      </div>

      <button
        type="button"
        onClick={submit}
        disabled={isSubmitting}
        className="rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:opacity-60"
      >
        {isSubmitting ? "Đang kiểm tra..." : "Kiểm tra đáp án"}
      </button>
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default ClozeDictationExercise;
