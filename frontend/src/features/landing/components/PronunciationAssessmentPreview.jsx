import { useEffect, useRef, useState } from "react";
import { CheckCircle, Microphone, Sparkle, Stop, Waveform } from "@phosphor-icons/react";
import { pronunciationAssessmentApi } from "@/features/landing/api/pronunciationAssessmentApi";
import { startLandingPronunciationRecorder } from "@/features/landing/utils/landingPronunciationRecorder";

const DEFAULT_CONFIG = {
  reference_text:
    "Every day I practice speaking with confidence. I listen carefully, pronounce clearly, and keep going even when a sentence feels difficult.",
  max_recording_seconds: 20,
  max_audio_bytes: 10485760,
  min_sample_rate: 16000,
};

const formatSeconds = (value) => `${Math.max(0, Math.ceil(value))}s`;

const scoreItems = [
  { key: "pronunciation_score", label: "Pronunciation" },
  { key: "accuracy_score", label: "Accuracy" },
  { key: "fluency_score", label: "Fluency" },
  { key: "completeness_score", label: "Completeness" },
];

const formatScore = (value) => {
  const score = Number(value);
  return Number.isFinite(score) ? Math.round(score) : "-";
};

const pickNumber = (...values) => {
  for (const value of values) {
    const number = Number(value);
    if (Number.isFinite(number)) {
      return number;
    }
  }
  return null;
};

