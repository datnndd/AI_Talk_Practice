import { useRef, useState } from "react";
import { Microphone, Stop } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { createRecorder } from "@/features/curriculum/utils/audioRecorder";

export const useExerciseRecorder = ({ exercise, onAttempt, defaultError }) => {
  const [recording, setRecording] = useState(false);
  const [feedback, setFeedback] = useState(exercise.progress?.state?.last_feedback || null);
  const [error, setError] = useState("");
  const recorderRef = useRef(null);

  const submitAudio = async (audioBase64) => {
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, { audio_base64: audioBase64 });
      setFeedback(response.feedback);
      onAttempt(response);
    } catch (err) {
      setError(err?.response?.data?.detail || defaultError);
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

  const RecordButton = () => (
    <button
      type="button"
      onClick={toggleRecording}
      className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white"
    >
      {recording ? <Stop size={18} weight="fill" /> : <Microphone size={18} weight="fill" />}
      {recording ? "Dừng ghi âm" : "Ghi âm"}
    </button>
  );

  return { recording, feedback, error, RecordButton };
};
