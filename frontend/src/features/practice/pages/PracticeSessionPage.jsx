import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, WarningCircle } from "@phosphor-icons/react";
import { useNavigate, useParams } from "react-router-dom";
import ChatWindow from "@/features/practice/components/ChatWindow";
import CurrentQuestionCard from "@/features/practice/components/CurrentQuestionCard";
import MetricsSidebar from "@/features/practice/components/MetricsSidebar";
import TypewriterInput from "@/features/practice/components/TypewriterInput";
import { SessionHeader } from "@/shared/components/navigation";
import {
  arrayBufferToBase64,
  base64ToArrayBuffer,
  createConversationWebSocketUrl,
  pcm16ToFloat32,
  resampleFloat32,
} from "@/features/practice/services/realtimeAudio";
import { practiceApi } from "@/features/practice/api/practiceApi";
import { buildConversationGuidance } from "@/features/practice/utils/conversationGuidance";
import {
  appendUniqueMessage,
  getLessonCompletionTone,
} from "@/features/practice/utils/lessonState";

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
  const [connectionState, setConnectionState] = useState("closed");
  const [recordingState, setRecordingState] = useState("idle");
  const [sessionId, setSessionId] = useState(null);
  const [sessionError, setSessionError] = useState("");
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [reconnectRequest, setReconnectRequest] = useState(0);
  const [lessonState, setLessonState] = useState(null);
  const [lessonHint, setLessonHint] = useState(null);
  const [isHintLoading, setIsHintLoading] = useState(false);

  const socketRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const mediaSourceRef = useRef(null);
  const processorRef = useRef(null);
  const silentGainRef = useRef(null);
  const captureActiveRef = useRef(false);
  const playbackCursorRef = useRef(0);
  const playbackSourcesRef = useRef(new Set());
  const sessionStartAtRef = useRef(null);
  const messageIdRef = useRef(0);
  const isCleaningUpRef = useRef(false);
  const autoStartRecordingRef = useRef(false);
  const suppressAssistantStreamRef = useRef(false);
  const assistantDraftRef = useRef("");
  const lessonStateRef = useRef(null);

  const buildMessage = (role, content) => {
    messageIdRef.current += 1;
    return { id: `${role}-${messageIdRef.current}`, role, content };
  };

  const ensureAudioContext = useCallback(async () => {
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
  }, []);

  const teardownAudioPipeline = async () => {
    captureActiveRef.current = false;
    suppressAssistantStreamRef.current = false;

    processorRef.current?.disconnect();
    mediaSourceRef.current?.disconnect();
    silentGainRef.current?.disconnect();

    processorRef.current = null;
    mediaSourceRef.current = null;
    silentGainRef.current = null;

    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;

    playbackSourcesRef.current.forEach((source) => {
      try {
        source.onended = null;
        source.stop(0);
      } catch {
        // Ignore already finished nodes.
      }
      source.disconnect();
    });
    playbackSourcesRef.current.clear();

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      await audioContextRef.current.close();
    }
    audioContextRef.current = null;
    playbackCursorRef.current = 0;
  };

  const closeSocket = (intentional = false) => {
    captureActiveRef.current = false;
    isCleaningUpRef.current = intentional;
    autoStartRecordingRef.current = false;
    suppressAssistantStreamRef.current = false;

    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  const ensureCapturePipeline = useCallback(async () => {
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
  }, [ensureAudioContext]);

  const queuePlaybackChunk = useCallback(async (audioBase64) => {
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
    playbackSourcesRef.current.add(source);
    source.onended = () => {
      playbackSourcesRef.current.delete(source);
      source.disconnect();
    };
  }, [ensureAudioContext]);

  const stopAssistantPlayback = useCallback(() => {
    playbackSourcesRef.current.forEach((source) => {
      try {
        source.onended = null;
        source.stop(0);
      } catch {
        // Ignore already finished nodes.
      }
      source.disconnect();
    });
    playbackSourcesRef.current.clear();

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      playbackCursorRef.current = audioContextRef.current.currentTime;
      return;
    }

    playbackCursorRef.current = 0;
  }, []);

  const startRecordingTurn = useCallback(async () => {
    try {
      await ensureCapturePipeline();
      await ensureAudioContext();
      stopAssistantPlayback();
      assistantDraftRef.current = "";
      suppressAssistantStreamRef.current = false;
      setAssistantDraft("");
      setPartialTranscript("");
      setSessionError("");
      setLessonHint(null);
      captureActiveRef.current = true;
      socketRef.current?.send(JSON.stringify({
        type: "start_recording",
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
      }));
      setRecordingState("recording");
    } catch (error) {
      captureActiveRef.current = false;
      autoStartRecordingRef.current = false;
      setSessionError(error?.message || "Microphone access failed.");
      setRecordingState("idle");
    }
  }, [ensureAudioContext, ensureCapturePipeline, stopAssistantPlayback]);

  const interruptAssistant = (startAfterInterrupt = false) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    suppressAssistantStreamRef.current = true;
    captureActiveRef.current = false;
    autoStartRecordingRef.current = startAfterInterrupt;
    stopAssistantPlayback();
    socketRef.current.send(JSON.stringify({ type: "interrupt_assistant" }));
    setRecordingState("interrupting");
  };

  const handleSocketMessage = useCallback(async (event) => {
    let payload;

    try {
      payload = JSON.parse(event.data);
    } catch {
      return;
    }

    switch (payload.type) {
      case "session_started":
        sessionStartAtRef.current = Date.now();
        suppressAssistantStreamRef.current = false;
        assistantDraftRef.current = "";
        setSessionId(payload.session_id);
        setConnectionState("ready");
        setRecordingState("idle");
        setSessionError("");
        setDurationSeconds(0);
        break;
      case "lesson_started":
        setLessonState(payload.lesson || null);
        if (payload.lesson?.current_question) {
          setMessages((current) => {
            return appendUniqueMessage(
              current,
              buildMessage("assistant", payload.lesson.current_question),
            );
          });
        }
        break;
      case "lesson_state":
        if (
          lessonStateRef.current?.current_objective?.objective_id &&
          payload.lesson?.current_objective?.objective_id &&
          lessonStateRef.current.current_objective.objective_id !== payload.lesson.current_objective.objective_id
        ) {
          setLessonHint(null);
        }
        setLessonState(payload.lesson || null);
        break;
      case "recording_started":
        setRecordingState("recording");
        setSessionError("");
        break;
      case "transcript_partial":
        setPartialTranscript(payload.text || "");
        break;
      case "transcript_final":
        captureActiveRef.current = false;
        if (payload.text) {
          setMessages((current) => appendUniqueMessage(current, buildMessage("user", payload.text)));
        }
        setLessonHint(null);
        setPartialTranscript("");
        setRecordingState("processing");
        break;
      case "llm_chunk":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        assistantDraftRef.current = `${assistantDraftRef.current}${payload.text || ""}`;
        setAssistantDraft((current) => `${current}${payload.text || ""}`);
        setRecordingState("assistant");
        break;
      case "llm_done":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        assistantDraftRef.current = "";
        setAssistantDraft("");
        if (payload.text) {
          setMessages((current) => appendUniqueMessage(current, buildMessage("assistant", payload.text)));
        }
        setRecordingState("assistant");
        break;
      case "audio_chunk":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        setRecordingState("assistant");
        await queuePlaybackChunk(payload.data);
        break;
      case "audio_done":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        setRecordingState("idle");
        break;
      case "conversation_end":
        setLessonState(payload.lesson || null);
        setRecordingState("idle");
        break;
      case "assistant_interrupted":
        stopAssistantPlayback();
        suppressAssistantStreamRef.current = false;
        assistantDraftRef.current = "";
        setAssistantDraft("");
        if (payload.text) {
          setMessages((current) => appendUniqueMessage(current, buildMessage("assistant", payload.text)));
        }
        if (autoStartRecordingRef.current) {
          autoStartRecordingRef.current = false;
          await startRecordingTurn();
          break;
        }
        setRecordingState("idle");
        break;
      case "error":
        stopAssistantPlayback();
        assistantDraftRef.current = "";
        suppressAssistantStreamRef.current = false;
        autoStartRecordingRef.current = false;
        setSessionError(payload.message || "Unexpected realtime error.");
        setRecordingState("idle");
        setConnectionState((current) => (current === "ready" ? current : "error"));
        break;
      default:
        break;
    }
  }, [queuePlaybackChunk, startRecordingTurn, stopAssistantPlayback]);

  const connectSocket = useCallback((resetConversation = true) => {
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
      setLessonState(null);
      setLessonHint(null);
      sessionStartAtRef.current = null;
      assistantDraftRef.current = "";
    }

    setConnectionState("connecting");
    setRecordingState("idle");
    setSessionError("");
    isCleaningUpRef.current = false;
    suppressAssistantStreamRef.current = false;
    stopAssistantPlayback();

    const socket = new WebSocket(createConversationWebSocketUrl(practiceApi.getApiBaseUrl()));
    socketRef.current = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({
        type: "session_start",
        token,
        scenario_id: scenarioId,
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
        metadata: {
          conversation_engine: "lesson_v1",
        },
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
  }, [handleSocketMessage, scenarioId, stopAssistantPlayback]);

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

  useEffect(() => () => {
    closeSocket(true);
    void teardownAudioPipeline();
  }, []);

  useEffect(() => {
    lessonStateRef.current = lessonState;
  }, [lessonState]);

  useEffect(() => {
    if (connectionState !== "ready" || !autoStartRecordingRef.current) {
      return;
    }

    autoStartRecordingRef.current = false;
    void startRecordingTurn();
  }, [connectionState, sessionId, startRecordingTurn]);

  useEffect(() => {
    if (reconnectRequest === 0) {
      return;
    }

    connectSocket(true);
  }, [connectSocket, reconnectRequest]);

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
      autoStartRecordingRef.current = true;
      if (connectionState !== "connecting") {
        setSessionError("");
        connectSocket(messages.length === 0 && !sessionId);
      }
      return;
    }

    if (recordingState === "assistant") {
      interruptAssistant(true);
      return;
    }

    if (recordingState === "interrupting") {
      return;
    }

    if (recordingState === "recording") {
      captureActiveRef.current = false;
      socketRef.current.send(JSON.stringify({ type: "stop_recording" }));
      setRecordingState("processing");
      return;
    }

    await startRecordingTurn();
  };

  const handleReconnect = () => {
    setReconnectRequest((current) => current + 1);
  };

  const handleEndSession = async () => {
    closeSocket(true);
    await teardownAudioPipeline();
    navigate("/topics");
  };

  const handleRequestHint = async () => {
    if (!sessionId || !lessonState?.lesson_id || isHintLoading) {
      return;
    }

    const latestUserMessage = [...messages].reverse().find((message) => message.role === "user");
    setIsHintLoading(true);
    setSessionError("");
    try {
      const hint = await practiceApi.getLessonHint({
        sessionId,
        lessonId: lessonState.lesson_id,
        objectiveId: lessonState.current_objective?.objective_id,
        userLastAnswer: latestUserMessage?.content || "",
      });
      setLessonHint(hint);
    } catch (error) {
      setSessionError(error?.response?.data?.detail || "Unable to generate a hint right now.");
    } finally {
      setIsHintLoading(false);
    }
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

  const lessonCompleted = lessonState?.should_end || lessonState?.status === "completed";
  const isMicDisabled =
    lessonCompleted ||
    connectionState === "connecting" ||
    recordingState === "processing" ||
    recordingState === "interrupting";
  const userTurnCount = messages.filter((message) => message.role === "user").length;
  const conversationGuidance = buildConversationGuidance({
    scenario,
    messages,
    durationSeconds,
    turnCount: userTurnCount,
  });
  const lessonCompletionTone = getLessonCompletionTone(lessonState);
  const progressPercent = lessonState?.progress?.percent ?? 0;

  return (
    <div className="min-h-[100dvh] bg-[radial-gradient(circle_at_top_left,_rgba(49,130,237,0.18),_transparent_30%),linear-gradient(135deg,_#eff6ff_0%,_#ffffff_48%,_#ecfeff_100%)] p-4 font-sans antialiased md:p-6">
      <div className="mx-auto flex h-[calc(100dvh-2rem)] max-w-[1440px] flex-col gap-4 md:h-[calc(100dvh-3rem)] md:gap-6">
        <SessionHeader
          scenarioTitle={scenario.title}
          connectionState={connectionState}
          onBack={() => navigate("/topics")}
          onExit={handleEndSession}
        />

        <section className="rounded-[28px] border border-white/45 bg-white/75 px-5 py-4 shadow-[0_18px_40px_-28px_rgba(15,23,42,0.4)] backdrop-blur-xl">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-primary">
                  Guided Lesson Progress
                </p>
                <span className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-600">
                  {lessonState?.progress
                    ? `${lessonState.progress.completed}/${lessonState.progress.total} complete`
                    : "Waiting"}
                </span>
              </div>
              <div className="mt-3 h-3 overflow-hidden rounded-full bg-zinc-100">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3 xl:min-w-[520px]">
              <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Current Objective</p>
                <p className="mt-1 text-sm font-semibold text-zinc-900">
                  {lessonState?.current_objective?.goal || "Loading objective"}
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Need To Mention</p>
                <p className="mt-1 text-sm font-semibold text-zinc-900">
                  {lessonState?.current_objective?.missing_points?.length || 0} points
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-200 bg-white px-4 py-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Follow-ups Left</p>
                <p className="mt-1 text-sm font-semibold text-zinc-900">
                  {lessonState?.current_objective?.remaining_follow_ups ?? 0}
                </p>
              </div>
            </div>
          </div>
        </section>

        <main className="grid min-h-0 flex-1 grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="relative flex min-h-0 flex-col gap-6 lg:col-span-8">
            <CurrentQuestionCard
              lessonState={lessonState}
              guidance={conversationGuidance}
              connectionState={connectionState}
              recordingState={recordingState}
            />
            <ChatWindow
              messages={messages}
              partialTranscript={partialTranscript}
              assistantDraft={assistantDraft}
            />
            <TypewriterInput
              partialTranscript={partialTranscript}
              recordingState={recordingState}
              connectionState={connectionState}
              onToggleRecording={handleToggleRecording}
              onReconnect={handleReconnect}
              disabled={isMicDisabled}
              error={sessionError}
              suggestions={lessonState?.suggested_responses?.length ? lessonState.suggested_responses : conversationGuidance.suggestedResponses}
              completion={lessonState ? {
                title: lessonCompleted ? "Conversation Complete" : "Current Goal",
                detail: lessonCompleted
                  ? lessonState.completion_message || "The lesson goals are complete. You can end the session now."
                  : lessonState.current_objective?.goal || conversationGuidance.completion?.detail,
                status: lessonCompleted ? "ready" : lessonCompletionTone,
              } : conversationGuidance.completion}
              lessonState={lessonState}
              hint={lessonHint}
              isHintLoading={isHintLoading}
              onRequestHint={handleRequestHint}
            />
          </div>

          <MetricsSidebar
            scenario={scenario}
            durationSeconds={durationSeconds}
            sessionId={sessionId}
            turnCount={userTurnCount}
            connectionState={connectionState}
            recordingState={recordingState}
            onReconnect={handleReconnect}
            onEndSession={handleEndSession}
            lessonState={lessonState}
          />
        </main>
      </div>
    </div>
  );
};

export default PracticeSession;
