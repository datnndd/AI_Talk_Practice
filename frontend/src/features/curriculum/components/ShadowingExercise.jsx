import { useRef, useState } from "react";
import { useExerciseRecorder } from "@/features/curriculum/components/useExerciseRecorder";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const ShadowingExercise = ({ exercise, onAttempt }) => {
  const audioRef = useRef(null);
  const [speed, setSpeed] = useState(1);
  const { feedback, error, RecordButton } = useExerciseRecorder({
    exercise,
    onAttempt,
    defaultError: "Kh?ng th? ch?m ph?t ?m. Vui l?ng th? l?i.",
  });
  const content = exercise.content || {};
  const audioUrl = speed === 0.75 && content.slow_audio_url ? content.slow_audio_url : content.sample_audio_url;

  const changeSpeed = (value) => {
    setSpeed(value);
    if (audioRef.current) audioRef.current.playbackRate = value;
  };

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-zinc-50 p-5 dark:bg-zinc-900">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Nghe v? l?p l?i</p>
        <p className="mt-2 text-2xl font-black leading-9 text-zinc-950 dark:text-white">{content.reference_text}</p>
        {content.meaning_vi && <p className="mt-2 text-sm font-semibold text-zinc-600 dark:text-zinc-300">{content.meaning_vi}</p>}
      </div>
      {audioUrl && (
        <div className="space-y-3">
          <audio ref={audioRef} controls src={absoluteAudioUrl(audioUrl)} className="w-full" onLoadedMetadata={() => changeSpeed(speed)} />
          <div className="flex gap-2">
            {[0.75, 1].map((value) => (
              <button key={value} type="button" onClick={() => changeSpeed(value)} className={`rounded-full px-4 py-2 text-xs font-black ${speed === value ? "bg-primary text-white" : "bg-zinc-100 text-zinc-700"}`}>
                {value}x
              </button>
            ))}
          </div>
        </div>
      )}
      <RecordButton />
      {feedback?.assessment && <div className="rounded-xl border border-border bg-card p-4 text-sm font-semibold">Score: {Math.round(feedback.assessment.score || 0)} ({feedback.assessment.source})</div>}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default ShadowingExercise;
