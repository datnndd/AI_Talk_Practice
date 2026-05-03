import { useState } from "react";
import { Link } from "react-router-dom";
import { ChatCircleText } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const ConversationExerciseLauncher = ({ exercise, onAttempt }) => {
  const [session, setSession] = useState(null);
  const [sessionId, setSessionId] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const [error, setError] = useState("");
  const scenarioId = exercise.content?.scenario_id;

  const start = async () => {
    setIsStarting(true);
    setError("");
    try {
      const response = await curriculumApi.startConversationLesson(exercise.id);
      setSession(response);
      setSessionId(String(response.session_id));
    } catch (err) {
      setError(err?.response?.data?.detail || "Không thể bắt đầu hội thoại.");
    } finally {
      setIsStarting(false);
    }
  };

  const scoreConversation = async () => {
    setIsScoring(true);
    setError("");
    try {
      const response = await curriculumApi.attemptLesson(exercise.id, {
        session_id: Number(sessionId),
        answer: { session_id: Number(sessionId) },
      });
      onAttempt?.(response);
    } catch (err) {
      setError(err?.response?.data?.detail || "Chưa thể chấm hội thoại. Hãy kết thúc session trước.");
    } finally {
      setIsScoring(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-zinc-50 p-5">
        <p className="text-xs font-black uppercase tracking-wide text-muted-foreground">Interactive conversation</p>
        <p className="mt-2 text-sm leading-6 text-zinc-700">
          Bài này dùng luồng hội thoại AI hiện tại. Sau khi kết thúc hội thoại, quay lại bài học và nộp điểm bằng session.
        </p>
      </div>

      {!session ? (
        <button
          type="button"
          onClick={start}
          disabled={isStarting || !scenarioId}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:opacity-60"
        >
          <ChatCircleText size={18} weight="fill" />
          {isStarting ? "Đang tạo session..." : "Bắt đầu hội thoại"}
        </button>
      ) : (
        <Link
          to={`/practice/${session.scenario_id}/preview?sessionId=${session.session_id}`}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white"
        >
          <ChatCircleText size={18} weight="fill" />
          Mở phòng hội thoại
        </Link>
      )}

      {session && (
        <div className="space-y-3 rounded-xl border border-border bg-card p-4">
          <p className="text-sm font-semibold text-muted-foreground">
            Session #{session.session_id}. Sau khi hoàn tất, bấm chấm điểm để hoàn thành lesson.
          </p>
          <div className="flex flex-wrap gap-2">
            <input
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              className="rounded-lg border border-border px-3 py-2 text-sm font-semibold"
              placeholder="Session ID"
            />
            <button
              type="button"
              onClick={scoreConversation}
              disabled={isScoring || !sessionId}
              className="rounded-lg bg-zinc-950 px-4 py-2 text-sm font-black text-white disabled:opacity-50"
            >
              {isScoring ? "Đang chấm..." : "Chấm hội thoại"}
            </button>
          </div>
        </div>
      )}
      {error && <p className="text-sm font-semibold text-rose-600">{error}</p>}
    </div>
  );
};

export default ConversationExerciseLauncher;

