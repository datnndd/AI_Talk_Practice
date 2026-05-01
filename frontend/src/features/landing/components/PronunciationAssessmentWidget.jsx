import { useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle, MicrophoneStage, SpeakerHigh, Stop, WarningCircle, Waveform } from "@phosphor-icons/react";

import { pronunciationAssessmentApi } from "@/features/landing/api/pronunciationAssessmentApi";
import { startLandingPronunciationRecorder } from "@/features/landing/utils/landingPronunciationRecorder";

const DEFAULT_REFERENCE_TEXT =
  "All men have a sweetness in their life. That is what helps them go on. It is towards that they turn when they feel too worn out.";

const scoreItems = [
  { key: "pronunciation_score", label: "Phát âm" },
  { key: "accuracy_score", label: "Chính xác" },
  { key: "fluency_score", label: "Trôi chảy" },
  { key: "completeness_score", label: "Đầy đủ" },
];

const normalizeToken = (value) => (value || "").toLowerCase().replace(/[^a-z']/g, "");

const getWordText = (word) => word?.Word || word?.word || word?.text || "";

const getAssessment = (word) => word?.PronunciationAssessment || word?.pronunciationAssessment || word?.pronunciation_assessment || {};

const getWordScore = (word) => {
  const assessment = getAssessment(word);
  const score = Number(assessment.AccuracyScore ?? assessment.accuracyScore ?? assessment.accuracy_score ?? word?.accuracy);
  return Number.isFinite(score) ? score : null;
};

const getErrorType = (word) => {
  const assessment = getAssessment(word);
  return String(assessment.ErrorType || assessment.errorType || assessment.error_type || "None");
};

const getPhonemeItems = (word) => {
  const phonemes = word?.Phonemes || word?.phonemes || [];
  return Array.isArray(phonemes) ? phonemes : [];
};

const getUnitText = (unit) => unit?.Phoneme || unit?.phoneme || unit?.Text || unit?.text || "";

const getUnitScore = (unit) => {
  const assessment = getAssessment(unit);
  const score = Number(unit?.AccuracyScore ?? unit?.accuracyScore ?? unit?.accuracy_score ?? assessment.AccuracyScore ?? assessment.accuracyScore ?? assessment.accuracy_score);
  return Number.isFinite(score) ? score : null;
};

const getToneFromScore = (score, fallbackTone = "good") => {
  if (score == null) return fallbackTone;
  if (score < 65) return "error";
  if (score < 85) return "warn";
  return "good";
};

const getWordTone = (word) => {
  const errorType = getErrorType(word).toLowerCase();
  const score = getWordScore(word);
  if (errorType && errorType !== "none") return "error";
  return getToneFromScore(score);
};

const toneClasses = {
  good: "text-[#46a302] decoration-[#88DF46]/40",
  warn: "text-amber-600 bg-amber-100/60 decoration-amber-300/70",
  error: "text-rose-600 bg-rose-100/70 decoration-rose-300/80",
  missing: "text-rose-600 bg-rose-100/70 line-through decoration-2 decoration-rose-400",
};

const formatScore = (value) => {
  const score = Number(value);
  return Number.isFinite(score) ? Math.round(score) : "-";
};

const buildLetterUnits = (token, word) => {
  const phonemes = getPhonemeItems(word);
  const letters = Array.from(token);
  const letterIndexes = letters.map((char, index) => (/\p{L}/u.test(char) ? index : null)).filter((index) => index != null);
  const fallbackTone = getWordTone(word);

  if (phonemes.length === 0 || letterIndexes.length === 0) {
    return letters.map((char, index) => ({
      key: `${index}-${char}`,
      text: char,
      tone: /\p{L}/u.test(char) ? fallbackTone : "neutral",
      score: getWordScore(word),
      label: getErrorType(word),
    }));
  }

  return letters.map((char, index) => {
    if (!/\p{L}/u.test(char)) {
      return { key: `${index}-${char}`, text: char, tone: "neutral", score: null, label: "punctuation" };
    }

    const letterPosition = letterIndexes.indexOf(index);
    const phonemeIndex = Math.min(phonemes.length - 1, Math.floor((letterPosition / letterIndexes.length) * phonemes.length));
    const phoneme = phonemes[phonemeIndex];
    const score = getUnitScore(phoneme);
    return {
      key: `${index}-${char}`,
      text: char,
      tone: getToneFromScore(score, fallbackTone),
      score,
      label: getUnitText(phoneme) || getErrorType(word),
    };
  });
};

const buildHighlightedTokens = (referenceText, words) => {
  const azureWords = Array.isArray(words) ? words : [];
  let cursor = 0;

  return referenceText.split(/(\s+)/).map((token, index) => {
    if (/^\s+$/.test(token)) {
      return { key: `${index}-${token}`, text: token, whitespace: true };
    }

    const normalized = normalizeToken(token);
    let match = null;
    for (let wordIndex = cursor; wordIndex < azureWords.length; wordIndex += 1) {
      if (normalizeToken(getWordText(azureWords[wordIndex])) === normalized) {
        match = azureWords[wordIndex];
        cursor = wordIndex + 1;
        break;
      }
    }

    if (!match) {
      return {
        key: `${index}-${token}`,
        text: token,
        tone: "missing",
        score: null,
        errorType: "Omission",
        letters: Array.from(token).map((char, charIndex) => ({
          key: `${charIndex}-${char}`,
          text: char,
          tone: /\p{L}/u.test(char) ? "missing" : "neutral",
          score: null,
          label: "Omission",
        })),
      };
    }

    return {
      key: `${index}-${token}`,
      text: token,
      tone: getWordTone(match),
      score: getWordScore(match),
      errorType: getErrorType(match),
      letters: buildLetterUnits(token, match),
    };
  });
};

const PronunciationAssessmentWidget = () => {
  const [config, setConfig] = useState({ reference_text: DEFAULT_REFERENCE_TEXT, max_recording_seconds: 20 });
  const [isRecording, setIsRecording] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(20);
  const [audioUrl, setAudioUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isScoring, setIsScoring] = useState(false);
  const [selectedTokenKey, setSelectedTokenKey] = useState("");
  const recorderRef = useRef(null);

  useEffect(() => {
    pronunciationAssessmentApi.getConfig().then(setConfig).catch(() => {});
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const highlightedTokens = useMemo(
    () => buildHighlightedTokens(config.reference_text || DEFAULT_REFERENCE_TEXT, result?.words || []),
    [config.reference_text, result?.words],
  );

  const selectedToken = useMemo(
    () => highlightedTokens.find((token) => token.key === selectedTokenKey && !token.whitespace) || null,
    [highlightedTokens, selectedTokenKey],
  );

  useEffect(() => {
    if (!result || selectedTokenKey) return;
    const firstProblem = highlightedTokens.find((token) => !token.whitespace && token.tone !== "good");
    if (firstProblem) {
      setSelectedTokenKey(firstProblem.key);
    }
  }, [highlightedTokens, result, selectedTokenKey]);

  const startRecording = async () => {
    setError("");
    setResult(null);
    setSelectedTokenKey("");
    setAudioUrl("");
    setRemainingSeconds(config.max_recording_seconds || 20);
    try {
      recorderRef.current = await startLandingPronunciationRecorder({
        maxSeconds: config.max_recording_seconds || 20,
        onTick: setRemainingSeconds,
        onStop: async ({ audioBlob, audioBase64 }) => {
          setIsRecording(false);
          const nextAudioUrl = URL.createObjectURL(audioBlob);
          setAudioUrl(nextAudioUrl);
          setIsScoring(true);
          try {
            const score = await pronunciationAssessmentApi.score({ audioBase64 });
            setResult(score);
          } catch (err) {
            setError(err?.message || "Không thể chấm phát âm. Vui lòng thử lại.");
          } finally {
            setIsScoring(false);
          }
        },
      });
      setIsRecording(true);
    } catch (err) {
      setError(err?.message || "Không thể mở microphone.");
    }
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
  };

  const renderHighlightedSentence = () =>
    highlightedTokens.map((token) =>
      token.whitespace ? (
        token.text
      ) : (
        <button
          type="button"
          key={token.key}
          title={token.score == null ? token.errorType : `${token.errorType} · ${Math.round(token.score)}`}
          onClick={() => setSelectedTokenKey(token.key)}
          className={`rounded-lg px-1.5 py-0.5 underline underline-offset-4 transition hover:scale-[1.03] ${toneClasses[token.tone || "good"]} ${selectedTokenKey === token.key ? "ring-2 ring-[#34DBC5]/40" : ""}`}
        >
          {token.text}
        </button>
      ),
    );

  return (
    <div className="rounded-[2.5rem] border border-white/80 bg-white/60 p-5 shadow-2xl shadow-sky-100/80 backdrop-blur-[18px]">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[2rem] border border-white/80 bg-white/78 p-6">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-[#D2E4F8]/70 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-[#2f6f9f]">
            <MicrophoneStage weight="duotone" /> Try it now
          </div>
          <h3 className="text-2xl font-black text-[#20314a]">Đọc câu mẫu và nhận đánh giá tức thì</h3>
          <p className="mt-3 text-sm font-semibold leading-6 text-[#667394]">
            Ghi âm giọng đọc của bạn, nghe lại âm thanh gốc và xem lỗi được highlight trực tiếp trên câu mẫu.
          </p>

          <div className="mt-5 rounded-3xl border border-white/80 bg-[#fffdf4]/80 p-5 text-lg font-black leading-9 text-[#20314a]">
            {result ? renderHighlightedSentence() : config.reference_text || DEFAULT_REFERENCE_TEXT}
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isScoring}
              className="inline-flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-[#88DF46] to-[#34DBC5] px-6 py-4 font-black text-white shadow-lg shadow-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isRecording ? <Stop weight="fill" /> : <MicrophoneStage weight="bold" />}
              {isRecording ? `Dừng (${Math.ceil(remainingSeconds)}s)` : "Bắt đầu ghi âm"}
            </button>
            {audioUrl ? (
              <audio className="h-14 flex-1" src={audioUrl} controls />
            ) : null}
          </div>

          {isScoring ? (
            <div className="mt-4 flex items-center gap-2 text-sm font-bold text-[#2f6f9f]">
              <Waveform className="animate-pulse" weight="bold" /> Hệ thống đang chấm bài...
            </div>
          ) : null}
          {error ? (
            <div className="mt-4 flex items-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-600">
              <WarningCircle weight="fill" /> {error}
            </div>
          ) : null}
        </div>

        <div className="rounded-[2rem] border border-white/80 bg-white/78 p-6">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-black uppercase tracking-[0.2em] text-[#34DBC5]">Kết quả</p>
              <h3 className="mt-1 text-2xl font-black text-[#20314a]">Kết quả luyện đọc</h3>
            </div>
            <div className="flex size-14 items-center justify-center rounded-2xl bg-[#88DF46]/15 text-[#46a302]">
              <CheckCircle size={30} weight="duotone" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {scoreItems.map((item) => (
              <div key={item.key} className="rounded-2xl border border-white/80 bg-white/70 p-4">
                <p className="text-xs font-black uppercase tracking-wider text-[#667394]">{item.label}</p>
                <p className="mt-1 text-3xl font-black text-[#20314a]">{formatScore(result?.[item.key])}</p>
              </div>
            ))}
          </div>

          {selectedToken ? (
            <div className="mt-4 rounded-3xl border border-white/80 bg-white/75 p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-sm font-black uppercase tracking-[0.18em] text-[#667394]">Chi tiết âm/chữ</p>
                <span className={`rounded-full px-3 py-1 text-xs font-black ${toneClasses[selectedToken.tone || "good"]}`}>
                  {selectedToken.score == null ? selectedToken.errorType : `${Math.round(selectedToken.score)}/100`}
                </span>
              </div>
              <div className="flex flex-wrap items-end gap-1.5">
                {selectedToken.letters?.map((letter) => (
                  <span key={letter.key} className="inline-flex flex-col items-center gap-1">
                    <span
                      title={letter.score == null ? letter.label : `${letter.label} · ${Math.round(letter.score)}`}
                      className={letter.tone === "neutral" ? "px-1 text-xl font-black text-[#20314a]" : `rounded-lg px-1.5 py-1 text-xl font-black ${toneClasses[letter.tone]}`}
                    >
                      {letter.text}
                    </span>
                    {letter.tone !== "neutral" ? (
                      <span className="text-[10px] font-black uppercase tracking-wide text-[#667394]">{letter.label || "âm"}</span>
                    ) : null}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-3xl border border-white/80 bg-[#f8fbff]/80 p-5 text-sm font-bold leading-7 text-[#667394]">
              Sau khi chấm, câu gốc bên trái sẽ được tô màu theo từng từ. Nhấn vào từng từ để xem chi tiết âm/chữ tại đây.
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2 text-xs font-black">
            <span className="rounded-full border border-[#88DF46]/30 bg-[#88DF46]/15 px-3 py-1 text-[#46a302]">Tốt</span>
            <span className="rounded-full border border-amber-300/50 bg-amber-100/70 px-3 py-1 text-amber-700">Cần luyện</span>
            <span className="rounded-full border border-rose-300/60 bg-rose-100/80 px-3 py-1 text-rose-700">Sai/thiếu</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PronunciationAssessmentWidget;
