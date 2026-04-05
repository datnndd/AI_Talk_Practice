import { useEffect, useEffectEvent, useRef, useState } from "react";
import { ArrowLeft, WarningCircle } from "@phosphor-icons/react";
import { useNavigate, useParams } from "react-router-dom";
import ChatWindow from "@/features/practice/components/ChatWindow";
import MetricsSidebar from "@/features/practice/components/MetricsSidebar";
import TypewriterInput from "@/features/practice/components/TypewriterInput";
import {
  arrayBufferToBase64,
  base64ToArrayBuffer,
  createConversationWebSocketUrl,
  pcm16ToFloat32,
  resampleFloat32,
} from "@/features/practice/services/realtimeAudio";
import { practiceApi } from "@/features/practice/api/practiceApi";

const DEFAULT_LANGUAGE = "en";
const DEFAULT_VOICE = "Cherry";

const PracticeSession = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const scenarioId = Number(id);

  const [scenario, setScenario] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const [messages, setMessages] = useState([]);
  const [partialTranscript, setPartialTranscript] = useState("");
  const [assistantDraft, setAssistantDraft] = useState("");
  const [connectionState, setConnectionState] = useState("connecting");
  const [recordingState, setRecordingState] = useState("idle");
  const [sessionId, setSessionId] = useState(null);
  const [sessionError, setSessionError] = useState("");
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [reconnectRequest, setReconnectRequest] = useState(0);

  const socketRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const mediaSourceRef = useRef(null);
  const processorRef = useRef(null);
  const silentGainRef = useRef(null);
  const captureActiveRef = useRef(false);
  const playbackCursorRef = useRef(0);
  const sessionStartAtRef = useRef(null);
  const messageIdRef = useRef(0);
  const isCleaningUpRef = useRef(false);

  const buildMessage = (role, content) => {
    messageIdRef.current += 1;
    return { id: `${role}-${messageIdRef.current}`, role, content };
  };

  const ensureAudioContext = async () => {
    const BrowserAudioContext = window.AudioContext || window.webkitAudioContext;
    if (!BrowserAudioContext) {
      throw new Error("This browser does not support Web Audio.");
    }

    if (!audioContextRef.current || audioContextRef.current.state === "closed") {
      audioContextRef.current = new BrowserAudioContext();
      playbackCursorRef.current = 0;
    }

    if (audioContextRef.current.state === "suspended") {
      await audioContextRef.current.resume();
    }

    return audioContextRef.current;
  };

  const teardownAudioPipeline = async () => {
    captureActiveRef.current = false;

    processorRef.current?.disconnect();
    mediaSourceRef.current?.disconnect();
    silentGainRef.current?.disconnect();

    processorRef.current = null;
    mediaSourceRef.current = null;
    silentGainRef.current = null;

    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      await audioContextRef.current.close();
    }
    audioContextRef.current = null;
    playbackCursorRef.current = 0;
  };

  const closeSocket = (intentional = false) => {
    captureActiveRef.current = false;
    isCleaningUpRef.current = intentional;

    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  const ensureCapturePipeline = async () => {
    if (mediaStreamRef.current && processorRef.current) {
      return;
    }

    const audioContext = await ensureAudioContext();
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    const silentGain = audioContext.createGain();
    silentGain.gain.value = 0;

    processor.onaudioprocess = (event) => {
      if (!captureActiveRef.current || socketRef.current?.readyState !== WebSocket.OPEN) {
        return;
      }

      const input = event.inputBuffer.getChannelData(0);
      const resampled = resampleFloat32(input, audioContext.sampleRate, 16000);
      const pcmBuffer = new Int16Array(resampled.length);

      for (let index = 0; index < resampled.length; index += 1) {
        const sample = Math.max(-1, Math.min(1, resampled[index]));
        pcmBuffer[index] = sample < 0 ? sample * 32768 : sample * 32767;
      }

      socketRef.current.send(JSON.stringify({
        type: "audio_chunk",
        data: arrayBufferToBase64(pcmBuffer.buffer),
      }));
    };

    source.connect(processor);
    processor.connect(silentGain);
    silentGain.connect(audioContext.destination);

    mediaStreamRef.current = stream;
    mediaSourceRef.current = source;
    processorRef.current = processor;
    silentGainRef.current = silentGain;
  };

  const queuePlaybackChunk = async (audioBase64) => {
    const audioContext = await ensureAudioContext();
    const float32 = pcm16ToFloat32(base64ToArrayBuffer(audioBase64));
    const buffer = audioContext.createBuffer(1, float32.length, 24000);
    buffer.copyToChannel(float32, 0);

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);

    const startAt = Math.max(audioContext.currentTime, playbackCursorRef.current);
    source.start(startAt);
    playbackCursorRef.current = startAt + buffer.duration;
  };

  const handleSocketMessage = useEffectEvent(async (event) => {
    let payload;

    try {
      payload = JSON.parse(event.data);
    } catch {
      return;
    }

    switch (payload.type) {
      case "session_started":
        sessionStartAtRef.current = Date.now();
        setSessionId(payload.session_id);
        setConnectionState("ready");
        setRecordingState("idle");
        setSessionError("");
        setDurationSeconds(0);
        break;
      case "recording_started":
        setRecordingState("recording");
        setSessionError("");
        break;
      case "transcript_partial":
        setPartialTranscript(payload.text || "");
        break;
      case "transcript_final":
        if (payload.text) {
          setMessages((current) => [...current, buildMessage("user", payload.text)]);
        }
        setPartialTranscript("");
        setRecordingState("processing");
        break;
      case "llm_chunk":
        setAssistantDraft((current) => `${current}${payload.text || ""}`);
        setRecordingState("assistant");
        break;
      case "llm_done":
        setAssistantDraft("");
        if (payload.text) {
          setMessages((current) => [...current, buildMessage("assistant", payload.text)]);
        }
        setRecordingState("assistant");
        break;
      case "audio_chunk":
        setRecordingState("assistant");
        await queuePlaybackChunk(payload.data);
        break;
      case "audio_done":
        setRecordingState("idle");
        break;
      case "error":
        setSessionError(payload.message || "Unexpected realtime error.");
        setRecordingState("idle");
        if (connectionState !== "ready") {
          setConnectionState("error");
        }
        break;
      default:
        break;
    }
  });

  const connectSocket = useEffectEvent((resetConversation = true) => {
    const token = window.localStorage.getItem("access_token");
    if (!token) {
      setSessionError("Missing access token. Please sign in again.");
      setConnectionState("error");
      return;
    }

    closeSocket(true);

    if (resetConversation) {
      setMessages([]);
      setAssistantDraft("");
      setPartialTranscript("");
      setSessionId(null);
      setDurationSeconds(0);
      sessionStartAtRef.current = null;
    }

    setConnectionState("connecting");
    setRecordingState("idle");
    setSessionError("");
    isCleaningUpRef.current = false;

    const socket = new WebSocket(createConversationWebSocketUrl(practiceApi.getApiBaseUrl()));
    socketRef.current = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({
        type: "session_start",
        token,
        scenario_id: scenarioId,
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
      }));
    };

    socket.onmessage = (event) => {
      void handleSocketMessage(event);
    };

    socket.onerror = () => {
      setConnectionState("error");
      setSessionError("Unable to reach the realtime conversation service.");
    };

    socket.onclose = () => {
      socketRef.current = null;
      captureActiveRef.current = false;

      if (isCleaningUpRef.current) {
        isCleaningUpRef.current = false;
        return;
      }

      setConnectionState((current) => (current === "error" ? current : "closed"));
      setRecordingState("idle");
    };
  });

  useEffect(() => {
    if (!Number.isFinite(scenarioId)) {
      setScenarioError("Invalid scenario id.");
      setIsLoading(false);
      return undefined;
    }

    let isMounted = true;

    const fetchScenario = async () => {
      setIsLoading(true);
      setScenarioError("");

      try {
        const response = await practiceApi.getScenario(scenarioId);
        if (!isMounted) {
          return;
        }
        setScenario(response);
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setScenarioError(error?.response?.data?.detail || "Failed to load the selected scenario.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void fetchScenario();

    return () => {
      isMounted = false;
    };
  }, [scenarioId]);

  useEffect(() => {
    if (!scenario || scenarioError) {
      return undefined;
    }

    connectSocket(true);

    return () => {
      closeSocket(true);
      void teardownAudioPipeline();
    };
  }, [scenario, scenarioError]);

  useEffect(() => {
    if (reconnectRequest === 0) {
      return;
    }

    connectSocket(true);
  }, [reconnectRequest]);

  useEffect(() => {
    if (!sessionStartAtRef.current) {
      return undefined;
    }

    const interval = window.setInterval(() => {
      setDurationSeconds(Math.max(0, Math.floor((Date.now() - sessionStartAtRef.current) / 1000)));
    }, 1000);

    return () => window.clearInterval(interval);
  }, [sessionId]);

  const handleToggleRecording = async () => {
    if (connectionState !== "ready" || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setSessionError("The conversation socket is not ready yet.");
      return;
    }

    if (recordingState === "recording") {
      captureActiveRef.current = false;
      socketRef.current.send(JSON.stringify({ type: "stop_recording" }));
      setRecordingState("processing");
      return;
    }

    try {
      await ensureCapturePipeline();
      await ensureAudioContext();
      setAssistantDraft("");
      setPartialTranscript("");
      setSessionError("");
      captureActiveRef.current = true;
      socketRef.current.send(JSON.stringify({
        type: "start_recording",
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
      }));
      setRecordingState("recording");
    } catch (error) {
      captureActiveRef.current = false;
      setSessionError(error?.message || "Microphone access failed.");
      setRecordingState("idle");
    }
  };

  const handleReconnect = () => {
    setReconnectRequest((current) => current + 1);
  };

  const handleEndSession = async () => {
    closeSocket(true);
    await teardownAudioPipeline();
    navigate("/topics");
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-gradient-to-br from-blue-50 via-white to-cyan-50">
        <div className="flex flex-col items-center gap-4 rounded-4xl border border-white/40 bg-white/70 px-8 py-10 shadow-xl backdrop-blur-xl">
          <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
          <p className="text-sm font-semibold text-zinc-500">Loading practice session...</p>
        </div>
      </div>
    );
  }

  if (scenarioError || !scenario) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-gradient-to-br from-blue-50 via-white to-cyan-50 p-6">
        <div className="max-w-lg rounded-4xl border border-rose-100 bg-white p-8 shadow-xl">
          <div className="flex items-start gap-3 text-rose-600">
            <WarningCircle size={24} weight="fill" className="mt-0.5 shrink-0" />
            <div>
              <h1 className="text-xl font-black text-zinc-950 font-display">Session unavailable</h1>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">
                {scenarioError || "This scenario could not be loaded."}
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate("/topics")}
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-zinc-950 px-5 py-3 text-sm font-bold text-white"
          >
            <ArrowLeft size={18} weight="bold" />
            Back to topics
          </button>
        </div>
      </div>
    );
  }

  const isMicDisabled = connectionState !== "ready" || recordingState === "processing" || recordingState === "assistant";

  return (
    <div className="min-h-[100dvh] bg-[radial-gradient(circle_at_top_left,_rgba(49,130,237,0.18),_transparent_30%),linear-gradient(135deg,_#eff6ff_0%,_#ffffff_48%,_#ecfeff_100%)] p-6 font-sans antialiased md:p-10">
      <main className="mx-auto grid h-[calc(100dvh-48px)] w-full max-w-[1440px] grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="relative flex h-full flex-col gap-6 lg:col-span-8">
          <ChatWindow
            scenario={scenario}
            messages={messages}
            partialTranscript={partialTranscript}
            assistantDraft={assistantDraft}
            connectionState={connectionState}
            recordingState={recordingState}
          />
          <TypewriterInput
            partialTranscript={partialTranscript}
            recordingState={recordingState}
            connectionState={connectionState}
            onToggleRecording={handleToggleRecording}
            onReconnect={handleReconnect}
            disabled={isMicDisabled}
            error={sessionError}
          />
        </div>

        <MetricsSidebar
          scenario={scenario}
          durationSeconds={durationSeconds}
          sessionId={sessionId}
          turnCount={messages.filter((message) => message.role === "user").length}
          connectionState={connectionState}
          recordingState={recordingState}
          onReconnect={handleReconnect}
          onEndSession={handleEndSession}
        />
      </main>
    </div>
  );
};

export default PracticeSession;
