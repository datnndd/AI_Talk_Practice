import { useRef, useState } from "react";
import { Microphone, Stop } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { createRecorder } from "@/features/curriculum/utils/audioRecorder";

const SentencePronunciationExercise = ({ exercise, onAttempt }) => {
  const [recording, setRecording] = useState(false);
  const [feedback, setFeedback] = useState(exercise.progress?.state?.last_feedback || null);
  const [error, setError] = useState("");
  const recorderRef = useRef(null);

  const submitAudio = async (audioBase64) => {
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, {
        audio_base64: audioBase64,
      });
      setFeedback(response.feedback);
      onAttempt(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể chấm phát âm. Vui lòng thử lại.");
    }
  };

  const toggleRecording = async () => {
    setError("");
    if (recording) {
      recorderRef.current?.stop();
      setRecording(false);
      return;
    }
    try {
      recorderRef.current = await createRecorder({ onStop: submitAudio });
      recorderRef.current.start();
      setRecording(true);
    } catch (err) {
      setError(err?.message || "Không thể mở microphone.");
    }
  };

  return (
    <div className="space-y-5">
      {exercise.content?.sample_audio_url && <audio controls src={exercise.content.sample_audio_url} className="w-full" />}
      <div className="rounded-xl bg-zinc-50 p-5">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Câu mẫu</p>
        <p className="mt-2 text-xl font-black leading-8 text-zinc-950">{exercise.content?.reference_text}</p>
      </div>
      <button
        type="button"
        onClick={toggleRecording}
        className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white"
      >
        {recording ? <Stop size={18} weight="fill" /> : <Microphone size={18} weight="fill" />}
        {recording ? "Dừng ghi âm" : "Ghi âm câu"}
      </button>
      {feedback?.assessment && (
        <div className="rounded-xl border border-border bg-card p-4 text-sm font-semibold">
          Score: {Math.round(feedback.assessment.score || 0)} ({feedback.assessment.source})
        </div>
      )}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default SentencePronunciationExercise;
