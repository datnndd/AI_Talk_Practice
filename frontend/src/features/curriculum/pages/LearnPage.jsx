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
      const cachedCurriculum = curriculumApi.getCachedCurriculum();
      if (cachedCurriculum) {
        setData(cachedCurriculum);
      }
      setIsLoading(!cachedCurriculum);
      setError("");
      try {
        const response = await curriculumApi.getCurriculum();
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || "Không thể tải lộ trình học.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    if (curriculumApi.getCachedCurriculum()) {
      void curriculumApi.getCurriculum({ force: true }).then((response) => {
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      }).catch(() => null);
    }
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
        {(data?.sections || []).map((section) => (
          <section key={section.id} className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h2 className="text-2xl font-black text-zinc-950">{section.title}</h2>
                {section.description && <p className="mt-1 text-sm text-muted-foreground">{section.description}</p>}
              </div>
              <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-black uppercase text-zinc-600">
                {section.cefr_level || section.code}
              </span>
            </div>
            <div className="grid gap-3">
              {section.units.map((unit) => {
                const completed = unit.progress_status === "completed";
                const Icon = unit.is_locked ? LockKey : completed ? CheckCircle : PlayCircle;
                return (
                  <Link
                    key={unit.id}
                    to={unit.is_locked ? "#" : `/learn/units/${unit.id}`}
                    className={`flex items-center gap-4 rounded-xl border p-4 transition ${
                      unit.is_locked
                        ? "cursor-not-allowed border-zinc-200 bg-zinc-50 text-zinc-400"
                        : "border-border bg-card hover:border-primary/40 hover:shadow-sm"
                    }`}
                  >
                    <Icon size={26} weight="fill" className={completed ? "text-emerald-600" : "text-primary"} />
                    <div className="min-w-0 flex-1">
                      <p className="font-black text-zinc-950">{unit.title}</p>
                      <p className="mt-1 text-xs font-semibold text-muted-foreground">
                        {unit.progress_status.replace("_", " ")}
                      </p>
                    </div>
                    {unit.best_score != null && (
                      <span className="text-sm font-black text-emerald-600">{Math.round(unit.best_score)}</span>
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
