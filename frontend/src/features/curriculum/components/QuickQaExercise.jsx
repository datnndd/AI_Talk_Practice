import { useExerciseRecorder } from "@/features/curriculum/components/useExerciseRecorder";
import { absoluteAudioUrl } from "@/features/curriculum/components/lessonAudio";

const QuickQaExercise = ({ exercise, onAttempt }) => {
  const { feedback, error, isCompleted, RecordButton } = useExerciseRecorder({
    exercise,
    onAttempt,
    defaultError: "Không thể chấm câu trả lời. Vui lòng thử lại.",
  });
  const content = exercise.content || {};
  const hints = content.answer_hints || [];
  const score = Number(feedback?.score ?? 0);
  const passScore = Number(feedback?.pass_score ?? exercise.pass_score ?? 0);
  const passed = Boolean(feedback?.passed ?? feedback?.correct);

  return (
    <div className="space-y-5">
      <div className="rounded-xl bg-muted p-5 text-[var(--page-fg)]">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Trả lời nhanh</p>
        <p className="mt-2 text-2xl font-black leading-9 text-[var(--page-fg)]">{content.question_text}</p>
        {content.question_audio_url && <audio controls src={absoluteAudioUrl(content.question_audio_url)} className="mt-3 w-full" />}
      </div>
      {hints.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Gợi ý</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {hints.map((hint, index) => <span key={`${hint}-${index}`} className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{hint}</span>)}
          </div>
        </div>
      )}
      <RecordButton />
      {isCompleted && <div className="rounded-xl bg-muted px-4 py-3 text-sm font-bold text-muted-foreground">Bài đã hoàn thành. Bạn chỉ có thể xem lại câu trả lời, không thể ghi âm lại.</div>}
      {feedback && (
        <div className={`space-y-3 rounded-xl px-4 py-3 text-sm font-bold ${passed ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>{passed ? "Đạt yêu cầu" : "Chưa đạt"}</span>
            <span>{Math.round(score)}/{Math.round(passScore)} điểm</span>
          </div>
          <p>Transcript: {feedback.transcript || "Không nhận diện được."}</p>
          {feedback.reason && <p>Nhận xét: {feedback.reason}</p>}
          {feedback.suggested_answer && <p>Gợi ý trả lời: {feedback.suggested_answer}</p>}
        </div>
      )}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default QuickQaExercise;
