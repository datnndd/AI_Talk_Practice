import { useRef, useState } from "react";
import { useExerciseRecorder } from "@/features/curriculum/components/useExerciseRecorder";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const ShadowingExercise = ({ exercise, onAttempt }) => {
  const audioRef = useRef(null);
  const [speed, setSpeed] = useState(1);
  const { feedback, error, RecordButton } = useExerciseRecorder({
    exercise,
    onAttempt,
    defaultError: "Không thể chấm phát âm. Vui lòng thử lại.",
  });
  const content = exercise.content || {};
  const audioUrl = speed === 0.75 && content.slow_audio_url ? content.slow_audio_url : content.sample_audio_url;

  const changeSpeed = (value) => {
    setSpeed(value);
    if (audioRef.current) audioRef.current.playbackRate = value;
  };

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-muted p-5 text-[var(--page-fg)]">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Nghe và lặp lại</p>
        <p className="mt-2 text-2xl font-black leading-9 text-[var(--page-fg)]">{content.reference_text}</p>
        {content.meaning_vi && <p className="mt-2 text-sm font-semibold text-[var(--page-muted)]">{content.meaning_vi}</p>}
      </div>
      {audioUrl && (
        <div className="space-y-3">
          <audio ref={audioRef} controls src={absoluteAudioUrl(audioUrl)} className="w-full" onLoadedMetadata={() => changeSpeed(speed)} />
          <div className="flex gap-2">
            {[0.75, 1].map((value) => (
              <button key={value} type="button" onClick={() => changeSpeed(value)} className={`rounded-full px-4 py-2 text-xs font-black ${speed === value ? "bg-primary text-white" : "bg-muted text-[var(--page-muted)]"}`}>
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
