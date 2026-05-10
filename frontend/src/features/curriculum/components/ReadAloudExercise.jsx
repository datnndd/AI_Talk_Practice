import { useExerciseRecorder } from "@/features/curriculum/components/useExerciseRecorder";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const ReadAloudExercise = ({ exercise, onAttempt }) => {
  const { feedback, error, RecordButton } = useExerciseRecorder({
    exercise,
    onAttempt,
    defaultError: "Kh?ng th? ch?m b?i ??c. Vui l?ng th? l?i.",
  });
  const content = exercise.content || {};

  return (
    <div className="space-y-5">
      {content.sample_audio_url && <audio controls src={absoluteAudioUrl(content.sample_audio_url)} className="w-full" />}
      <div className="rounded-xl bg-zinc-50 p-5 dark:bg-zinc-900">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">??c to v?n b?n</p>
        <p className="mt-2 whitespace-pre-line text-xl font-black leading-8 text-zinc-950 dark:text-white">{content.text}</p>
        {content.meaning_vi && <p className="mt-3 whitespace-pre-line text-sm font-semibold text-zinc-600 dark:text-zinc-300">{content.meaning_vi}</p>}
      </div>
      <RecordButton />
      {feedback?.assessment && <div className="rounded-xl border border-border bg-card p-4 text-sm font-semibold">Score: {Math.round(feedback.assessment.score || 0)} ({feedback.assessment.source})</div>}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default ReadAloudExercise;
