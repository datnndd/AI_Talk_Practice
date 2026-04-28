import { useMemo, useRef, useState } from "react";
import { Microphone, Stop, SpeakerHigh } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";
import { createRecorder } from "@/features/curriculum/utils/audioRecorder";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const wordLabel = (item) => (typeof item === "string" ? item : item.word);

const VocabularyPronunciationExercise = ({ exercise, onAttempt }) => {
  const words = useMemo(() => exercise.content?.words || [], [exercise]);
  const passedWords = new Set(exercise.progress?.state?.passed_words || []);
  const retryWords = exercise.progress?.state?.retry_words || [];
  const [activeWord, setActiveWord] = useState(() => wordLabel(words[0] || ""));
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const recorderRef = useRef(null);

  const currentWord = activeWord || wordLabel(words.find((item) => !passedWords.has(wordLabel(item))) || words[0] || "");

  const submitAudio = async (audioBase64) => {
    try {
      const result = await curriculumApi.attemptLesson(exercise.id, {
        audio_base64: audioBase64,
        answer: { word: currentWord },
      });
      onAttempt(result);
      const next = words.map(wordLabel).find((word) => !(result.progress?.state?.passed_words || []).includes(word));
      if (next) {
        setActiveWord(next);
      }
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
      <div className="grid gap-3 sm:grid-cols-2">
        {words.map((item) => {
          const word = wordLabel(item);
          const isPassed = passedWords.has(word);
          return (
            <button
              type="button"
              key={word}
              onClick={() => setActiveWord(word)}
              className={`rounded-xl border px-4 py-3 text-left ${
                word === currentWord ? "border-primary bg-primary/5" : "border-border bg-card"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-lg font-black">{word}</span>
                <span className={`text-xs font-bold ${isPassed ? "text-emerald-600" : "text-zinc-500"}`}>
                  {isPassed ? "Passed" : "Pending"}
                </span>
              </div>
              {item.meaning_vi && <p className="mt-1 text-sm text-muted-foreground">{item.meaning_vi}</p>}
            </button>
          );
        })}
      </div>

      {retryWords.length > 0 && (
        <div className="rounded-xl bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
          Cần luyện lại: {retryWords.join(", ")}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {currentWord && (
          <audio
            controls
            src={`${getApiBaseUrl()}/curriculum/dictionary/audio?word=${encodeURIComponent(currentWord)}&lang=en`}
            className="h-10"
          />
        )}
        <button
          type="button"
          onClick={toggleRecording}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-black text-white"
        >
          {recording ? <Stop size={18} weight="fill" /> : <Microphone size={18} weight="fill" />}
          {recording ? "Dừng ghi âm" : `Phát âm: ${currentWord}`}
        </button>
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-muted-foreground">
          <SpeakerHigh size={14} /> Nghe mẫu rồi ghi âm từng từ.
        </span>
      </div>

      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default VocabularyPronunciationExercise;
