import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, WarningCircle } from "@phosphor-icons/react";
import { useNavigate, useParams } from "react-router-dom";
import ChatWindow from "@/features/practice/components/ChatWindow";
import ScenarioSidebar from "@/features/practice/components/ScenarioSidebar";
import TypewriterInput from "@/features/practice/components/TypewriterInput";
import { SessionHeader } from "@/shared/components/navigation";
import {
  arrayBufferToBase64,
  base64ToArrayBuffer,
  createConversationWebSocketUrl,
  pcm16ToFloat32,
} from "@/features/practice/services/realtimeAudio";
import { practiceApi } from "@/features/practice/api/practiceApi";
import { buildConversationGuidance } from "@/features/practice/utils/conversationGuidance";
import {
  appendUniqueMessage,
} from "@/features/practice/utils/lessonState";

const DEFAULT_LANGUAGE = "en";
const DEFAULT_VOICE = "Cherry";
const STOP_CAPTURE_FLUSH_MS = 250;
const RECONNECT_DELAYS_MS = [500, 1000, 2000];
const NO_INPUT_NOTICE = "Mải mê nghe giọng bạn làm mình đãng trí. Bạn có thể nói lại một lần nữa được không?";
const TIME_LIMIT_NOTICE = "Đã hết thời gian luyện tập. Mình sẽ chuyển bạn sang phần đánh giá.";

