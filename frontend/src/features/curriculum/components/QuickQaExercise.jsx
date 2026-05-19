import { useExerciseRecorder } from "@/features/curriculum/components/useExerciseRecorder";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const QuickQaExercise = ({ exercise, onAttempt }) => {
  const { feedback, error, RecordButton } = useExerciseRecorder({
    exercise,
    onAttempt,
    defaultError: "Kh?ng th? ch?m c?u tr? l?i. Vui l?ng th? l?i.",
  });
  const content = exercise.content || {};
  const hints = content.answer_hints || [];

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-muted p-5 text-[var(--page-fg)]">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Tr? l?i nhanh</p>
        <p className="mt-2 text-2xl font-black leading-9 text-[var(--page-fg)]">{content.question_text}</p>
        {content.question_audio_url && <audio controls src={absoluteAudioUrl(content.question_audio_url)} className="mt-3 w-full" />}
      </div>
      {hints.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">G?i ?</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {hints.map((hint, index) => <span key={`${hint}-${index}`} className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{hint}</span>)}
          </div>
        </div>
      )}
      <RecordButton />
      {feedback && <div className={`rounded-xl px-4 py-3 text-sm font-bold ${feedback.correct ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>Transcript: {feedback.transcript || "Kh?ng nh?n di?n ???c."}</div>}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default QuickQaExercise;
