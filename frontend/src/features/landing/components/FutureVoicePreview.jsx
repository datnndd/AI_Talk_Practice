import { useEffect, useRef, useState } from "react";
import { Microphone, Sparkle, Stop, Waveform } from "@phosphor-icons/react";
import { futureVoiceApi } from "@/features/landing/api/futureVoiceApi";
import { createFutureVoiceFingerprint } from "@/features/landing/utils/futureVoiceFingerprint";
import { startFutureVoiceRecorder } from "@/features/landing/utils/futureVoiceRecorder";

const TRIAL_STORAGE_KEY = "future_voice_trial_used";

const DEFAULT_CONFIG = {
  transcript:
    "Every day I practice speaking with confidence. I listen carefully, pronounce clearly, and keep going even when a sentence feels difficult.",
  max_recording_seconds: 20,
  max_audio_bytes: 10485760,
  min_sample_rate: 24000,
};

const formatSeconds = (value) => `${Math.max(0, Math.ceil(value))}s`;

const FutureVoicePreview = () => {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [status, setStatus] = useState(() =>
    window.sessionStorage.getItem(TRIAL_STORAGE_KEY) === "1" ? "used" : "idle",
  );
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState("");
  const [originalUrl, setOriginalUrl] = useState("");
  const [futureUrl, setFutureUrl] = useState("");
  const recorderRef = useRef(null);
  const originalUrlRef = useRef("");

  useEffect(() => {
    let mounted = true;
    futureVoiceApi
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
      if (originalUrlRef.current) {
        URL.revokeObjectURL(originalUrlRef.current);
      }
    },
    [],
  );

  const clearAudio = () => {
    if (originalUrlRef.current) {
      URL.revokeObjectURL(originalUrlRef.current);
      originalUrlRef.current = "";
    }
    setOriginalUrl("");
    setFutureUrl("");
  };

  const handleStopPayload = async ({ blob, audioBase64 }) => {
    const objectUrl = URL.createObjectURL(blob);
    if (originalUrlRef.current) {
      URL.revokeObjectURL(originalUrlRef.current);
    }
    originalUrlRef.current = objectUrl;
    setOriginalUrl(objectUrl);
    setStatus("processing");
    setError("");

    try {
      const fingerprint = await createFutureVoiceFingerprint();
      const response = await futureVoiceApi.generate({ audioBase64, fingerprint });
      setFutureUrl(response.future_audio_base64);
      window.sessionStorage.setItem(TRIAL_STORAGE_KEY, "1");
      setStatus("success");
    } catch (err) {
      const responseStatus = err?.response?.status;
      if (responseStatus === 409) {
        window.sessionStorage.setItem(TRIAL_STORAGE_KEY, "1");
        setStatus("used");
        setError("This browser has already used the future voice demo.");
        return;
      }
      setStatus("idle");
      setError(err?.message || "Could not generate your future voice. Please try again.");
    }
  };

  const startRecording = async () => {
    clearAudio();
    setError("");
    setElapsed(0);

    try {
      recorderRef.current = await startFutureVoiceRecorder({
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
  const isUsed = status === "used";
  const canRecord = !isRecording && !isProcessing && !isUsed;
  const remainingSeconds = config.max_recording_seconds - elapsed;

  return (
    <section className="border-y-2 border-brand-gray bg-[#f7fbff] px-6 py-14 lg:px-12">
      <div className="mx-auto grid max-w-7xl items-start gap-8 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-xs font-black uppercase text-brand-blue shadow-sm">
            <Sparkle size={16} weight="fill" />
            Future voice preview
          </div>
          <h2 className="max-w-xl text-3xl font-black leading-tight text-brand-text lg:text-4xl">
            Hear the voice you are practicing toward.
          </h2>
          <p className="max-w-xl text-base font-semibold leading-7 text-brand-muted-text">
            Read the script once. The app clones your current voice for this session and generates the same line as a polished preview.
          </p>
        </div>

        <div className="space-y-5 rounded-lg border-2 border-brand-gray bg-white p-5 shadow-[0_6px_0_#e5e5e5]">
          <div className="rounded-lg bg-brand-green/10 p-4">
            <p className="text-xs font-black uppercase text-brand-green-dark">Script</p>
            <p className="mt-2 text-lg font-black leading-8 text-brand-text">{config.transcript}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!canRecord && !isRecording}
              className="inline-flex min-h-[52px] items-center justify-center gap-2 rounded-lg border-2 border-b-4 border-brand-blue-dark bg-brand-blue px-5 text-sm font-black uppercase text-white transition-all active:border-b-2 active:translate-y-[2px] disabled:cursor-not-allowed disabled:border-brand-gray disabled:bg-brand-gray disabled:text-brand-muted-text"
            >
              {isRecording ? <Stop size={20} weight="fill" /> : <Microphone size={20} weight="fill" />}
              {isRecording ? "Stop recording" : "Record script"}
            </button>

            <div className="inline-flex min-h-[52px] items-center gap-2 rounded-lg border-2 border-brand-gray px-4 text-sm font-black text-brand-text">
              <Waveform size={18} weight="bold" />
              {isRecording ? formatSeconds(remainingSeconds) : `${config.max_recording_seconds}s max`}
            </div>
          </div>

          {isProcessing && (
            <div className="rounded-lg border border-brand-blue/20 bg-brand-blue/10 px-4 py-3 text-sm font-bold text-brand-blue-dark">
              Generating your future voice preview...
            </div>
          )}

          {isUsed && (
            <div className="rounded-lg border border-brand-orange/30 bg-brand-orange/10 px-4 py-3 text-sm font-bold text-brand-orange-dark">
              This browser has already used the one-time future voice preview.
            </div>
          )}

          {error && <p className="text-sm font-bold text-brand-red">{error}</p>}

          {(originalUrl || futureUrl) && (
            <div className="grid gap-4 md:grid-cols-2">
              {originalUrl && (
                <div className="rounded-lg border-2 border-brand-gray p-4">
                  <p className="text-xs font-black uppercase text-brand-muted-text">Original recording</p>
                  <audio controls src={originalUrl} className="mt-3 w-full" />
                </div>
              )}

              {futureUrl && (
                <div className="rounded-lg border-2 border-brand-green bg-brand-green/5 p-4">
                  <p className="text-xs font-black uppercase text-brand-green-dark">Improved / Future voice</p>
                  <audio controls src={futureUrl} className="mt-3 w-full" />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default FutureVoicePreview;

