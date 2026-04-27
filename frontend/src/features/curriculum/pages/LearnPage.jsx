import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LockKey, PlayCircle, CheckCircle } from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const LearnPage = () => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setIsLoading(true);
      setError("");
      try {
        const response = await curriculumApi.getCurriculum();
        if (mounted) setData(response);
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || "Không thể tải lộ trình học.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  if (isLoading) {
    return <div className="p-8 text-sm font-semibold text-muted-foreground">Đang tải lộ trình...</div>;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-6 pb-12 pt-4">
      <header>
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Learning Path</p>
        <h1 className="mt-3 text-4xl font-black tracking-tight text-zinc-950">Học theo tiến độ</h1>
        <p className="mt-2 text-sm font-semibold text-muted-foreground">
          Hoàn thành từng bài theo thứ tự để mở khóa bài tiếp theo.
        </p>
      </header>

      {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{error}</div>}

      <div className="space-y-8">
        {(data?.levels || []).map((level) => (
          <section key={level.id} className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h2 className="text-2xl font-black text-zinc-950">{level.title}</h2>
                {level.description && <p className="mt-1 text-sm text-muted-foreground">{level.description}</p>}
              </div>
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-black uppercase text-zinc-600">
                {level.code}
              </span>
            </div>
            <div className="grid gap-3">
              {level.lessons.map((lesson) => {
                const completed = lesson.progress_status === "completed";
                const Icon = lesson.is_locked ? LockKey : completed ? CheckCircle : PlayCircle;
                return (
                  <Link
                    key={lesson.id}
                    to={lesson.is_locked ? "#" : `/learn/lessons/${lesson.id}`}
                    className={`flex items-center gap-4 rounded-xl border p-4 transition ${
                      lesson.is_locked
                        ? "cursor-not-allowed border-zinc-200 bg-zinc-50 text-zinc-400"
                        : "border-border bg-card hover:border-primary/40 hover:shadow-sm"
                    }`}
                  >
                    <Icon size={26} weight="fill" className={completed ? "text-emerald-600" : "text-primary"} />
                    <div className="min-w-0 flex-1">
                      <p className="font-black text-zinc-950">{lesson.title}</p>
                      <p className="mt-1 text-xs font-semibold text-muted-foreground">
                        {lesson.estimated_minutes || 10} phút · {lesson.progress_status.replace("_", " ")}
                      </p>
                    </div>
                    {lesson.best_score != null && (
                      <span className="text-sm font-black text-emerald-600">{Math.round(lesson.best_score)}</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};

export default LearnPage;