const wait = (milliseconds) => new Promise((resolve) => {
  window.setTimeout(resolve, milliseconds);
});

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
  const intentionalCloseSocketRef = useRef(null);
  const connectSocketRef = useRef(null);
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
  const hasAutoConnectedRef = useRef(false);
  const isStoppingRecordingRef = useRef(false);
  const connectionStateRef = useRef(connectionState);
  const recordingStateRef = useRef(recordingState);
  const sessionIdRef = useRef(sessionId);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef(null);
  const isAutoReconnectingRef = useRef(false);
  const isNavigatingToResultRef = useRef(false);

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
      audioContextRef.current = new BrowserAudioContext({ sampleRate: 16000 });
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

  const closeSocket = useCallback((intentional = false) => {
    captureActiveRef.current = false;
    isCleaningUpRef.current = intentional;
    autoStartRecordingRef.current = false;
    suppressAssistantStreamRef.current = false;
    isStoppingRecordingRef.current = false;
    if (intentional && reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
      isAutoReconnectingRef.current = false;
      reconnectAttemptsRef.current = 0;
    }

    if (socketRef.current) {
      if (intentional) {
        intentionalCloseSocketRef.current = socketRef.current;
      }
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const navigateToResult = useCallback((nextSessionId = sessionIdRef.current) => {
    if (!nextSessionId || isNavigatingToResultRef.current) {
      return;
    }
    isNavigatingToResultRef.current = true;
    closeSocket(true);
    navigate(`/sessions/${nextSessionId}/result`);
  }, [closeSocket, navigate]);

  const finalizeAfterConnectionFailure = useCallback(async () => {
    const activeSessionId = sessionIdRef.current;
    if (!activeSessionId || isNavigatingToResultRef.current) {
      return;
    }

    isNavigatingToResultRef.current = true;
    connectionStateRef.current = "error";
    recordingStateRef.current = "idle";
    setConnectionState("error");
    setRecordingState("idle");
    setSessionError("Connection failed after 3 reconnect attempts. Moving to your session result.");

    try {
      await practiceApi.endSession(activeSessionId, {
        status: "completed",
        metadata: { end_reason: "connection_failed" },
      });
    } catch {
      // Navigation still proceeds; the backend may already have finalized the session.
    } finally {
      closeSocket(true);
      navigate(`/sessions/${activeSessionId}/result`);
    }
  }, [closeSocket, navigate]);

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

    await audioContext.audioWorklet.addModule("/audio-capture-worklet.js");
    const processor = new AudioWorkletNode(audioContext, "audio-capture-processor");

    const silentGain = audioContext.createGain();
    silentGain.gain.value = 0;

    processor.port.onmessage = (event) => {
      if (!captureActiveRef.current || socketRef.current?.readyState !== WebSocket.OPEN) {
        return;
      }

      const pcmBuffer = event.data;
      socketRef.current.send(JSON.stringify({
        type: "audio_chunk",
        data: arrayBufferToBase64(pcmBuffer),
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

  const scheduleAutoReconnect = useCallback(() => {
    if (!sessionIdRef.current || reconnectAttemptsRef.current >= RECONNECT_DELAYS_MS.length) {
      void finalizeAfterConnectionFailure();
      return;
    }

    const attemptIndex = reconnectAttemptsRef.current;
    const delay = RECONNECT_DELAYS_MS[attemptIndex];
    reconnectAttemptsRef.current += 1;
    isAutoReconnectingRef.current = true;
    connectionStateRef.current = "reconnecting";
    recordingStateRef.current = "idle";
    setConnectionState("reconnecting");
    setRecordingState("idle");
    setSessionError(`Connection interrupted. Reconnecting (${attemptIndex + 1}/3)...`);

    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
    }

    reconnectTimerRef.current = window.setTimeout(() => {
      reconnectTimerRef.current = null;
      connectSocketRef.current?.({ resetConversation: false, resume: true });
    }, delay);
  }, [finalizeAfterConnectionFailure]);

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
      isStoppingRecordingRef.current = false;
      captureActiveRef.current = true;
      socketRef.current?.send(JSON.stringify({
        type: "start_recording",
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
      }));
      recordingStateRef.current = "recording";
      setRecordingState("recording");
    } catch (error) {
      captureActiveRef.current = false;
      autoStartRecordingRef.current = false;
      setSessionError(error?.message || "Microphone access failed.");
      recordingStateRef.current = "idle";
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
    recordingStateRef.current = "interrupting";
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
        if (!sessionStartAtRef.current || sessionIdRef.current !== payload.session_id) {
          sessionStartAtRef.current = Date.now();
          setDurationSeconds(0);
        }
        reconnectAttemptsRef.current = 0;
        isAutoReconnectingRef.current = false;
        if (reconnectTimerRef.current) {
          window.clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
        suppressAssistantStreamRef.current = false;
        assistantDraftRef.current = "";
        sessionIdRef.current = payload.session_id;
        setSessionId(payload.session_id);
        connectionStateRef.current = "ready";
        recordingStateRef.current = "idle";
        setConnectionState("ready");
        setRecordingState("idle");
        setSessionError("");
        break;
      case "lesson_started":
        setLessonState(payload.lesson || null);
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
        recordingStateRef.current = "recording";
        setRecordingState("recording");
        setSessionError("");
        break;
      case "transcript_partial":
        if (payload.text) {
          setPartialTranscript(payload.text);
        }
        break;
      case "transcript_final":
        captureActiveRef.current = false;
        isStoppingRecordingRef.current = false;
        if (payload.text) {
          setMessages((current) => appendUniqueMessage(current, buildMessage("user", payload.text)));
        }
        setLessonHint(null);
        setPartialTranscript("");
        recordingStateRef.current = "processing";
        setRecordingState("processing");
        break;
      case "asr_no_input":
        captureActiveRef.current = false;
        isStoppingRecordingRef.current = false;
        setPartialTranscript("");
        recordingStateRef.current = "idle";
        setRecordingState("idle");
        setMessages((current) => appendUniqueMessage(
          current,
          buildMessage("notice", payload.message || NO_INPUT_NOTICE),
        ));
        break;
      case "llm_chunk":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        assistantDraftRef.current = `${assistantDraftRef.current}${payload.text || ""}`;
        setAssistantDraft((current) => `${current}${payload.text || ""}`);
        recordingStateRef.current = "assistant";
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
        recordingStateRef.current = "assistant";
        setRecordingState("assistant");
        break;
      case "audio_chunk":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        recordingStateRef.current = "assistant";
        setRecordingState("assistant");
        await queuePlaybackChunk(payload.data);
        break;
      case "audio_done":
        if (suppressAssistantStreamRef.current) {
          break;
        }
        recordingStateRef.current = "idle";
        setRecordingState("idle");
        break;
      case "conversation_end":
        setLessonState(payload.lesson || null);
        recordingStateRef.current = "idle";
        setRecordingState("idle");
        setPartialTranscript("");
        if (payload.message) {
          setMessages((current) => appendUniqueMessage(
            current,
            buildMessage("notice", payload.message),
          ));
        }
        if (payload.reason === "time_limit_reached" && payload.session_id) {
          navigateToResult(payload.session_id);
        }
        break;
      case "session_finalized":
        if (payload.reason === "time_limit_reached") {
          setMessages((current) => appendUniqueMessage(
            current,
            buildMessage("notice", TIME_LIMIT_NOTICE),
          ));
        }
        if (!isNavigatingToResultRef.current) {
          isNavigatingToResultRef.current = true;
          closeSocket(true);
          navigate(payload.result_url || `/sessions/${payload.session_id}/result`);
        }
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
        recordingStateRef.current = "idle";
        setRecordingState("idle");
        break;
      case "error":
        stopAssistantPlayback();
        isStoppingRecordingRef.current = false;
        assistantDraftRef.current = "";
        suppressAssistantStreamRef.current = false;
        autoStartRecordingRef.current = false;
        setSessionError(payload.message || "Unexpected realtime error.");
        recordingStateRef.current = "idle";
        setRecordingState("idle");
        setConnectionState((current) => {
          const next = current === "ready" ? current : "error";
          connectionStateRef.current = next;
          return next;
        });
        break;
      default:
        break;
    }
  }, [closeSocket, navigate, navigateToResult, queuePlaybackChunk, startRecordingTurn, stopAssistantPlayback]);

  const connectSocket = useCallback((options = true) => {
    const resetConversation = typeof options === "boolean" ? options : options.resetConversation !== false;
    const shouldResume = typeof options === "object" && options.resume && sessionIdRef.current;
    const token = window.localStorage.getItem("access_token");
    if (!token) {
      setSessionError("Missing access token. Please sign in again.");
      setConnectionState("error");
      return;
    }

    const reconnectAttemptsBeforeClose = reconnectAttemptsRef.current;
    closeSocket(true);
    if (shouldResume) {
      reconnectAttemptsRef.current = reconnectAttemptsBeforeClose;
      isAutoReconnectingRef.current = true;
    }

    if (resetConversation) {
      setMessages([]);
      setAssistantDraft("");
      setPartialTranscript("");
      setSessionId(null);
      sessionIdRef.current = null;
      setDurationSeconds(0);
      setLessonState(null);
      setLessonHint(null);
      sessionStartAtRef.current = null;
      assistantDraftRef.current = "";
    }

    connectionStateRef.current = shouldResume ? "reconnecting" : "connecting";
    recordingStateRef.current = "idle";
    setConnectionState(shouldResume ? "reconnecting" : "connecting");
    setRecordingState("idle");
    setSessionError("");
    isCleaningUpRef.current = false;
    suppressAssistantStreamRef.current = false;
    stopAssistantPlayback();

    const socket = new WebSocket(createConversationWebSocketUrl(practiceApi.getApiBaseUrl()));
    socketRef.current = socket;

    socket.onopen = () => {
      const startMessage = {
        type: "session_start",
        token,
        scenario_id: scenarioId,
        language: DEFAULT_LANGUAGE,
        voice: DEFAULT_VOICE,
        metadata: {
          conversation_engine: "lesson_v1",
          resume_enabled: true,
        },
      };
      if (shouldResume) {
        startMessage.session_id = sessionIdRef.current;
      }
      socket.send(JSON.stringify(startMessage));
    };

    socket.onmessage = (event) => {
      void handleSocketMessage(event);
    };

    socket.onerror = () => {
      if (["recording", "processing"].includes(recordingStateRef.current) && sessionIdRef.current) {
        return;
      }
      setConnectionState("error");
      connectionStateRef.current = "error";
      setSessionError("Unable to reach the realtime conversation service.");
    };

    socket.onclose = () => {
      if (intentionalCloseSocketRef.current === socket) {
        intentionalCloseSocketRef.current = null;
        return;
      }

      socketRef.current = null;
      captureActiveRef.current = false;
      const wasActiveTurn = ["recording", "processing"].includes(recordingStateRef.current);

      if (isCleaningUpRef.current) {
        isCleaningUpRef.current = false;
        return;
      }

      if ((wasActiveTurn || isAutoReconnectingRef.current) && sessionIdRef.current) {
        void teardownAudioPipeline();
        scheduleAutoReconnect();
        return;
      }

      setConnectionState((current) => {
        const next = current === "error" ? current : "closed";
        connectionStateRef.current = next;
        return next;
      });
      recordingStateRef.current = "idle";
      setRecordingState("idle");
    };
  }, [closeSocket, handleSocketMessage, scenarioId, scheduleAutoReconnect, stopAssistantPlayback]);

  useEffect(() => {
    connectSocketRef.current = connectSocket;
  }, [connectSocket]);

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
  }, [closeSocket]);

  useEffect(() => {
    lessonStateRef.current = lessonState;
  }, [lessonState]);

  useEffect(() => {
    connectionStateRef.current = connectionState;
  }, [connectionState]);

  useEffect(() => {
    recordingStateRef.current = recordingState;
  }, [recordingState]);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    if (!scenario || scenarioError || hasAutoConnectedRef.current || connectionState !== "closed") {
      return;
    }

    hasAutoConnectedRef.current = true;
    connectSocket(true);
  }, [connectSocket, connectionState, scenario, scenarioError]);

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

    connectSocket({ resetConversation: !sessionIdRef.current, resume: Boolean(sessionIdRef.current) });
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
      if (connectionState !== "connecting" && connectionState !== "reconnecting") {
        setSessionError("");
        connectSocket({ resetConversation: messages.length === 0 && !sessionId, resume: Boolean(sessionId) });
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
      if (isStoppingRecordingRef.current) {
        return;
      }
      isStoppingRecordingRef.current = true;
      recordingStateRef.current = "processing";
      setRecordingState("processing");
      await wait(STOP_CAPTURE_FLUSH_MS);
      captureActiveRef.current = false;
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: "stop_recording" }));
      } else {
        isStoppingRecordingRef.current = false;
      }
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

    setIsHintLoading(true);
    setSessionError("");
    try {
      const hint = await practiceApi.getLessonHint({
        sessionId,
        lessonId: lessonState.lesson_id,
        objectiveId: lessonState.current_objective?.objective_id,
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
    connectionState === "reconnecting" ||
    recordingState === "processing" ||
    recordingState === "interrupting";
  const userTurnCount = messages.filter((message) => message.role === "user").length;
  const conversationGuidance = buildConversationGuidance({
    scenario,
    messages,
    durationSeconds,
    turnCount: userTurnCount,
  });

  return (
    <div className="min-h-[100dvh] bg-[linear-gradient(135deg,_#f8fafc_0%,_#ffffff_46%,_#f0fdf4_100%)] p-4 font-sans antialiased md:p-6">
      <div className="mx-auto flex h-[calc(100dvh-2rem)] max-w-[1440px] flex-col gap-4 md:h-[calc(100dvh-3rem)] md:gap-6">
        <SessionHeader
          onBack={handleEndSession}
          onReconnect={handleReconnect}
          connectionState={connectionState}
        />

        <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[340px_minmax(0,1fr)] xl:grid-cols-[380px_minmax(0,1fr)] w-full">
          <div className="hidden min-h-0 lg:flex">
            <ScenarioSidebar scenario={scenario} lessonState={lessonState} guidance={conversationGuidance} />
          </div>
          <div className="relative flex min-h-0 flex-1 flex-col gap-3">
            <ChatWindow
              scenario={scenario}
              lessonState={lessonState}
              guidance={conversationGuidance}
              messages={messages}
              assistantDraft={assistantDraft}
              isListening={recordingState === "recording"}
            />
            <TypewriterInput
              partialTranscript={partialTranscript}
              recordingState={recordingState}
              connectionState={connectionState}
              onToggleRecording={handleToggleRecording}
              onReconnect={handleReconnect}
              disabled={isMicDisabled}
              error={sessionError}
              lessonState={lessonState}
              hint={lessonHint}
              isHintLoading={isHintLoading}
              onRequestHint={handleRequestHint}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default PracticeSession;
