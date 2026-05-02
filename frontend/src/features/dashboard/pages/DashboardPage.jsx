import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import PlaylistSection from "@/features/dashboard/components/PlaylistSection";
import { useAuth } from "@/features/auth/context/AuthContext";
import { canAccessSubscriptionFeatures } from "@/features/auth/utils/subscription";
import { practiceApi } from "@/features/practice/api/practiceApi";

const Dashboard = () => {
  const { user, gamification } = useAuth();
  const [scenarios, setScenarios] = useState([]);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);
  const [scenarioError, setScenarioError] = useState("");
  const surpriseScenario = useMemo(() => {
    if (scenarios.length === 0) {
      return null;
    }

    return scenarios[Math.floor(Math.random() * scenarios.length)];
  }, [scenarios]);
  const hasProAccess = canAccessSubscriptionFeatures(user);
  const streak = gamification?.check_in?.current_streak || 0;
  const level = gamification?.xp?.level || 1;

  useEffect(() => {
    let isMounted = true;

    const loadScenarios = async () => {
      const cachedScenarios = practiceApi.getCachedScenarios?.();
      if (cachedScenarios) {
        setScenarios(Array.isArray(cachedScenarios) ? cachedScenarios : []);
      }
      setIsLoadingScenarios(!cachedScenarios);
      setScenarioError("");

      try {
        const data = await practiceApi.listScenarios();
        if (isMounted) {
          setScenarios(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (isMounted) {
          setScenarioError(error?.response?.data?.detail || "Không thể tải danh sách kịch bản.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingScenarios(false);
        }
      }
    };

    const hadCachedScenarios = Boolean(practiceApi.getCachedScenarios?.());
    void loadScenarios();
    if (hadCachedScenarios) {
      void practiceApi.listScenarios({ force: true }).then((data) => {
        if (isMounted) {
          setScenarios(Array.isArray(data) ? data : []);
        }
      }).catch(() => null);
    }

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-10 px-8 pb-12 pt-4">
      <section className="space-y-4">
        <h2 className="text-xl font-extrabold uppercase tracking-wide text-foreground/80">
          Role-Play Labs <span className="ml-1">🎭</span>
        </h2>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          <div className={`group relative col-span-1 overflow-hidden rounded-2xl p-7 text-white shadow-md transition hover:shadow-lg md:col-span-2 ${
            hasProAccess ? "bg-gradient-to-br from-purple-700 via-[#1a1f4d] to-amber-500" : "bg-[#1a1f4d]"
          }`}>
            <div
              className="pointer-events-none absolute inset-0 opacity-20"
              style={{
                backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)",
                backgroundSize: "16px 16px",
              }}
            />
            <div className="pointer-events-none absolute inset-y-0 right-0 w-2/3 bg-gradient-to-l from-[#2a3175]/60 to-transparent" />
            <div className="relative z-10 flex h-full items-center justify-between gap-4">
              <div className="space-y-4">
                <p className="text-[11px] font-black uppercase tracking-[0.22em] text-amber-200">
                  {hasProAccess ? "Pro Practice Hub" : "Free practice mode"}
                </p>
                <h3 className="text-3xl font-extrabold leading-tight">
                  {hasProAccess ? "AI Tutor unlocked" : "Mở khóa luyện nói AI không giới hạn"}
                </h3>
                <p className="text-sm font-semibold text-white/70">
                  {hasProAccess ? `Level ${level} • Streak ${streak} ngày • Premium scenarios ready` : "Nâng cấp Pro để mở kịch bản VIP, luyện nói live và phản hồi nâng cao."}
                </p>
                <Link
                  to={hasProAccess ? (surpriseScenario ? `/practice/${surpriseScenario.id}` : "/learn") : "/subscription"}
                  className="inline-flex rounded-full bg-brand-purple px-6 py-2.5 text-sm font-bold text-white shadow-md transition hover:bg-brand-purple/90 active:scale-95"
                >
                  {hasProAccess ? "Quick start" : "Nâng cấp Pro"}
                </Link>
              </div>
              <div className="flex h-28 w-28 shrink-0 items-center justify-center text-7xl transition-transform select-none group-hover:scale-110">
                🤖
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 md:col-span-1">
            <Link
              to={surpriseScenario ? `/practice/${surpriseScenario.id}` : "#playlists"}
              className="group flex flex-1 items-center gap-4 rounded-2xl border border-border bg-card p-5 text-left shadow-sm transition hover:border-brand-purple/40 hover:shadow-md active:scale-98"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-purple-soft text-2xl">🎁</div>
              <div>
                <p className="text-sm font-extrabold text-foreground">Surprise me</p>
                <p className="text-xs font-semibold text-muted-foreground">Kịch bản ngẫu nhiên</p>
              </div>
            </Link>
            <a
              href="#playlists"
              className="group flex flex-1 items-center gap-4 rounded-2xl border border-border bg-card p-5 text-left shadow-sm transition hover:border-brand-purple/40 hover:shadow-md active:scale-98"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-orange-soft text-2xl">✨</div>
              <div>
                <p className="text-sm font-extrabold text-foreground">Browse scenarios</p>
                <p className="text-xs font-semibold text-muted-foreground">Xem toàn bộ thư viện</p>
              </div>
            </a>
          </div>
        </div>
      </section>

      <div id="playlists">
        <PlaylistSection scenarios={scenarios} isLoading={isLoadingScenarios} error={scenarioError} hasProAccess={hasProAccess} />
      </div>
    </div>
  );
};

export default Dashboard;