const parseAzureRaw = (raw) => {
  if (!raw) {
    return null;
  }
  if (typeof raw === "object") {
    return raw;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

const normalizeAzureWord = (word) => {
  const assessment = word?.PronunciationAssessment || word?.pronunciationAssessment || word?.pronunciation_assessment || {};
  return {
    text: word?.Word || word?.word || "",
    accuracy: pickNumber(assessment.AccuracyScore, assessment.accuracyScore, assessment.accuracy_score),
    errorType: assessment.ErrorType || assessment.errorType || assessment.error_type || "",
    phonemes: word?.Phonemes || word?.phonemes || [],
    syllables: word?.Syllables || word?.syllables || [],
  };
};

const extractUnitScore = (unit) => {
  const assessment = unit?.PronunciationAssessment || unit?.pronunciationAssessment || unit?.pronunciation_assessment || {};
  return pickNumber(unit?.AccuracyScore, unit?.accuracyScore, unit?.accuracy_score, assessment.AccuracyScore, assessment.accuracyScore);
};

const extractUnitText = (unit) => unit?.Phoneme || unit?.phoneme || unit?.Syllable || unit?.syllable || unit?.Text || unit?.text || "";

const getVisibleUnits = (word) => (word.phonemes.length > 0 ? word.phonemes : word.syllables);

const getWeakUnits = (word) =>
  getVisibleUnits(word)
    .map((unit) => ({
      text: extractUnitText(unit) || "unit",
      score: extractUnitScore(unit),
    }))
    .filter((unit) => unit.score != null)
    .sort((a, b) => a.score - b.score)
    .slice(0, 3);

const getErrorLabel = (errorType) => {
  const normalized = (errorType || "").toLowerCase();
  if (!normalized || normalized === "none") {
    return "No Azure error";
  }
  if (normalized === "mispronunciation") {
    return "Mispronounced";
  }
  if (normalized === "omission") {
    return "Missing word";
  }
  if (normalized === "insertion") {
    return "Extra word";
  }
  return errorType;
};

const getWordStatus = (word) => {
  const errorType = (word.errorType || "").toLowerCase();
  if (errorType && errorType !== "none") {
    return "red";
  }
  if (word.accuracy != null && word.accuracy < 65) {
    return "red";
  }
  if (word.accuracy != null && word.accuracy < 85) {
    return "yellow";
  }
  return "green";
};

const wordToneClasses = {
  green: {
    chip: "border-brand-green/40 bg-brand-green/15 text-brand-green-dark hover:bg-brand-green/20 focus-visible:ring-brand-green/30",
    dot: "bg-brand-green",
    tooltip: "border-brand-green/30",
    label: "Good",
  },
  yellow: {
    chip: "border-brand-gold/60 bg-brand-gold/20 text-[#8a5c00] hover:bg-brand-gold/30 focus-visible:ring-brand-gold/30",
    dot: "bg-brand-gold",
    tooltip: "border-brand-gold/50",
    label: "Practice",
  },
  red: {
    chip: "border-brand-red/40 bg-brand-red/10 text-brand-red hover:bg-brand-red/15 focus-visible:ring-brand-red/30",
    dot: "bg-brand-red",
    tooltip: "border-brand-red/40",
    label: "Fix",
  },
};

const getWordTooltipLines = (word) => {
  const status = getWordStatus(word);
  const weakUnits = getWeakUnits(word);
  const lines = [`Accuracy: ${formatScore(word.accuracy)}`, `Result: ${getErrorLabel(word.errorType)}`];

  if (weakUnits.length > 0 && status !== "green") {
    lines.push(`Weakest: ${weakUnits.map((unit) => `${unit.text} ${formatScore(unit.score)}`).join(", ")}`);
  }

  if (status === "green") {
    lines.push("Pronounced clearly.");
  } else if ((word.errorType || "").toLowerCase() === "omission") {
    lines.push("Azure did not hear this word clearly.");
  } else if ((word.errorType || "").toLowerCase() === "insertion") {
    lines.push("Azure detected an extra word.");
  } else if ((word.errorType || "").toLowerCase() === "mispronunciation") {
    lines.push("Focus on the highlighted sounds.");
  } else {
    lines.push("Repeat this word more slowly.");
  }

  return lines;
};

const PronunciationAssessmentPreview = () => {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [status, setStatus] = useState("idle");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [recordingUrl, setRecordingUrl] = useState("");
  const [assessment, setAssessment] = useState(null);
  const recorderRef = useRef(null);
  const recordingUrlRef = useRef("");

  useEffect(() => {
    let mounted = true;
    pronunciationAssessmentApi
      .getConfig()
      .then((response) => {
        if (mounted) {
          setConfig(response);
        }
      })
      .catch(() => {
        if (mounted) {
          setConfig(DEFAULT_CONFIG);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(
    () => () => {
      if (recordingUrlRef.current) {
        URL.revokeObjectURL(recordingUrlRef.current);
      }
    },
    [],
  );

  const clearResult = () => {
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
      recordingUrlRef.current = "";
    }
    setRecordingUrl("");
    setAssessment(null);
  };

  const handleStopPayload = async ({ blob, audioBase64 }) => {
    const objectUrl = URL.createObjectURL(blob);
    if (recordingUrlRef.current) {
      URL.revokeObjectURL(recordingUrlRef.current);
    }
    recordingUrlRef.current = objectUrl;
    setRecordingUrl(objectUrl);
    setStatus("processing");
    setError("");

    try {
      const response = await pronunciationAssessmentApi.score({ audioBase64 });
      setAssessment(response);
      setStatus("success");
    } catch (err) {
      setStatus("idle");
      setError(err?.response?.data?.detail || err?.message || "Could not score your pronunciation. Please try again.");
    }
  };

  const startRecording = async () => {
    clearResult();
    setError("");
    setElapsed(0);

    try {
      recorderRef.current = await startLandingPronunciationRecorder({
        maxSeconds: config.max_recording_seconds,
        minSampleRate: config.min_sample_rate,
        onTick: setElapsed,
        onStop: handleStopPayload,
      });
      setStatus("recording");
    } catch (err) {
      setStatus("idle");
      setError(err?.message || "Could not open the microphone.");
    }
  };

  const stopRecording = async () => {
    await recorderRef.current?.stop();
    recorderRef.current = null;
  };

  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  const canRecord = !isRecording && !isProcessing;
  const remainingSeconds = config.max_recording_seconds - elapsed;
  const azureRaw = parseAzureRaw(assessment?.raw);
  const bestResult = azureRaw?.NBest?.[0] || null;
  const recognizedText = bestResult?.Display || azureRaw?.DisplayText || azureRaw?.Text || "";
  const wordDetails = (assessment?.words || []).map(normalizeAzureWord).filter((word) => word.text);
  const missedOrInsertedWords = wordDetails.filter((word) => {
    const errorType = word.errorType.toLowerCase();
    return errorType && errorType !== "none";
  });

  return (
    <section className="border-y-2 border-brand-gray bg-[#f7fbff] px-6 py-14 lg:px-12">
      <div className="mx-auto grid max-w-7xl items-start gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-xs font-black uppercase text-brand-blue shadow-sm">
            <Sparkle size={16} weight="fill" />
            Pronunciation check
          </div>
          <h2 className="max-w-xl text-3xl font-black leading-tight text-brand-text lg:text-4xl">
            Get an instant pronunciation score.
          </h2>
          <p className="max-w-xl text-base font-semibold leading-7 text-brand-muted-text">
            Read the fixed line once. Azure Speech scores pronunciation, accuracy, fluency, and completeness.
          </p>
        </div>

        <div className="space-y-5 rounded-lg border-2 border-brand-gray bg-white p-5 shadow-[0_6px_0_#e5e5e5]">
          <div className="rounded-lg bg-brand-green/10 p-4">
            <p className="text-xs font-black uppercase text-brand-green-dark">Read aloud</p>
            <p className="mt-2 text-lg font-black leading-8 text-brand-text">{config.reference_text}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!canRecord && !isRecording}
              className="inline-flex min-h-[52px] items-center justify-center gap-2 rounded-lg border-2 border-b-4 border-brand-blue-dark bg-brand-blue px-5 text-sm font-black uppercase text-white transition-all active:border-b-2 active:translate-y-[2px] disabled:cursor-not-allowed disabled:border-brand-gray disabled:bg-brand-gray disabled:text-brand-muted-text"
            >
              {isRecording ? <Stop size={20} weight="fill" /> : <Microphone size={20} weight="fill" />}
              {isRecording ? "Stop recording" : "Record and score"}
            </button>

            <div className="inline-flex min-h-[52px] items-center gap-2 rounded-lg border-2 border-brand-gray px-4 text-sm font-black text-brand-text">
              <Waveform size={18} weight="bold" />
              {isRecording ? formatSeconds(remainingSeconds) : `${config.max_recording_seconds}s max`}
            </div>
          </div>

          {isProcessing && (
            <div className="rounded-lg border border-brand-blue/20 bg-brand-blue/10 px-4 py-3 text-sm font-bold text-brand-blue-dark">
              Scoring your pronunciation...
            </div>
          )}

          {error && <p className="text-sm font-bold text-brand-red">{error}</p>}

          {(recordingUrl || assessment) && (
            <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
              {recordingUrl && (
                <div className="rounded-lg border-2 border-brand-gray p-4">
                  <p className="text-xs font-black uppercase text-brand-muted-text">Your recording</p>
                  <audio controls src={recordingUrl} className="mt-3 w-full" />
                </div>
              )}

              {assessment && (
                <div className="rounded-lg border-2 border-brand-green bg-brand-green/5 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-black uppercase text-brand-green-dark">Azure score</p>
                    <div className="inline-flex items-center gap-1 text-sm font-black text-brand-green-dark">
                      <CheckCircle size={18} weight="fill" />
                      {Math.round(assessment.score || 0)}
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    {scoreItems.map((item) => (
                      <div key={item.key} className="rounded-lg border border-brand-green/20 bg-white px-3 py-2">
                        <p className="text-[11px] font-black uppercase text-brand-muted-text">{item.label}</p>
                        <p className="mt-1 text-xl font-black text-brand-text">{formatScore(assessment[item.key])}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {assessment && (
            <div className="space-y-4 rounded-lg border-2 border-brand-gray bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase text-brand-blue">Azure details</p>
                  <p className="mt-1 text-sm font-bold text-brand-muted-text">
                    Word-level assessment returned by Azure Speech.
                  </p>
                </div>
                <span className="rounded-lg border border-brand-gray px-3 py-1 text-xs font-black uppercase text-brand-muted-text">
                  {assessment.source || "azure"}
                </span>
              </div>

              {recognizedText && (
                <div className="rounded-lg bg-[#f7fbff] p-3">
                  <p className="text-[11px] font-black uppercase text-brand-muted-text">Recognized text</p>
                  <p className="mt-1 text-sm font-black leading-6 text-brand-text">{recognizedText}</p>
                </div>
              )}

              {missedOrInsertedWords.length > 0 && (
                <div className="rounded-lg border border-brand-red/20 bg-brand-red/5 p-3">
                  <p className="text-[11px] font-black uppercase text-brand-red">Needs attention</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {missedOrInsertedWords.map((word, index) => (
                      <span
                        key={`${word.text}-${index}`}
                        className="rounded-lg border border-brand-red/20 bg-white px-2 py-1 text-xs font-black text-brand-red"
                      >
                        {word.text} - {word.errorType}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {wordDetails.length > 0 && (
                <div className="rounded-lg border border-brand-gray p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-[11px] font-black uppercase text-brand-muted-text">Word color map</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(wordToneClasses).map(([status, tone]) => (
                        <span key={status} className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-brand-muted-text">
                          <span className={`h-2.5 w-2.5 rounded-full ${tone.dot}`} />
                          {tone.label}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {wordDetails.map((word, index) => {
                      const status = getWordStatus(word);
                      const tone = wordToneClasses[status];
                      const tooltipLines = getWordTooltipLines(word);
                      return (
                        <span key={`${word.text}-${index}`} className="group relative inline-flex">
                          <button
                            type="button"
                            className={`inline-flex min-h-9 items-center gap-2 rounded-lg border px-3 text-sm font-black transition-colors focus-visible:ring-2 ${tone.chip}`}
                            aria-label={`${word.text}. ${tooltipLines.join(". ")}`}
                          >
                            <span className={`h-2.5 w-2.5 rounded-full ${tone.dot}`} />
                            {word.text}
                            <span className="text-[11px] opacity-80">{formatScore(word.accuracy)}</span>
                          </button>
                          <div
                            role="tooltip"
                            className={`pointer-events-none absolute left-1/2 top-full z-30 mt-2 hidden w-64 -translate-x-1/2 rounded-lg border bg-white p-3 text-left shadow-[0_8px_24px_rgba(0,0,0,0.12)] group-hover:block group-focus-within:block ${tone.tooltip}`}
                          >
                            <p className="text-sm font-black text-brand-text">{word.text}</p>
                            <div className="mt-2 space-y-1">
                              {tooltipLines.map((line) => (
                                <p key={line} className="text-xs font-bold leading-5 text-brand-muted-text">
                                  {line}
                                </p>
                              ))}
                            </div>
                          </div>
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {assessment.raw && (
                <details className="rounded-lg border border-brand-gray bg-[#f7fbff] p-3">
                  <summary className="cursor-pointer text-xs font-black uppercase text-brand-muted-text">
                    Raw Azure JSON
                  </summary>
                  <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs font-bold leading-5 text-brand-text">
                    {azureRaw ? JSON.stringify(azureRaw, null, 2) : assessment.raw}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default PronunciationAssessmentPreview;
